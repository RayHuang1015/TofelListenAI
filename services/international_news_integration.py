"""
International News Integration Service
Handles multiple news sources (BBC, CNN, Reuters, AP) for daily 3-hour compilations
"""

import logging
import requests
import feedparser
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import re
from urllib.parse import urljoin, urlparse

from app import app, db
from models import ProviderSource, DailyEdition, EditionSegment, ContentSource, IngestionJob


@dataclass
class NormalizedNewsItem:
    """Standardized news item from any provider"""
    title: str
    url: str
    description: str
    published_at: datetime
    region: str = 'global'
    category: str = 'general'
    duration_estimate: int = 180  # seconds (3 minutes default)
    transcript_text: str = ''
    language: str = 'en'
    provider_key: str = ''
    original_data: Dict = None


class InternationalNewsIntegration:
    """Main integration service for international news sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_active_providers(self) -> List[ProviderSource]:
        """Get all active news providers"""
        return ProviderSource.query.filter_by(active=True).all()
    
    def ingest_for_date(self, target_date: date) -> Dict[str, Any]:
        """
        Ingest international news for a specific date from all providers
        
        Args:
            target_date: Date to ingest news for
            
        Returns:
            Dict with status, items_found, providers_processed, errors
        """
        with app.app_context():
            # Check for existing ingestion job
            job = IngestionJob.query.filter_by(date=target_date).first()
            if not job:
                job = IngestionJob(
                    date=target_date,
                    status='running',
                    started_at=datetime.utcnow(),
                    attempts=1
                )
                db.session.add(job)
                db.session.commit()
            else:
                job.attempts += 1
                job.status = 'running'
                job.started_at = datetime.utcnow()
                db.session.commit()
            
            try:
                providers = self.get_active_providers()
                all_items = []
                errors = []
                
                self.logger.info(f"Starting ingestion for {target_date} with {len(providers)} providers")
                
                for provider in providers:
                    try:
                        items = self._fetch_from_provider(provider, target_date)
                        all_items.extend(items)
                        self.logger.info(f"Fetched {len(items)} items from {provider.name}")
                    except Exception as e:
                        error_msg = f"Error fetching from {provider.name}: {str(e)}"
                        errors.append(error_msg)
                        self.logger.error(error_msg)
                
                # Save normalized items to ContentSource
                saved_count = self._save_items_to_database(all_items, target_date)
                
                # Create or update daily edition
                edition = self._create_daily_edition(target_date, saved_count)
                
                # Update job status
                job.status = 'completed'
                job.finished_at = datetime.utcnow()
                job.stats = {
                    'providers_processed': len(providers),
                    'total_items_found': len(all_items),
                    'items_saved': saved_count,
                    'errors': len(errors)
                }
                db.session.commit()
                
                return {
                    'status': 'success',
                    'date': str(target_date),
                    'items_found': len(all_items),
                    'items_saved': saved_count,
                    'providers_processed': len(providers),
                    'edition_id': edition.id if edition else None,
                    'errors': errors
                }
                
            except Exception as e:
                job.status = 'failed'
                job.last_error = str(e)
                job.finished_at = datetime.utcnow()
                db.session.commit()
                
                self.logger.error(f"Ingestion failed for {target_date}: {e}")
                return {
                    'status': 'failed',
                    'date': str(target_date),
                    'error': str(e)
                }
    
    def _fetch_from_provider(self, provider: ProviderSource, target_date: date) -> List[NormalizedNewsItem]:
        """Fetch news items from a specific provider"""
        
        if provider.type == 'rss':
            return self._fetch_from_rss(provider, target_date)
        elif provider.type == 'api':
            return self._fetch_from_api(provider, target_date)
        else:
            self.logger.warning(f"Unsupported provider type: {provider.type}")
            return []
    
    def _fetch_from_rss(self, provider: ProviderSource, target_date: date) -> List[NormalizedNewsItem]:
        """Fetch from RSS feed"""
        try:
            response = requests.get(provider.base_url, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            items = []
            
            for entry in feed.entries[:50]:  # Limit to 50 items per provider
                try:
                    # Parse published date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.utcnow()
                    
                    # Filter by date (within 24 hours of target)
                    target_datetime = datetime.combine(target_date, datetime.min.time())
                    if abs((pub_date - target_datetime).days) > 1:
                        continue
                    
                    # Extract content
                    description = getattr(entry, 'description', '')
                    if hasattr(entry, 'content') and entry.content:
                        description = entry.content[0].value if entry.content else description
                    
                    # Clean HTML
                    description = re.sub(r'<[^>]+>', '', description)
                    
                    # Estimate reading time (180 words per minute)
                    word_count = len(description.split())
                    duration_estimate = max(120, min(600, word_count * 60 // 180))  # 2-10 minutes
                    
                    item = NormalizedNewsItem(
                        title=getattr(entry, 'title', 'Untitled'),
                        url=getattr(entry, 'link', provider.base_url),
                        description=description,
                        published_at=pub_date,
                        region=self._categorize_region(entry.title if hasattr(entry, 'title') else ''),
                        category=self._categorize_content(entry.title if hasattr(entry, 'title') else ''),
                        duration_estimate=duration_estimate,
                        transcript_text=description,
                        provider_key=provider.key,
                        original_data={'feed_entry': dict(entry)}
                    )
                    
                    items.append(item)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing RSS entry from {provider.name}: {e}")
                    continue
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error fetching RSS from {provider.name}: {e}")
            return []
    
    def _fetch_from_api(self, provider: ProviderSource, target_date: date) -> List[NormalizedNewsItem]:
        """Fetch from API (to be implemented for specific APIs)"""
        # Placeholder for API-based providers like NewsAPI, Guardian API, etc.
        self.logger.info(f"API fetching not yet implemented for {provider.name}")
        return []
    
    def _categorize_region(self, title: str) -> str:
        """Categorize news by region based on title"""
        title_lower = title.lower()
        
        # Simple keyword-based categorization
        if any(word in title_lower for word in ['china', 'asia', 'japan', 'korea', 'india']):
            return 'asia'
        elif any(word in title_lower for word in ['europe', 'uk', 'france', 'germany', 'russia']):
            return 'europe'
        elif any(word in title_lower for word in ['africa', 'nigeria', 'south africa']):
            return 'africa'
        elif any(word in title_lower for word in ['america', 'us', 'usa', 'canada', 'mexico']):
            return 'americas'
        elif any(word in title_lower for word in ['middle east', 'israel', 'iran', 'saudi']):
            return 'middle_east'
        else:
            return 'global'
    
    def _categorize_content(self, title: str) -> str:
        """Categorize news by content type"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['business', 'economy', 'market', 'trade', 'finance']):
            return 'business'
        elif any(word in title_lower for word in ['technology', 'tech', 'ai', 'cyber', 'digital']):
            return 'technology'
        elif any(word in title_lower for word in ['health', 'medical', 'disease', 'virus', 'pandemic']):
            return 'health'
        elif any(word in title_lower for word in ['climate', 'environment', 'weather', 'global warming']):
            return 'environment'
        elif any(word in title_lower for word in ['sport', 'football', 'olympics', 'soccer']):
            return 'sports'
        elif any(word in title_lower for word in ['politics', 'election', 'government', 'policy']):
            return 'politics'
        else:
            return 'general'
    
    def _save_items_to_database(self, items: List[NormalizedNewsItem], target_date: date) -> int:
        """Save normalized items to ContentSource table"""
        saved_count = 0
        
        for item in items:
            try:
                # Check if already exists (by URL)
                existing = ContentSource.query.filter_by(url=item.url).first()
                if existing:
                    continue
                
                # Get provider reference
                provider = ProviderSource.query.filter_by(key=item.provider_key).first()
                
                content = ContentSource(
                    name=f'International News',
                    type='news',
                    url=item.url,
                    description=item.description,
                    duration=item.duration_estimate,
                    topic=item.category,
                    category=item.category,
                    published_date=item.published_at,
                    content_metadata={
                        'provider': item.provider_key,
                        'original_data': item.original_data,
                        'ingestion_date': target_date.isoformat()
                    },
                    transcript_text=item.transcript_text,
                    language=item.language,
                    region=item.region,
                    license_info=f'Source: {provider.name if provider else item.provider_key}',
                    source_ref=provider.id if provider else None
                )
                
                db.session.add(content)
                saved_count += 1
                
            except Exception as e:
                self.logger.error(f"Error saving item {item.title}: {e}")
                continue
        
        try:
            db.session.commit()
            return saved_count
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error committing items to database: {e}")
            return 0
    
    def _create_daily_edition(self, target_date: date, items_count: int) -> Optional[DailyEdition]:
        """Create or update daily edition for the date"""
        try:
            # Check if edition already exists
            edition = DailyEdition.query.filter_by(date=target_date, edition_number=1).first()
            
            if not edition:
                edition = DailyEdition(
                    date=target_date,
                    edition_number=1,
                    title=f'International News - {target_date.strftime("%B %d, %Y")}',
                    total_duration_sec=0,  # Will be calculated later
                    word_count=0,          # Will be calculated later  
                    status='draft',
                    edition_metadata={
                        'items_ingested': items_count,
                        'created_at': datetime.utcnow().isoformat()
                    }
                )
                db.session.add(edition)
                db.session.commit()
                
                self.logger.info(f"Created daily edition for {target_date}")
            
            return edition
            
        except Exception as e:
            self.logger.error(f"Error creating daily edition: {e}")
            return None


def test_integration():
    """Test function for integration"""
    with app.app_context():
        integration = InternationalNewsIntegration()
        
        # Test with a recent date
        test_date = date.today() - timedelta(days=1)
        result = integration.ingest_for_date(test_date)
        
        print(f"Integration test result: {result}")
        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_integration()