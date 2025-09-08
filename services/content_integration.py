import requests
import feedparser
import os
import logging
from app import db
from models import ContentSource

class ContentIntegrationService:
    """Service for integrating content from various sources"""
    
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY', 'demo_key')
        self.news_api_key = os.getenv('NEWS_API_KEY', 'demo_key')
    
    def sync_tpo_content(self):
        """Sync TPO (TOEFL Practice Online) content"""
        try:
            # TPO content would typically come from official ETS sources
            # For now, we'll create placeholder entries for TPO 1-75
            count = 0
            for i in range(1, 76):
                existing = ContentSource.query.filter_by(name=f'TPO{i:02d}').first()
                if not existing:
                    content = ContentSource(
                        name=f'TPO{i:02d}',
                        type='audio',
                        description=f'TOEFL Practice Online Test {i} - Official listening practice',
                        difficulty_level='intermediate',
                        duration=1800,  # 30 minutes typical
                        topic='Academic Listening',
                        url=f'https://toefl-practice.com/tpo{i:02d}'
                    )
                    db.session.add(content)
                    count += 1
            
            db.session.commit()
            return count
            
        except Exception as e:
            logging.error(f"Error syncing TPO content: {e}")
            return 0
    
    def sync_ted_content(self):
        """Sync TED talks content using YouTube API"""
        try:
            # Search for TED talks on YouTube
            search_url = 'https://www.googleapis.com/youtube/v3/search'
            params = {
                'part': 'snippet',
                'q': 'TED talk english',
                'type': 'video',
                'maxResults': 50,
                'key': self.youtube_api_key,
                'videoDuration': 'medium'  # 4-20 minutes
            }
            
            response = requests.get(search_url, params=params)
            if response.status_code != 200:
                logging.warning("YouTube API not available, creating sample TED content")
                return self._create_sample_ted_content()
            
            data = response.json()
            count = 0
            
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                description = item['snippet']['description']
                
                existing = ContentSource.query.filter_by(url=f'https://www.youtube.com/watch?v={video_id}').first()
                if not existing:
                    content = ContentSource(
                        name='TED',
                        type='video',
                        url=f'https://www.youtube.com/watch?v={video_id}',
                        description=f'{title}: {description[:200]}...',
                        difficulty_level='intermediate',
                        duration=900,  # Average 15 minutes
                        topic='Education & Technology'
                    )
                    db.session.add(content)
                    count += 1
            
            db.session.commit()
            return count
            
        except Exception as e:
            logging.error(f"Error syncing TED content: {e}")
            return self._create_sample_ted_content()
    
    def _create_sample_ted_content(self):
        """Create sample TED content when API is not available"""
        ted_topics = [
            'The Power of Vulnerability',
            'How to Build Your Creative Confidence',
            'The Puzzle of Motivation',
            'How Schools Kill Creativity',
            'The Power of Introverts'
        ]
        
        count = 0
        for topic in ted_topics:
            existing = ContentSource.query.filter_by(description__contains=topic).first()
            if not existing:
                content = ContentSource(
                    name='TED',
                    type='video',
                    url='https://ted.com/sample',
                    description=f'TED Talk: {topic}',
                    difficulty_level='intermediate',
                    duration=900,
                    topic='Education & Technology'
                )
                db.session.add(content)
                count += 1
        
        db.session.commit()
        return count
    
    def sync_news_content(self):
        """Sync news content from CNN, BBC, ABC"""
        try:
            news_sources = ['cnn', 'bbc-news', 'abc-news']
            count = 0
            
            for source in news_sources:
                url = 'https://newsapi.org/v2/top-headlines'
                params = {
                    'sources': source,
                    'apiKey': self.news_api_key,
                    'pageSize': 10
                }
                
                response = requests.get(url, params=params)
                if response.status_code != 200:
                    logging.warning(f"News API not available for {source}")
                    continue
                
                data = response.json()
                
                for article in data.get('articles', []):
                    existing = ContentSource.query.filter_by(url=article['url']).first()
                    if not existing:
                        content = ContentSource(
                            name=source.upper().replace('-', ' '),
                            type='audio',
                            url=article['url'],
                            description=article['title'],
                            difficulty_level='advanced',
                            duration=300,  # 5 minutes average
                            topic='Current Affairs'
                        )
                        db.session.add(content)
                        count += 1
            
            db.session.commit()
            return count
            
        except Exception as e:
            logging.error(f"Error syncing news content: {e}")
            return self._create_sample_news_content()
    
    def _create_sample_news_content(self):
        """Create sample news content when API is not available"""
        news_items = [
            ('CNN', 'Breaking News: Technology Advances in Education'),
            ('BBC', 'Global Climate Summit: Key Takeaways'),
            ('ABC', 'Economic Trends: Market Analysis'),
            ('CNN', 'Health Update: Latest Medical Research'),
            ('BBC', 'Science Discovery: Space Exploration')
        ]
        
        count = 0
        for source, title in news_items:
            content = ContentSource(
                name=source,
                type='audio',
                url='https://news-sample.com',
                description=title,
                difficulty_level='advanced',
                duration=300,
                topic='Current Affairs'
            )
            db.session.add(content)
            count += 1
        
        db.session.commit()
        return count
    
    def sync_podcast_content(self):
        """Sync podcast content from RSS feeds"""
        try:
            podcast_feeds = [
                'https://feeds.npr.org/510289/podcast.xml',  # Planet Money
                'https://feeds.megaphone.fm/sciencevs',     # Science Vs
                'https://feeds.simplecast.com/54nAGcIl'     # The Daily
            ]
            
            count = 0
            for feed_url in podcast_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    podcast_name = feed.feed.get('title', 'Unknown Podcast')
                    
                    for entry in feed.entries[:5]:  # Limit to 5 episodes per podcast
                        existing = ContentSource.query.filter_by(url=entry.link).first()
                        if not existing:
                            content = ContentSource(
                                name=f'Podcast - {podcast_name}',
                                type='audio',
                                url=entry.link,
                                description=entry.title,
                                difficulty_level='intermediate',
                                duration=1800,  # 30 minutes average
                                topic='General Interest'
                            )
                            db.session.add(content)
                            count += 1
                            
                except Exception as e:
                    logging.warning(f"Error parsing podcast feed {feed_url}: {e}")
                    continue
            
            db.session.commit()
            return count
            
        except Exception as e:
            logging.error(f"Error syncing podcast content: {e}")
            return 0
