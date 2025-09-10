import os
import json
import logging
from datetime import datetime
from typing import List, Dict
from app import db
from models import ContentSource, Question
from services.youtube_content_fetcher import YouTubeContentFetcher
from services.ai_question_generator import AIQuestionGenerator

class ABCNewsIntegration:
    """Service for integrating ABC News Live content from YouTube"""
    
    def __init__(self):
        self.youtube_fetcher = YouTubeContentFetcher()
        self.question_generator = AIQuestionGenerator()
        
    def sync_abc_news_content(self, start_year: int = 2019, end_year: int = 2025) -> Dict:
        """Sync ABC News Live content from YouTube for specified year range"""
        results = {
            'total_fetched': 0,
            'total_saved': 0,
            'years_processed': [],
            'errors': []
        }
        
        try:
            for year in range(start_year, min(end_year + 1, datetime.now().year + 1)):
                logging.info(f"Processing ABC News content for year {year}")
                
                # Fetch videos for this year
                year_videos = self.youtube_fetcher.fetch_abc_news_content_by_year(year)
                results['total_fetched'] += len(year_videos)
                
                # Process and save videos
                saved_count = self._save_videos_to_database(year_videos)
                results['total_saved'] += saved_count
                results['years_processed'].append(year)
                
                logging.info(f"Year {year}: Fetched {len(year_videos)} videos, saved {saved_count}")
                
        except Exception as e:
            error_msg = f"Error during ABC News sync: {e}"
            logging.error(error_msg)
            results['errors'].append(error_msg)
        
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
    
    def update_abc_news_area(self) -> Dict:
        """Update ABC News area with latest content"""
        try:
            # Get current date
            current_date = datetime.now()
            
            # Sync content from 2019 to current year
            results = self.sync_abc_news_content(2019, current_date.year)
            
            # Get total count of ABC News content
            total_content = ContentSource.query.filter_by(name='ABC News').count()
            
            results['total_in_database'] = total_content
            
            return results
            
        except Exception as e:
            logging.error(f"Error updating ABC News area: {e}")
            return {'error': str(e)}
    
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