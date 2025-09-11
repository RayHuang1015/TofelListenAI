"""
Real Content Providers for Historical International News
Handles fetching actual content from BBC, Reuters, AP, and other international sources
"""

import logging
import requests
import feedparser
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import time
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json

from app import db
from models import ContentSource, ProviderSource


class RealContentProvider:
    """Base class for real content providers"""
    
    def __init__(self, provider_name: str, base_url: str):
        self.provider_name = provider_name
        self.base_url = base_url
        self.logger = logging.getLogger(f"{__name__}.{provider_name}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; TOEFL Practice Bot/1.0)'
        })
    
    def fetch_content_for_date(self, target_date: date) -> List[Dict]:
        """Fetch content for a specific date. Override in subclasses."""
        raise NotImplementedError
    
    def extract_text_content(self, url: str) -> Optional[str]:
        """Extract text content from a URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Find main content area
            content_selectors = [
                'article', '.article-body', '.story-body', '.content',
                'main', '.main-content', '.post-content', 'div[role="main"]'
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Get text and clean it
                text = main_content.get_text(separator=' ', strip=True)
                # Clean multiple spaces and newlines
                text = re.sub(r'\s+', ' ', text)
                return text[:5000] if text else None  # Limit to 5000 chars
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {url}: {e}")
        
        return None
    
    def estimate_duration(self, text: str) -> int:
        """Estimate reading duration based on text length (180 words per minute)"""
        if not text:
            return 0
        
        word_count = len(text.split())
        # Assume 180 words per minute reading speed
        minutes = word_count / 180
        return max(60, int(minutes * 60))  # At least 1 minute


class BBCWorldServiceProvider(RealContentProvider):
    """BBC World Service content provider"""
    
    def __init__(self):
        super().__init__("BBC World Service", "https://www.bbc.com")
        self.rss_feeds = [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://feeds.bbci.co.uk/news/business/rss.xml",
            "http://feeds.bbci.co.uk/news/politics/rss.xml",
            "http://feeds.bbci.co.uk/news/technology/rss.xml"
        ]
    
    def fetch_content_for_date(self, target_date: date) -> List[Dict]:
        """Fetch BBC content for a specific date"""
        content_items = []
        
        for feed_url in self.rss_feeds:
            try:
                self.logger.info(f"Fetching BBC feed: {feed_url}")
                
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse published date
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6]).date()
                        elif hasattr(entry, 'published'):
                            pub_date = datetime.strptime(entry.published[:10], '%Y-%m-%d').date()
                        else:
                            continue
                    except:
                        continue
                    
                    # Check if it's from our target date (±1 day tolerance for historical content)
                    date_diff = abs((pub_date - target_date).days)
                    if date_diff <= 1:
                        
                        # Extract text content
                        text_content = self.extract_text_content(entry.link)
                        if text_content and len(text_content.split()) > 50:  # At least 50 words
                            
                            duration = self.estimate_duration(text_content)
                            
                            content_item = {
                                'name': 'BBC World Service',
                                'url': entry.link,
                                'type': 'news',
                                'language': 'en',
                                'duration': duration,
                                'description': entry.title,
                                'topic': getattr(entry, 'category', 'World News'),
                                'category': self._extract_category_from_feed(feed_url),
                                'published_date': datetime.combine(pub_date, datetime.min.time()),
                                'transcript_text': text_content,
                                'region': 'global',
                                'content_metadata': {
                                    'source': 'bbc_rss',
                                    'feed_url': feed_url,
                                    'original_title': entry.title,
                                    'summary': getattr(entry, 'summary', '')[:500]
                                }
                            }
                            content_items.append(content_item)
                
                # Be respectful to BBC servers
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error fetching BBC feed {feed_url}: {e}")
        
        self.logger.info(f"Found {len(content_items)} BBC articles for {target_date}")
        return content_items
    
    def _extract_category_from_feed(self, feed_url: str) -> str:
        """Extract category from feed URL"""
        if 'business' in feed_url:
            return 'business'
        elif 'politics' in feed_url:
            return 'politics'
        elif 'technology' in feed_url:
            return 'technology'
        else:
            return 'world'


class ReutersProvider(RealContentProvider):
    """Reuters content provider"""
    
    def __init__(self):
        super().__init__("Reuters International", "https://www.reuters.com")
        self.rss_feeds = [
            "https://feeds.reuters.com/reuters/worldNews",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.reuters.com/reuters/politicsNews",
            "https://feeds.reuters.com/reuters/technologyNews"
        ]
    
    def fetch_content_for_date(self, target_date: date) -> List[Dict]:
        """Fetch Reuters content for a specific date"""
        content_items = []
        
        for feed_url in self.rss_feeds:
            try:
                self.logger.info(f"Fetching Reuters feed: {feed_url}")
                
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse published date
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6]).date()
                        else:
                            continue
                    except:
                        continue
                    
                    # Check if it's from our target date (±1 day tolerance)
                    date_diff = abs((pub_date - target_date).days)
                    if date_diff <= 1:
                        
                        # Extract text content
                        text_content = self.extract_text_content(entry.link)
                        if text_content and len(text_content.split()) > 50:
                            
                            duration = self.estimate_duration(text_content)
                            
                            content_item = {
                                'name': 'Reuters International',
                                'url': entry.link,
                                'type': 'news',
                                'language': 'en',
                                'duration': duration,
                                'description': entry.title,
                                'topic': getattr(entry, 'category', 'International News'),
                                'category': self._extract_category_from_feed(feed_url),
                                'published_date': datetime.combine(pub_date, datetime.min.time()),
                                'transcript_text': text_content,
                                'region': 'global',
                                'content_metadata': {
                                    'source': 'reuters_rss',
                                    'feed_url': feed_url,
                                    'original_title': entry.title,
                                    'summary': getattr(entry, 'summary', '')[:500]
                                }
                            }
                            content_items.append(content_item)
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                self.logger.error(f"Error fetching Reuters feed {feed_url}: {e}")
        
        self.logger.info(f"Found {len(content_items)} Reuters articles for {target_date}")
        return content_items
    
    def _extract_category_from_feed(self, feed_url: str) -> str:
        """Extract category from feed URL"""
        if 'business' in feed_url:
            return 'business'
        elif 'politics' in feed_url:
            return 'politics'
        elif 'technology' in feed_url:
            return 'technology'
        else:
            return 'world'


class APNewsProvider(RealContentProvider):
    """Associated Press News provider"""
    
    def __init__(self):
        super().__init__("AP News International", "https://apnews.com")
        self.rss_feeds = [
            "https://feeds.apnews.com/rss/apf-intlnews",
            "https://feeds.apnews.com/rss/apf-topnews",
            "https://feeds.apnews.com/rss/apf-business",
            "https://feeds.apnews.com/rss/apf-politics"
        ]
    
    def fetch_content_for_date(self, target_date: date) -> List[Dict]:
        """Fetch AP News content for a specific date"""
        content_items = []
        
        for feed_url in self.rss_feeds:
            try:
                self.logger.info(f"Fetching AP News feed: {feed_url}")
                
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse published date
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6]).date()
                        else:
                            continue
                    except:
                        continue
                    
                    # Check if it's from our target date (±1 day tolerance)
                    date_diff = abs((pub_date - target_date).days)
                    if date_diff <= 1:
                        
                        # Extract text content
                        text_content = self.extract_text_content(entry.link)
                        if text_content and len(text_content.split()) > 50:
                            
                            duration = self.estimate_duration(text_content)
                            
                            content_item = {
                                'name': 'AP News International',
                                'url': entry.link,
                                'type': 'news',
                                'language': 'en',
                                'duration': duration,
                                'description': entry.title,
                                'topic': getattr(entry, 'category', 'Breaking News'),
                                'category': self._extract_category_from_feed(feed_url),
                                'published_date': datetime.combine(pub_date, datetime.min.time()),
                                'transcript_text': text_content,
                                'region': 'global',
                                'content_metadata': {
                                    'source': 'ap_rss',
                                    'feed_url': feed_url,
                                    'original_title': entry.title,
                                    'summary': getattr(entry, 'summary', '')[:500]
                                }
                            }
                            content_items.append(content_item)
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                self.logger.error(f"Error fetching AP News feed {feed_url}: {e}")
        
        self.logger.info(f"Found {len(content_items)} AP News articles for {target_date}")
        return content_items
    
    def _extract_category_from_feed(self, feed_url: str) -> str:
        """Extract category from feed URL"""
        if 'business' in feed_url:
            return 'business'
        elif 'politics' in feed_url:
            return 'politics'
        elif 'intlnews' in feed_url:
            return 'international'
        else:
            return 'news'


class RealContentOrchestrator:
    """Orchestrates multiple real content providers"""
    
    def __init__(self):
        self.providers = [
            BBCWorldServiceProvider(),
            ReutersProvider(),
            APNewsProvider()
        ]
        self.logger = logging.getLogger(__name__)
    
    def fetch_content_for_date(self, target_date: date) -> List[Dict]:
        """Fetch content from all providers for a specific date"""
        all_content = []
        
        for provider in self.providers:
            try:
                provider_content = provider.fetch_content_for_date(target_date)
                all_content.extend(provider_content)
                
                # Short delay between providers
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error with provider {provider.provider_name}: {e}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_content = []
        for item in all_content:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_content.append(item)
        
        self.logger.info(f"Fetched {len(unique_content)} unique articles for {target_date}")
        return unique_content
    
    def save_content_to_database(self, content_items: List[Dict]) -> int:
        """Save content items to database"""
        saved_count = 0
        
        for item in content_items:
            try:
                # Check if content already exists
                existing = ContentSource.query.filter_by(url=item['url']).first()
                if existing:
                    continue
                
                # Create new content source
                content = ContentSource()
                content.name = item['name']
                content.url = item['url']
                content.type = item['type']
                content.language = item['language']
                content.duration = item['duration']
                content.description = item['description']
                content.topic = item['topic']
                content.category = item['category']
                content.published_date = item['published_date']
                content.transcript_text = item['transcript_text']
                content.region = item.get('region', 'global')
                content.content_metadata = json.dumps(item['content_metadata'])
                
                db.session.add(content)
                saved_count += 1
                
            except Exception as e:
                self.logger.error(f"Error saving content item: {e}")
        
        try:
            db.session.commit()
            self.logger.info(f"Saved {saved_count} new content items to database")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error committing content to database: {e}")
            saved_count = 0
        
        return saved_count


# Convenience function for route usage
def fetch_real_content_for_date(target_date: date) -> Dict[str, any]:
    """Fetch and save real content for a specific date"""
    from datetime import date as date_class
    today = date_class.today()
    
    # If target_date is historical (before today), use historical generator
    if target_date < today:
        logging.getLogger(__name__).info(f"Using historical news generator for {target_date}")
        from services.historical_news_generator import HistoricalNewsGenerator
        generator = HistoricalNewsGenerator()
        articles = generator.generate_news_for_date(target_date)
        
        # Save to database using orchestrator
        orchestrator = RealContentOrchestrator()
        saved_count = orchestrator.save_content_to_database(articles)
        
        # After saving content, compose daily edition
        from services.daily_edition_composer import DailyEditionComposer
        composer = DailyEditionComposer()
        composition_result = composer.compose_daily_edition(target_date)
        
        return {
            'status': 'success',
            'date': target_date,
            'items_fetched': len(articles),
            'items_saved': saved_count,
            'providers_used': 1,  # HistoricalNewsGenerator
            'composition_result': composition_result
        }
    
    # For today and future dates, use real RSS providers
    orchestrator = RealContentOrchestrator()
    
    try:
        # Fetch content from all providers
        content_items = orchestrator.fetch_content_for_date(target_date)
        
        # Save to database
        saved_count = orchestrator.save_content_to_database(content_items)
        
        return {
            'status': 'success',
            'date': target_date,
            'items_fetched': len(content_items),
            'items_saved': saved_count,
            'providers_used': len(orchestrator.providers)
        }
        
    except Exception as e:
        logging.error(f"Error in fetch_real_content_for_date: {e}")
        return {
            'status': 'error',
            'date': target_date,
            'error': str(e)
        }