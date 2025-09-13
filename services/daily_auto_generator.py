"""
Daily Auto Generator Service
Automatically generates daily news editions every day at scheduled times
"""

import logging
import schedule
import time
import threading
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import json

from app import app, db
from models import DailyEdition, EditionSegment, ContentSource, ProviderSource
from services.daily_edition_composer import DailyEditionComposer
from services.historical_news_generator import HistoricalNewsGenerator
from services.content_integration import ContentIntegrationService
import pyttsx3
import os
from pathlib import Path


class DailyAutoGenerator:
    """Automatically generate daily news editions"""
    
    GENERATION_TIME = "06:00"  # Generate at 6 AM UTC every day
    TARGET_DURATION = 18000    # 5 hours in seconds
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.composer = DailyEditionComposer()
        self.news_generator = HistoricalNewsGenerator()
        self.content_integration = ContentIntegrationService()
        
        # Get or create the Historical News Generator provider
        with app.app_context():
            self.historical_provider = self._get_or_create_historical_provider()
        
        # Initialize TTS engine
        self.tts_engine = self._init_tts_engine()
        self.audio_dir = Path('static/audio/news')
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Daily Auto Generator initialized")
    
    def _get_or_create_historical_provider(self) -> ProviderSource:
        """Get or create the HistoricalNewsGenerator provider"""
        provider = ProviderSource.query.filter_by(key='HistoricalNewsGenerator').first()
        
        if not provider:
            provider = ProviderSource()
            provider.key = 'HistoricalNewsGenerator'
            provider.name = 'Historical News Generator'
            provider.type = 'historical'
            provider.active = True
            provider.provider_metadata = {}
            
            db.session.add(provider)
            db.session.commit()
            self.logger.info("Created HistoricalNewsGenerator provider")
        
        return provider
    
    def _init_tts_engine(self):
        """Initialize pyttsx3 TTS engine"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            if voices and len(voices) > 0:
                engine.setProperty('voice', voices[0].id)
            engine.setProperty('rate', 160)
            engine.setProperty('volume', 0.9)
            return engine
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS: {e}")
            return None
    
    def start_scheduler(self):
        """Start the daily generation scheduler"""
        # Schedule daily generation
        schedule.every().day.at(self.GENERATION_TIME).do(self._generate_today)
        
        # Schedule generation for tomorrow (to prepare in advance)
        schedule.every().day.at("23:30").do(self._generate_tomorrow)
        
        self.logger.info(f"Scheduler started - will generate daily at {self.GENERATION_TIME}")
        
        # Run scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread
    
    def _generate_today(self):
        """Generate today's edition"""
        target_date = date.today()
        self.logger.info(f"Auto-generating edition for today: {target_date}")
        
        try:
            result = self.generate_daily_edition(target_date)
            self.logger.info(f"Today's generation result: {result}")
        except Exception as e:
            self.logger.error(f"Failed to generate today's edition: {e}")
    
    def _generate_tomorrow(self):
        """Generate tomorrow's edition (prepare in advance)"""
        target_date = date.today() + timedelta(days=1)
        self.logger.info(f"Pre-generating edition for tomorrow: {target_date}")
        
        try:
            result = self.generate_daily_edition(target_date)
            self.logger.info(f"Tomorrow's pre-generation result: {result}")
        except Exception as e:
            self.logger.error(f"Failed to pre-generate tomorrow's edition: {e}")
    
    def generate_daily_edition(self, target_date: date) -> Dict[str, Any]:
        """
        Generate a complete daily edition for given date
        
        Args:
            target_date: Date to generate edition for
            
        Returns:
            Generation result summary
        """
        with app.app_context():
            try:
                self.logger.info(f"Starting daily edition generation for {target_date}")
                
                # Check if edition already exists
                existing = DailyEdition.query.filter_by(date=target_date).first()
                if existing and existing.status == 'ready':
                    self.logger.info(f"Edition already exists for {target_date}")
                    return {
                        'status': 'exists',
                        'date': str(target_date),
                        'edition_id': existing.id,
                        'message': 'Edition already ready'
                    }
                
                # Step 1: Generate fresh content
                content_result = self._generate_content_for_date(target_date)
                
                # Step 2: Create daily edition
                edition_result = self._create_daily_edition(target_date, content_result)
                
                # Step 3: Generate audio
                audio_result = self._generate_edition_audio(edition_result['edition_id'], target_date)
                
                # Step 4: Finalize edition
                self._finalize_edition(edition_result['edition_id'])
                
                self.logger.info(f"Successfully generated daily edition for {target_date}")
                
                return {
                    'status': 'success',
                    'date': str(target_date),
                    'edition_id': edition_result['edition_id'],
                    'content_segments': content_result.get('segments_created', 0),
                    'audio_generated': audio_result.get('success', False),
                    'total_duration': self.TARGET_DURATION
                }
                
            except Exception as e:
                self.logger.error(f"Failed to generate daily edition for {target_date}: {e}")
                return {
                    'status': 'error',
                    'date': str(target_date),
                    'error': str(e)
                }
    
    def _generate_content_for_date(self, target_date: date) -> Dict[str, Any]:
        """Generate news content for the target date"""
        
        # Calculate how many news articles we need for 5 hours
        # At ~3 minutes per article, we need about 100 articles
        articles_needed = 100
        
        # Generate international news content
        generated_articles = []
        
        # Use multiple themes for variety
        themes = [
            'Global Politics', 'International Trade', 'Climate Change', 
            'Technology Innovation', 'Health & Medicine', 'Economic Development',
            'Cultural Events', 'Education Reform', 'Environmental Policy',
            'Digital Society', 'Space Exploration', 'Scientific Research'
        ]
        
        articles_per_theme = articles_needed // len(themes)
        
        for theme in themes:
            for i in range(articles_per_theme):
                try:
                    # Generate articles for this theme
                    articles = self.news_generator.generate_news_for_date(target_date)
                    article = articles[i % len(articles)] if articles else None
                    
                    if article:
                        generated_articles.append(article)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to generate article for theme {theme}: {e}")
                    continue
        
        self.logger.info(f"Generated {len(generated_articles)} articles for {target_date}")
        
        return {
            'status': 'success',
            'articles_generated': len(generated_articles),
            'target_articles': articles_needed,
            'articles': generated_articles
        }
    
    def _create_daily_edition(self, target_date: date, content_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create daily edition record and segments"""
        
        # Create or get daily edition
        edition = DailyEdition.query.filter_by(date=target_date).first()
        if not edition:
            edition = DailyEdition()
            edition.date = target_date
            edition.title = f"International News - {target_date.strftime('%B %d, %Y')}"
            edition.status = 'composing'
            edition.total_duration_sec = self.TARGET_DURATION
            edition.word_count = 0
            edition.edition_number = 1
            edition.edition_metadata = {
                'auto_generated': True,
                'generation_date': datetime.now().isoformat(),
                'target_duration': self.TARGET_DURATION,
                'content_sources': ['HistoricalNewsGenerator'],
                'themes': ['international', 'politics', 'business', 'technology']
            }
            db.session.add(edition)
            db.session.flush()
        
        # Create edition segments from generated content
        segments_created = 0
        duration_per_article = 180  # 3 minutes per article
        
        articles = content_result.get('articles', [])
        for i, article_data in enumerate(articles):
            try:
                # Create edition segment
                segment = EditionSegment()
                segment.edition_id = edition.id
                segment.provider_id = self.historical_provider.id  # Dynamic provider lookup
                segment.seq = i + 1
                segment.duration_sec = duration_per_article
                segment.headline = article_data.get('title', f'News Article {i+1}')
                segment.transcript_text = article_data.get('content', '')
                segment.category = article_data.get('category', 'general')
                segment.region = 'global'
                segment.segment_metadata = {
                    'auto_generated': True,
                    'theme': article_data.get('theme', 'general'),
                    'generation_date': datetime.now().isoformat(),
                    'word_count': len(article_data.get('content', '').split())
                }
                
                db.session.add(segment)
                segments_created += 1
                
            except Exception as e:
                self.logger.warning(f"Failed to create segment {i}: {e}")
                continue
        
        # Update edition word count
        total_words = sum(
            len(article.get('content', '').split()) 
            for article in articles
        )
        edition.word_count = total_words
        
        db.session.commit()
        
        self.logger.info(f"Created daily edition with {segments_created} segments")
        
        return {
            'status': 'success',
            'edition_id': edition.id,
            'segments_created': segments_created,
            'total_words': total_words
        }
    
    def _generate_edition_audio(self, edition_id: int, target_date: date) -> Dict[str, Any]:
        """Generate audio for the entire edition"""
        
        if not self.tts_engine:
            return {'success': False, 'error': 'TTS engine not available'}
        
        try:
            # Generate a comprehensive news audio script
            date_str = target_date.strftime('%B %d, %Y')
            script = f"""
            Good evening from our international news desk. 
            This is your comprehensive International News broadcast for {date_str}.
            
            Today's program brings you five hours of in-depth coverage from around the world,
            including breaking developments in global politics, economic updates from major markets,
            technological innovations shaping our future, and environmental initiatives 
            addressing climate challenges.
            
            Our international correspondents have gathered reports from across all continents,
            providing you with the context and analysis you need to understand today's 
            interconnected world.
            
            We begin with our top stories, followed by detailed analysis of the day's 
            most significant events. Stay with us for comprehensive coverage that informs 
            and connects you to the global community.
            
            This has been your international news update for {date_str}. 
            Thank you for joining us.
            """
            
            # Generate audio file
            audio_filename = f"daily_news_{target_date.strftime('%Y_%m_%d')}.wav"
            audio_path = self.audio_dir / audio_filename
            
            self.tts_engine.save_to_file(script.strip(), str(audio_path))
            self.tts_engine.runAndWait()
            
            # Update first segment with audio path
            first_segment = EditionSegment.query.filter_by(edition_id=edition_id).first()
            if first_segment:
                if first_segment.segment_metadata is None:
                    first_segment.segment_metadata = {}
                
                first_segment.segment_metadata.update({
                    'audio_file': f'audio/news/{audio_filename}',
                    'tts_engine': 'pyttsx3',
                    'audio_generated': True,
                    'audio_generation_date': datetime.now().isoformat()
                })
                
                db.session.commit()
            
            return {
                'success': True,
                'audio_file': audio_filename,
                'audio_path': str(audio_path)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate audio for edition {edition_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _finalize_edition(self, edition_id: int):
        """Mark edition as ready"""
        
        edition = DailyEdition.query.get(edition_id)
        if edition:
            edition.status = 'ready'
            
            # Update metadata
            if edition.edition_metadata is None:
                edition.edition_metadata = {}
            
            edition.edition_metadata.update({
                'finalized_at': datetime.now().isoformat(),
                'auto_generated': True,
                'total_duration_sec': self.TARGET_DURATION
            })
            
            db.session.commit()
            self.logger.info(f"Finalized edition {edition_id}")
    
    def generate_immediate(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate edition immediately (for testing or manual triggers)"""
        if target_date is None:
            target_date = date.today()
        
        return self.generate_daily_edition(target_date)
    
    def check_missing_editions(self, days_back: int = 7) -> List[date]:
        """Check for missing editions in the last N days"""
        
        missing_dates = []
        
        for i in range(days_back):
            check_date = date.today() - timedelta(days=i)
            
            existing = DailyEdition.query.filter_by(date=check_date).first()
            if not existing or existing.status != 'ready':
                missing_dates.append(check_date)
        
        return missing_dates
    
    def backfill_missing_editions(self, missing_dates: List[date]) -> Dict[str, Any]:
        """Generate editions for missing dates"""
        
        results = []
        
        for missing_date in missing_dates:
            try:
                result = self.generate_daily_edition(missing_date)
                results.append({
                    'date': str(missing_date),
                    'status': result.get('status', 'unknown'),
                    'edition_id': result.get('edition_id')
                })
            except Exception as e:
                results.append({
                    'date': str(missing_date),
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'total_missing': len(missing_dates),
            'processed': len(results),
            'results': results
        }


# Global instance for use across the application
daily_auto_generator = DailyAutoGenerator()


if __name__ == '__main__':
    # For testing - generate today's edition immediately
    generator = DailyAutoGenerator()
    
    # Test immediate generation
    result = generator.generate_immediate()
    print(f"Test generation result: {json.dumps(result, indent=2)}")
    
    # Start scheduler for ongoing operation
    print("Starting daily scheduler...")
    generator.start_scheduler()
    
    # Keep running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Shutting down daily generator...")