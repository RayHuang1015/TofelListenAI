"""
Daily Edition Composer Service
Creates 3-hour international news listening transcripts from ingested content
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


@dataclass
class ContentRanking:
    """Content item with ranking score"""
    content: ContentSource
    score: float
    category_priority: int
    region_priority: int
    duration_sec: int


class DailyEditionComposer:
    """Composes 3-hour daily international news editions"""
    
    TARGET_DURATION = 10800  # 3 hours in seconds
    MIN_DURATION = 9600      # 2h 40min (acceptable minimum)
    MAX_DURATION = 12000     # 3h 20min (acceptable maximum)
    
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
        Compose a 3-hour daily edition for the given date
        
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
        """Get international news content available for the date"""
        
        # Look for content within 24 hours of target date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        content = ContentSource.query.filter(
            ContentSource.name == 'International News',
            ContentSource.published_date >= start_datetime,
            ContentSource.published_date < end_datetime,
            ContentSource.duration > 30,  # At least 30 seconds
            ContentSource.transcript_text.isnot(None)  # Must have transcript
        ).all()
        
        self.logger.info(f"Found {len(content)} content items for {target_date}")
        return content
    
    def _select_content_for_edition(self, available_content: List[ContentSource]) -> List[ContentRanking]:
        """Select and rank content to fill approximately 3 hours"""
        
        # Create ranked content items
        ranked_items = []
        for content in available_content:
            ranking = self._calculate_content_ranking(content)
            ranked_items.append(ranking)
        
        # Sort by score (highest first)
        ranked_items.sort(key=lambda x: x.score, reverse=True)
        
        # Select items to fill target duration with diversity
        selected = self._optimize_content_selection(ranked_items)
        
        self.logger.info(
            f"Selected {len(selected)} items from {len(available_content)} available "
            f"(duration: {sum(item.duration_sec for item in selected)}s)"
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
        if total_duration < self.MIN_DURATION:
            remaining_items = [item for item in ranked_items if item not in selected]
            
            for item in remaining_items:
                if total_duration >= self.MAX_DURATION:
                    break
                if total_duration + item.duration_sec <= self.MAX_DURATION:
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
        """Create edition segments from selected content"""
        
        # Clear existing segments
        EditionSegment.query.filter_by(edition_id=edition.id).delete()
        
        current_time = 0
        segments_created = 0
        
        for seq, item in enumerate(selected_content, 1):
            try:
                # Create segment
                segment = EditionSegment(
                    edition_id=edition.id,
                    provider_id=item.content.source_ref,
                    source_content_id=item.content.id,
                    seq=seq,
                    start_sec=current_time,
                    duration_sec=item.duration_sec,
                    headline=item.content.description[:300] if item.content.description else 'News Update',
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
                        'provider_key': item.content.provider.key if item.content.provider else None
                    }
                )
                
                db.session.add(segment)
                current_time += item.duration_sec
                segments_created += 1
                
            except Exception as e:
                self.logger.error(f"Error creating segment {seq}: {e}")
                continue
        
        db.session.commit()
        self.logger.info(f"Created {segments_created} segments for edition {edition.id}")
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
            
            # Count by provider
            if item.content.provider:
                prov = item.content.provider.name
                providers[prov] = providers.get(prov, 0) + 1
        
        return {
            'categories': categories,
            'regions': regions,
            'providers': providers,
            'total_segments': len(selected_content),
            'average_duration': sum(item.duration_sec for item in selected_content) / len(selected_content)
        }


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