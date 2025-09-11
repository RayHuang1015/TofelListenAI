import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from app import db
from models import ContentSource, Question
from services.youtube_content_fetcher import YouTubeContentFetcher
from services.ai_question_generator import AIQuestionGenerator
from services.archive_org_integration import ArchiveOrgIntegration

class ABCNewsIntegration:
    """Service for integrating ABC News Live content from YouTube"""
    
    def __init__(self):
        self.youtube_fetcher = YouTubeContentFetcher()
        self.question_generator = AIQuestionGenerator()
        self.archive_org = ArchiveOrgIntegration()
        
    def sync_abc_news_content(self, start_year: int = 2024, end_year: int = 2025) -> Dict:
        """Sync ABC News authentic content from Archive.org for specified year range"""
        logging.info(f"Syncing ABC News from Archive.org for {start_year}-{end_year}")
        
        results = {
            'total_days_processed': 0,
            'total_content_created': 0,
            'years_processed': [],
            'errors': []
        }
        
        try:
            # Use Archive.org integration for authentic content instead of YouTube
            for year in range(start_year, min(end_year + 1, datetime.now().year + 1)):
                logging.info(f"Processing Archive.org ABC News content for year {year}")
                
                # Create date range for the year
                start_date = datetime(year, 1, 1)
                
                # Calculate end date for the year (don't go beyond current date)
                if year == datetime.now().year:
                    end_date = datetime.now()
                else:
                    end_date = datetime(year, 12, 31)
                
                # Use Archive.org integration for authentic daily content
                year_results = self.archive_org.sync_date_range(start_date, end_date)
                
                results['total_days_processed'] += year_results['total_days']
                results['total_content_created'] += year_results['content_created']
                results['years_processed'].append(year)
                
                if year_results['errors']:
                    results['errors'].extend([f"{year}: {error}" for error in year_results['errors']])
                
                logging.info(f"Year {year}: Processed {year_results['total_days']} days, created {year_results['content_created']} authentic daily editions")
                
                # Rate limiting between years
                import time
                time.sleep(1)
                
        except Exception as e:
            error_msg = f"Error during Archive.org ABC News sync: {e}"
            logging.error(error_msg)
            results['errors'].append(error_msg)
        
        logging.info(f"Archive.org sync completed: {results['total_content_created']} authentic daily editions created")
        return results
    
    def _save_videos_to_database(self, videos: List[Dict]) -> int:
        """Save YouTube videos to database as ContentSource entries"""
        saved_count = 0
        
        for video_data in videos:
            try:
                # Check if video already exists
                existing = ContentSource.query.filter_by(
                    url=video_data['video_url']
                ).first()
                
                if existing:
                    continue  # Skip if already exists
                
                # Create transcript placeholder
                transcript = self.youtube_fetcher.get_video_transcript_placeholder(video_data)
                
                # Create content metadata
                content_metadata = {
                    'transcript': transcript,
                    'video_data': {
                        'video_id': video_data['video_id'],
                        'youtube_url': video_data['video_url'],
                        'thumbnail_url': video_data.get('thumbnail_url', ''),
                        'view_count': video_data.get('view_count', 0),
                        'tags': video_data.get('tags', []),
                        'source': 'youtube'
                    },
                    'content_data': {
                        'type': 'abc_news_live',
                        'category': video_data.get('category', 'General News'),
                        'original_title': video_data.get('title', ''),
                        'fetched_from': 'youtube_api',
                        'duration': video_data.get('duration', 0)
                    }
                }
                
                # Create ContentSource entry
                content = ContentSource(
                    name='ABC News',
                    type='news',
                    url=video_data['video_url'],
                    description=self._clean_title(video_data.get('title', '')),
                    category=video_data.get('category', 'General News'),
                    difficulty_level=self._determine_difficulty(video_data),
                    duration=video_data.get('duration', 0),
                    topic=video_data.get('category', 'General News'),
                    published_date=video_data.get('published_date'),
                    content_metadata=json.dumps(content_metadata, ensure_ascii=False, default=str)
                )
                
                db.session.add(content)
                db.session.flush()  # Get the ID
                
                # Generate questions for this content
                self._generate_questions_for_content(content)
                
                saved_count += 1
                
            except Exception as e:
                logging.error(f"Error saving video {video_data.get('video_id', 'unknown')}: {e}")
                continue
        
        try:
            db.session.commit()
            logging.info(f"Successfully saved {saved_count} ABC News videos to database")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error committing to database: {e}")
            saved_count = 0
        
        return saved_count
    
    def _clean_title(self, title: str) -> str:
        """Clean and format video title for better display"""
        # Remove common YouTube title patterns
        title = title.replace('ABC News Live:', '').replace('LIVE:', '').strip()
        
        # Limit length for better UI display
        if len(title) > 100:
            title = title[:97] + '...'
        
        return title
    
    def _determine_difficulty(self, video_data: Dict) -> str:
        """Determine difficulty level based on video characteristics"""
        duration = video_data.get('duration', 0)
        category = video_data.get('category', '').lower()
        
        # Shorter videos tend to be easier to follow
        if duration < 600:  # Less than 10 minutes
            return 'intermediate'
        elif duration < 1800:  # Less than 30 minutes
            return 'intermediate'
        else:
            return 'advanced'
        
        # Some categories are inherently more complex
        complex_categories = ['politics', 'international', 'economy', 'technology']
        if any(cat in category for cat in complex_categories):
            return 'advanced'
        
        return 'intermediate'
    
    def _generate_questions_for_content(self, content: ContentSource) -> None:
        """Generate TOEFL-style questions for ABC News content"""
        try:
            # Generate questions using the AI question generator
            questions_data = self.question_generator.generate_questions(content)
            
            for q_data in questions_data:
                question = Question(
                    content_id=content.id,
                    question_text=q_data.get('question_text', ''),
                    question_type=q_data.get('question_type', 'multiple_choice'),
                    options=q_data.get('options', []),
                    correct_answer=str(q_data.get('correct_answer', 0)),
                    explanation=q_data.get('explanation', ''),
                    difficulty=content.difficulty_level
                )
                db.session.add(question)
                
        except Exception as e:
            logging.error(f"Error generating questions for content {content.id}: {e}")
    
    def sync_daily_editions(self, start_date: datetime, end_date: datetime) -> Dict:
        """Sync authentic daily news editions from Archive.org for specific date range"""
        logging.info(f"Syncing ABC News from Archive.org for {start_date.date()} to {end_date.date()}")
        
        # Use Archive.org integration for authentic daily content
        results = self.archive_org.sync_date_range(start_date, end_date)
        
        # Convert Archive.org results to match expected format
        formatted_results = {
            'total_days_processed': results['total_days'],
            'successful_days': results['successful_days'],
            'daily_editions_created': results['content_created'],
            'errors': results['errors']
        }
        
        logging.info(f"Archive.org sync completed: {results['content_created']} authentic daily editions created")
        return formatted_results
    
    def _save_daily_edition_to_database(self, daily_edition: Dict) -> bool:
        """Save a daily edition composite playlist to database"""
        try:
            date = daily_edition['date']
            
            # Remove existing entry for this date if it exists
            existing = ContentSource.query.filter(
                ContentSource.name == 'ABC News',
                db.func.date(ContentSource.published_date) == date
            ).first()
            
            if existing:
                db.session.delete(existing)
                
            # Create content metadata for composite playlist
            content_metadata = {
                'composite': True,
                'daily_edition': True,
                'date': str(date),
                'total_duration': daily_edition['total_duration'],
                'video_count': daily_edition['video_count'],
                'segments': daily_edition['videos'],
                'playlist_url': daily_edition.get('playlist_url'),
                'source': 'youtube_daily_search',
                'fetched_at': datetime.now().isoformat()
            }
            
            # Create main video info from first segment for compatibility
            main_video = daily_edition['videos'][0] if daily_edition['videos'] else {}
            
            # Create ContentSource entry
            content = ContentSource(
                name='ABC News',
                type='news',
                url=daily_edition.get('playlist_url') or main_video.get('video_url', ''),
                description=daily_edition['description'],
                category=main_video.get('category', 'General News'),
                difficulty_level='intermediate',
                duration=daily_edition['total_duration'],
                topic='Daily News',
                published_date=datetime.combine(date, datetime.min.time()),
                content_metadata=json.dumps(content_metadata, ensure_ascii=False, default=str)
            )
            
            db.session.add(content)
            db.session.commit()
            
            logging.info(f"Saved daily edition for {date}: {daily_edition['video_count']} segments, {daily_edition['total_duration']//3600}h {(daily_edition['total_duration']%3600)//60}m")
            return True
            
        except Exception as e:
            logging.error(f"Error saving daily edition for {daily_edition.get('date')}: {e}")
            db.session.rollback()
            return False
    
    def update_abc_news_area(self) -> Dict:
        """Update ABC News area with latest authentic content from Archive.org"""
        try:
            logging.info("Updating ABC News area with Archive.org content")
            
            # Sync recent content from Archive.org (last 30 days)
            archive_results = self.archive_org.sync_recent_content(days_back=30)
            
            # Also backfill any missing 2024-2025 content
            backfill_results = self.backfill_authentic_daily_content(2024, 2025)
            
            # Get total count of ABC News content
            total_content = ContentSource.query.filter_by(name='ABC News').count()
            
            results = {
                'recent_sync': archive_results,
                'backfill': backfill_results,
                'total_in_database': total_content,
                'source': 'archive_org'
            }
            
            logging.info(f"ABC News area update completed: {total_content} total items in database")
            return results
            
        except Exception as e:
            logging.error(f"Error updating ABC News area: {e}")
            return {'error': str(e)}
    
    def backfill_authentic_daily_content(self, start_year: int = 2024, end_year: int = 2025) -> Dict:
        """Replace fake content with authentic daily editions from Archive.org for 2024-2025"""
        logging.info(f"Starting Archive.org backfill for {start_year}-{end_year}")
        
        # Use Archive.org integration for comprehensive backfill
        archive_results = self.archive_org.backfill_2024_2025_content()
        
        # Convert to expected format
        results = {
            'total_backfilled': archive_results['total_content_created'],
            'years_processed': archive_results['years_processed'],
            'errors': [f"Total errors: {archive_results['total_errors']}"],
            'year_breakdown': archive_results['year_results']
        }
        
        logging.info(f"Archive.org backfill completed: {archive_results['total_content_created']} authentic daily editions")
        return results
    
    def get_abc_news_statistics(self) -> Dict:
        """Get statistics about ABC News content in database"""
        try:
            abc_content = ContentSource.query.filter_by(name='ABC News').all()
            
            stats = {
                'total_videos': len(abc_content),
                'years_covered': set(),
                'categories': {},
                'total_duration': 0,
                'average_duration': 0
            }
            
            for content in abc_content:
                if content.published_date:
                    stats['years_covered'].add(content.published_date.year)
                
                category = content.category or 'General News'
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                
                if content.duration:
                    stats['total_duration'] += content.duration
            
            stats['years_covered'] = sorted(list(stats['years_covered']))
            
            if abc_content:
                stats['average_duration'] = stats['total_duration'] // len(abc_content)
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting ABC News statistics: {e}")
            return {}