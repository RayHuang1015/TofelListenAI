"""
Daily Edition Composer Service
Creates 5-hour international news listening transcripts from ingested content
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import re

from app import app, db
from models import (
    ContentSource, ProviderSource, DailyEdition, EditionSegment, 
    IngestionJob
)
from services.historical_news_generator import HistoricalNewsGenerator
from services.real_content_providers import BBCWorldServiceProvider, ReutersProvider
from services.content_integration import ContentIntegrationService


@dataclass
class ContentRanking:
    """Content item with ranking score"""
    content: ContentSource
    score: float
    category_priority: int
    region_priority: int
    duration_sec: int


class DailyEditionComposer:
    """Composes 5-hour daily international news editions"""
    
    TARGET_DURATION = 18000  # 5 hours in seconds (EXACTLY)
    MIN_DURATION = 18000     # Must be exactly 5 hours
    MAX_DURATION = 18000     # Must be exactly 5 hours
    
    # Category priorities (higher = more important)
    CATEGORY_PRIORITIES = {
        'politics': 10,
        'business': 9,
        'general': 8,
        'technology': 7,
        'health': 6,
        'environment': 5,
        'sports': 4
    }
    
    # Region priorities for global coverage
    REGION_PRIORITIES = {
        'global': 10,
        'americas': 9,
        'europe': 8,
        'asia': 7,
        'middle_east': 6,
        'africa': 5
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compose_daily_edition(self, target_date: date, edition_number: int = 1) -> Dict[str, Any]:
        """
        Compose a 5-hour daily edition for the given date
        
        Args:
            target_date: Date to compose edition for
            edition_number: Edition number (default 1)
            
        Returns:
            Dict with status, edition_id, duration, segments, etc.
        """
        with app.app_context():
            try:
                self.logger.info(f"Starting composition for {target_date}, edition {edition_number}")
                
                # Check if edition already exists
                existing = DailyEdition.query.filter_by(
                    date=target_date, 
                    edition_number=edition_number
                ).first()
                
                if existing and existing.status == 'ready':
                    self.logger.info(f"Edition already exists and is ready: {existing.id}")
                    return {
                        'status': 'exists',
                        'edition_id': existing.id,
                        'message': f'Edition for {target_date} already ready'
                    }
                
                # Get available content for the date
                available_content = self._get_available_content(target_date)
                
                if not available_content:
                    self.logger.warning(f"No content available for {target_date}")
                    return {
                        'status': 'no_content',
                        'message': f'No international news content found for {target_date}'
                    }
                
                # Rank and select content for 3-hour composition
                selected_content = self._select_content_for_edition(available_content)
                
                if not selected_content:
                    return {
                        'status': 'insufficient_content',
                        'message': f'Insufficient quality content for {target_date}'
                    }
                
                # Create or update daily edition
                edition = self._create_or_update_edition(
                    target_date, edition_number, selected_content
                )
                
                # Create edition segments
                segments_created = self._create_edition_segments(edition, selected_content)
                
                # Ensure EXACT 18000 second duration before finalization
                selected_content = self._adjust_to_exact_duration(selected_content, self.TARGET_DURATION)
                
                # Finalize edition
                self._finalize_edition(edition, selected_content)
                
                total_duration = sum(item.duration_sec for item in selected_content)
                
                self.logger.info(
                    f"Composition complete: Edition {edition.id}, "
                    f"{len(selected_content)} segments, {total_duration}s"
                )
                
                return {
                    'status': 'success',
                    'edition_id': edition.id,
                    'total_duration': total_duration,
                    'segments_count': len(selected_content),
                    'target_duration': self.TARGET_DURATION,
                    'coverage_summary': self._generate_coverage_summary(selected_content)
                }
                
            except Exception as e:
                self.logger.error(f"Composition failed for {target_date}: {e}")
                return {
                    'status': 'failed',
                    'error': str(e)
                }
    
    def _get_available_content(self, target_date: date) -> List[ContentSource]:
        """Get international news content available for the date with fallback generation"""
        
        # Look for existing content within 24 hours of target date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        content = ContentSource.query.filter(
            ContentSource.published_date >= start_datetime,
            ContentSource.published_date < end_datetime,
            ContentSource.duration > 30,  # At least 30 seconds
            ContentSource.transcript_text.isnot(None),  # Must have transcript
            ContentSource.type.in_(['news_article', 'news', 'audio', 'video'])  # News content types
        ).all()
        
        self.logger.info(f"Found {len(content)} existing content items for {target_date}")
        
        # Check if we have enough content to reach minimum duration after deduplication
        total_available_duration = sum(item.duration for item in content if item.duration)
        
        if total_available_duration < self.MIN_DURATION:
            self.logger.info(
                f"Insufficient content ({total_available_duration}s < {self.MIN_DURATION}s). "
                f"Fetching real news sources first, then generating additional content if needed."
            )
            
            # First try to fetch real news content
            real_news_content = self._fetch_real_news_content(target_date)
            
            # Convert real news to ContentSource objects and save to database
            new_real_content_items = []
            for news_data in real_news_content:
                # Check if this URL already exists to avoid duplicates
                existing = ContentSource.query.filter_by(url=news_data['url']).first()
                if not existing:
                    content_item = ContentSource(
                        name=news_data['name'],
                        type=news_data['type'],
                        url=news_data['url'],
                        description=news_data['description'],
                        topic=news_data['topic'],
                        category=news_data['category'],
                        duration=news_data['duration'],
                        published_date=news_data['published_date'],
                        transcript_text=news_data['transcript_text'],
                        language=news_data['language'],
                        region=news_data['region'],
                        license_info=f"Real news from {news_data['name']}",
                        content_metadata=news_data.get('content_metadata', {})
                    )
                    db.session.add(content_item)
                    new_real_content_items.append(content_item)
            
            if new_real_content_items:
                try:
                    db.session.commit()
                    self.logger.info(f"Fetched and saved {len(new_real_content_items)} real news items")
                    content.extend(new_real_content_items)
                except Exception as e:
                    self.logger.error(f"Error saving real news content: {e}")
                    db.session.rollback()
            
            # Check again if we still need more content after adding real news
            total_after_real_news = sum(item.duration for item in content if item.duration)
            
            if total_after_real_news < self.MIN_DURATION:
                self.logger.info(
                    f"Still insufficient content ({total_after_real_news}s < {self.MIN_DURATION}s). "
                    f"Generating additional content via HistoricalNewsGenerator as fallback."
                )
                
                # Use historical generator as final fallback
                generator = HistoricalNewsGenerator()
                generated_articles = generator.generate_news_for_date(target_date)
                
                # Convert generated articles to ContentSource objects and save to database
                new_generated_items = []
                for article_data in generated_articles:
                    # Check if this URL already exists to avoid duplicates
                    existing = ContentSource.query.filter_by(url=article_data['url']).first()
                    if not existing:
                        content_item = ContentSource(
                            name=article_data['name'],
                            type=article_data['type'],
                            url=article_data['url'],
                            description=article_data['description'],
                            topic=article_data['topic'],
                            category=article_data['category'],
                            duration=article_data['duration'],
                            published_date=article_data['published_date'],
                            transcript_text=article_data['transcript_text'],
                            language=article_data['language'],
                            region=article_data['region'],
                            license_info=f"Generated by {article_data['content_metadata']['provider']}",
                            content_metadata=article_data['content_metadata']
                        )
                        db.session.add(content_item)
                        new_generated_items.append(content_item)
                
                if new_generated_items:
                    try:
                        db.session.commit()
                        self.logger.info(f"Generated and saved {len(new_generated_items)} fallback content items")
                        content.extend(new_generated_items)
                    except Exception as e:
                        self.logger.error(f"Error saving generated content: {e}")
                        db.session.rollback()
        
        final_duration = sum(item.duration for item in content if item.duration)
        self.logger.info(
            f"Final content pool: {len(content)} items, {final_duration}s total duration"
        )
        
        return content
    
    def _fetch_real_news_content(self, target_date: date) -> List[Dict]:
        """Fetch real news content from multiple sources"""
        real_content = []
        
        try:
            # Try BBC World Service
            bbc_provider = BBCWorldServiceProvider()
            bbc_content = bbc_provider.fetch_content_for_date(target_date)
            if bbc_content:
                real_content.extend(bbc_content)
                self.logger.info(f"Fetched {len(bbc_content)} BBC articles")
        except Exception as e:
            self.logger.error(f"Error fetching BBC content: {e}")
        
        try:
            # Try Reuters
            reuters_provider = ReutersProvider()
            reuters_content = reuters_provider.fetch_content_for_date(target_date)
            if reuters_content:
                real_content.extend(reuters_content)
                self.logger.info(f"Fetched {len(reuters_content)} Reuters articles")
        except Exception as e:
            self.logger.error(f"Error fetching Reuters content: {e}")
        
        try:
            # Try News API integration (sync current news - it doesn't filter by date)
            content_integration = ContentIntegrationService()
            news_api_count = content_integration.sync_news_content()
            if news_api_count > 0:
                self.logger.info(f"Synced {news_api_count} News API articles to database")
                # Query the newly synced content from database
                recent_news = ContentSource.query.filter(
                    ContentSource.type == 'audio',
                    ContentSource.topic == 'Current Affairs'
                ).limit(10).all()
                for news_item in recent_news:
                    news_data = {
                        'name': news_item.name,
                        'type': news_item.type,
                        'url': news_item.url,
                        'description': news_item.description,
                        'topic': news_item.topic,
                        'category': news_item.category or 'news',
                        'duration': news_item.duration,
                        'published_date': target_date,  # Assign to target date
                        'transcript_text': getattr(news_item, 'transcript_text', news_item.description),
                        'language': 'en',
                        'region': 'global',
                        'content_metadata': {}
                    }
                    real_content.append(news_data)
        except Exception as e:
            self.logger.error(f"Error fetching News API content: {e}")
        
        self.logger.info(f"Total real news content fetched: {len(real_content)} items")
        return real_content
    
    def _select_content_for_edition(self, available_content: List[ContentSource]) -> List[ContentRanking]:
        """Select and rank content to fill approximately 3 hours with deduplication"""
        
        # Deduplicate content first
        deduplicated_content = self._deduplicate_content(available_content)
        
        # Create ranked content items
        ranked_items = []
        for content in deduplicated_content:
            ranking = self._calculate_content_ranking(content)
            ranked_items.append(ranking)
        
        # Sort by score (highest first)
        ranked_items.sort(key=lambda x: x.score, reverse=True)
        
        # Select items to fill target duration 
        selected = self._optimize_content_selection(ranked_items)
        
        # Adjust to reasonable duration range
        selected = self._adjust_to_exact_duration(selected, self.TARGET_DURATION)
        
        self.logger.info(
            f"Selected {len(selected)} items from {len(available_content)} available "
            f"({len(deduplicated_content)} after deduplication, duration: {sum(item.duration_sec for item in selected)}s)"
        )
        
        return selected
    
    def _calculate_content_ranking(self, content: ContentSource) -> ContentRanking:
        """Calculate ranking score for content item"""
        
        score = 0.0
        
        # Base score from duration (prefer 2-8 minute segments)
        duration = content.duration or 180
        if 120 <= duration <= 480:  # 2-8 minutes
            score += 10
        elif duration < 120:
            score += max(0, duration / 120 * 5)  # Scale down for shorter
        else:
            score += max(5, 15 - (duration - 480) / 60)  # Scale down for longer
        
        # Category priority
        category = content.category or 'general'
        category_priority = self.CATEGORY_PRIORITIES.get(category, 5)
        score += category_priority
        
        # Region priority
        region = content.region or 'global'
        region_priority = self.REGION_PRIORITIES.get(region, 5)
        score += region_priority
        
        # Content quality indicators
        if content.transcript_text:
            text_length = len(content.transcript_text)
            if text_length > 200:  # Substantial content
                score += 5
            if text_length > 500:  # Rich content
                score += 3
        
        # Provider diversity bonus
        if content.source_ref:
            provider = ProviderSource.query.get(content.source_ref)
            if provider and 'bbc' in provider.key.lower():
                score += 2  # Slight BBC bonus for quality
        
        # Recency bonus (more recent = slightly better)
        if content.published_date:
            hours_old = (datetime.utcnow() - content.published_date).total_seconds() / 3600
            if hours_old < 24:
                score += max(0, (24 - hours_old) / 24 * 2)
        
        return ContentRanking(
            content=content,
            score=score,
            category_priority=category_priority,
            region_priority=region_priority,
            duration_sec=duration
        )
    
    def _optimize_content_selection(self, ranked_items: List[ContentRanking]) -> List[ContentRanking]:
        """Optimize selection for 3-hour target with diversity"""
        
        selected = []
        total_duration = 0
        used_categories = set()
        used_regions = set()
        
        # First pass: Select high-priority diverse content
        for item in ranked_items:
            if total_duration >= self.TARGET_DURATION:
                break
                
            # Diversity checks
            category_bonus = 0 if item.content.category in used_categories else 5
            region_bonus = 0 if item.content.region in used_regions else 3
            
            # Adjust score for diversity
            adjusted_score = item.score + category_bonus + region_bonus
            
            # Accept if it improves diversity or we need more content
            if (category_bonus > 0 or region_bonus > 0 or 
                total_duration < self.MIN_DURATION or 
                len(selected) < 10):
                
                selected.append(item)
                total_duration += item.duration_sec
                used_categories.add(item.content.category)
                used_regions.add(item.content.region)
        
        # Second pass: Fill remaining time with best available content
        if total_duration < self.TARGET_DURATION:
            remaining_items = [item for item in ranked_items if item not in selected]
            
            # More aggressive approach to reach target duration
            for item in remaining_items:
                if total_duration >= self.TARGET_DURATION:
                    break
                # Accept content that gets us closer to target, even if it exceeds slightly
                if total_duration + item.duration_sec <= self.MAX_DURATION:
                    selected.append(item)
                    total_duration += item.duration_sec
            
            # Third pass: If still short, cycle through the best items again
            if total_duration < self.MIN_DURATION and selected:
                self.logger.info(f"Still short at {total_duration}s, cycling through content again")
                best_items = sorted(ranked_items, key=lambda x: x.score, reverse=True)[:20]
                
                for item in best_items:
                    if total_duration >= self.TARGET_DURATION:
                        break
                    if item not in selected and total_duration + item.duration_sec <= self.MAX_DURATION:
                        selected.append(item)
                        total_duration += item.duration_sec
        
        # Sort final selection by category and region for better flow
        selected.sort(key=lambda x: (
            -x.category_priority,  # Important categories first
            -x.region_priority,    # Important regions first
            -x.score              # Highest quality first
        ))
        
        return selected
    
    def _create_or_update_edition(
        self, 
        target_date: date, 
        edition_number: int,
        selected_content: List[ContentRanking]
    ) -> DailyEdition:
        """Create or update daily edition"""
        
        edition = DailyEdition.query.filter_by(
            date=target_date,
            edition_number=edition_number
        ).first()
        
        total_duration = sum(item.duration_sec for item in selected_content)
        total_words = sum(
            len(item.content.transcript_text.split()) 
            if item.content.transcript_text else 0
            for item in selected_content
        )
        
        if not edition:
            edition = DailyEdition(
                date=target_date,
                edition_number=edition_number,
                title=f'International News - {target_date.strftime("%B %d, %Y")}',
                total_duration_sec=total_duration,
                word_count=total_words,
                status='draft',
                edition_metadata={
                    'composition_date': datetime.utcnow().isoformat(),
                    'target_duration': self.TARGET_DURATION,
                    'sources_count': len(selected_content),
                    'categories': list(set(item.content.category for item in selected_content)),
                    'regions': list(set(item.content.region for item in selected_content))
                }
            )
            db.session.add(edition)
        else:
            # Update existing edition
            edition.total_duration_sec = total_duration
            edition.word_count = total_words
            edition.status = 'draft'
            edition.edition_metadata = {
                **edition.edition_metadata,
                'last_updated': datetime.utcnow().isoformat(),
                'sources_count': len(selected_content)
            }
        
        db.session.commit()
        return edition
    
    def _create_edition_segments(
        self, 
        edition: DailyEdition, 
        selected_content: List[ContentRanking]
    ) -> int:
        """Create edition segments from selected content with deduplication"""
        
        # Clear existing segments to ensure idempotency
        EditionSegment.query.filter_by(edition_id=edition.id).delete()
        db.session.commit()
        
        # Deduplicate content by content ID
        seen_content_ids = set()
        unique_content = []
        
        for item in selected_content:
            if item.content.id not in seen_content_ids:
                unique_content.append(item)
                seen_content_ids.add(item.content.id)
            else:
                self.logger.info(f"Skipping duplicate content ID {item.content.id}")
        
        current_time = 0
        segments_created = 0
        
        # Create a provider entry if needed
        from models import ProviderSource
        provider_key = 'HistoricalNewsGenerator'
        provider = ProviderSource.query.filter_by(key=provider_key).first()
        if not provider:
            provider = ProviderSource(
                key=provider_key,
                name='Historical News Generator',
                type='historical',
                base_url=None,
                active=True
            )
            db.session.add(provider)
            db.session.flush()
        
        for seq, item in enumerate(unique_content, 1):
            try:
                # Check for existing segment with same content to prevent accidental duplicates
                existing_segment = EditionSegment.query.filter_by(
                    edition_id=edition.id,
                    source_content_id=item.content.id
                ).first()
                
                if existing_segment:
                    self.logger.warning(
                        f"Segment with content ID {item.content.id} already exists in edition {edition.id}, skipping"
                    )
                    continue
                
                segment = EditionSegment(
                    edition_id=edition.id,
                    provider_id=provider.id,
                    source_content_id=item.content.id,
                    seq=seq,
                    start_sec=current_time,
                    duration_sec=item.duration_sec,
                    headline=item.content.description[:300] if item.content.description else f'News Update {seq}',
                    region=item.content.region or 'global',
                    category=item.content.category or 'general',
                    transcript_text=item.content.transcript_text,
                    summary={
                        'source': item.content.license_info,
                        'score': round(item.score, 2),
                        'word_count': len(item.content.transcript_text.split()) if item.content.transcript_text else 0
                    },
                    segment_metadata={
                        'original_url': item.content.url,
                        'published_date': item.content.published_date.isoformat() if item.content.published_date else None,
                        'provider_key': 'HistoricalNewsGenerator',
                        'dedup_processed': True
                    }
                )
                
                db.session.add(segment)
                current_time += item.duration_sec
                segments_created += 1
                
            except Exception as e:
                self.logger.error(f"Error creating segment {seq}: {e}")
                continue
        
        db.session.commit()
        self.logger.info(f"Created {segments_created} unique segments for edition {edition.id}")
        return segments_created
    
    def _finalize_edition(self, edition: DailyEdition, selected_content: List[ContentRanking]):
        """Finalize the edition and mark as ready"""
        
        edition.status = 'ready'
        edition.edition_metadata = {
            **edition.edition_metadata,
            'finalized_at': datetime.utcnow().isoformat(),
            'final_duration': sum(item.duration_sec for item in selected_content),
            'segments_count': len(selected_content)
        }
        
        db.session.commit()
        self.logger.info(f"Edition {edition.id} finalized and marked ready")
    
    def _deduplicate_content(self, content_list: List[ContentSource]) -> List[ContentSource]:
        """Remove duplicate content based on normalized title and content similarity"""
        
        import hashlib
        
        seen_hashes = set()
        seen_titles = set() 
        unique_content = []
        duplicates_removed = 0
        
        for content in content_list:
            # Create normalized title (lowercase, remove punctuation)
            normalized_title = ''.join(c.lower() for c in (content.description or 'untitled') if c.isalnum() or c.isspace()).strip()
            normalized_title = ' '.join(normalized_title.split())  # Remove extra whitespace
            
            # Create content hash from transcript text
            content_text = content.transcript_text or ''
            content_hash = hashlib.md5(content_text.encode('utf-8')).hexdigest()[:16]  # First 16 chars of MD5
            
            # Skip if we've seen this URL, title, or content before
            if (content.url in {c.url for c in unique_content} or 
                normalized_title in seen_titles or 
                content_hash in seen_hashes):
                duplicates_removed += 1
                self.logger.debug(f"Removing duplicate: {content.url} (title: {normalized_title[:50]})")
                continue
            
            # Add to unique content
            unique_content.append(content)
            seen_titles.add(normalized_title)
            seen_hashes.add(content_hash)
        
        self.logger.info(
            f"Deduplication complete: {len(unique_content)} unique items, {duplicates_removed} duplicates removed"
        )
        
        return unique_content
    
    def _generate_coverage_summary(self, selected_content: List[ContentRanking]) -> Dict[str, Any]:
        """Generate coverage summary for the edition"""
        
        categories = {}
        regions = {}
        providers = {}
        
        for item in selected_content:
            # Count by category
            cat = item.content.category or 'general'
            categories[cat] = categories.get(cat, 0) + 1
            
            # Count by region
            reg = item.content.region or 'global'
            regions[reg] = regions.get(reg, 0) + 1
            
            # Count by provider from content metadata
            provider_info = item.content.content_metadata if item.content.content_metadata else {}
            if isinstance(provider_info, str):
                import json
                try:
                    provider_info = json.loads(provider_info)
                except:
                    provider_info = {}
            
            prov = provider_info.get('provider', 'Historical News Generator')
            providers[prov] = providers.get(prov, 0) + 1
        
        return {
            'categories': categories,
            'regions': regions,
            'providers': providers,
            'total_segments': len(selected_content),
            'average_duration': sum(item.duration_sec for item in selected_content) / len(selected_content) if selected_content else 0
        }
    
    def _adjust_to_exact_duration(self, selected: List[ContentRanking], target_duration: int) -> List[ContentRanking]:
        """Adjust selection to reach target duration without duplicating content"""
        if not selected:
            return selected
        
        # Remove duplicates first - ensure each content item appears only once
        seen_content_ids = set()
        unique_selected = []
        for item in selected:
            if item.content.id not in seen_content_ids:
                unique_selected.append(item)
                seen_content_ids.add(item.content.id)
        
        selected = unique_selected
        current_duration = sum(item.duration_sec for item in selected)
        
        if current_duration >= self.MIN_DURATION:
            # We have sufficient content, trim if needed
            if current_duration > self.MAX_DURATION:
                # Trim excess by removing items or adjusting duration
                trimmed = []
                running_duration = 0
                
                for item in selected:
                    if running_duration + item.duration_sec <= self.MAX_DURATION:
                        trimmed.append(item)
                        running_duration += item.duration_sec
                    else:
                        # Add partial duration to reach exactly MAX_DURATION
                        remaining = self.MAX_DURATION - running_duration
                        if remaining > 30:  # Only if at least 30 seconds
                            partial_item = ContentRanking(
                                content=item.content,
                                score=item.score,
                                duration_sec=remaining,
                                category_priority=item.category_priority,
                                region_priority=item.region_priority
                            )
                            trimmed.append(partial_item)
                        break
                
                selected = trimmed
            
            final_duration = sum(item.duration_sec for item in selected)
            self.logger.info(f"Final duration after adjustment: {final_duration}s (target: {target_duration}s)")
            return selected
        
        else:
            # Insufficient content - log warning but proceed
            gap = target_duration - current_duration
            self.logger.warning(
                f"Insufficient content: {current_duration}s available, {gap}s gap to target. "
                f"Proceeding with {len(selected)} unique items."
            )
            return selected


def test_composition():
    """Test function for edition composition"""
    with app.app_context():
        composer = DailyEditionComposer()
        
        # Test with 2018-01-01 (user's requested start date)
        test_date = date(2018, 1, 1)
        result = composer.compose_daily_edition(test_date)
        
        print(f"Composition test result: {result}")
        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_composition()