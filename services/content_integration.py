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
            # Create TPO tests with various academic topics
            tpo_topics = [
                'Biology & Life Sciences', 'Physics & Astronomy', 'Environmental Science',
                'History & Archaeology', 'Psychology & Social Science', 'Business & Economics',
                'Arts & Literature', 'Technology & Innovation', 'Medicine & Health',
                'Engineering & Technology', 'Education & Learning', 'Political Science',
                'Linguistics & Languages', 'Anthropology & Cultural Studies', 'Geography & Earth Sciences'
            ]
            
            for i in range(1, 76):
                existing = ContentSource.query.filter_by(name=f'TPO{i:02d}').first()
                if not existing:
                    # Assign topic cyclically to ensure variety
                    topic = tpo_topics[(i - 1) % len(tpo_topics)]
                    
                    # Vary difficulty levels
                    if i <= 25:
                        difficulty = 'beginner'
                    elif i <= 50:
                        difficulty = 'intermediate'
                    else:
                        difficulty = 'advanced'
                        
                    content = ContentSource(
                        name=f'TPO{i:02d}',
                        type='audio',
                        description=f'TOEFL Practice Online Test {i} - Official listening practice',
                        difficulty_level=difficulty,
                        duration=1800,  # 30 minutes typical
                        topic=topic,
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
            ('The Power of Vulnerability', 'Psychology & Social Science'),
            ('How to Build Your Creative Confidence', 'Arts & Literature'),
            ('The Puzzle of Motivation', 'Psychology & Social Science'),
            ('How Schools Kill Creativity', 'Education & Learning'),
            ('The Power of Introverts', 'Psychology & Social Science'),
            ('The Future of AI and Machine Learning', 'Technology & Innovation'),
            ('Climate Change: Solutions for Tomorrow', 'Environmental Science'),
            ('The Economics of Happiness', 'Business & Economics'),
            ('Breakthroughs in Medical Technology', 'Medicine & Health'),
            ('The Universe: What We Still Don\'t Know', 'Physics & Astronomy'),
            ('Ancient Civilizations: Lessons for Today', 'History & Archaeology'),
            ('The Science of Sleep and Dreams', 'Biology & Life Sciences'),
            ('Building Better Cities', 'Engineering & Technology'),
            ('The Evolution of Language', 'Linguistics & Languages'),
            ('Democracy in the Digital Age', 'Political Science')
        ]
        
        count = 0
        for title, topic in ted_topics:
            existing = ContentSource.query.filter(ContentSource.description.contains(title)).first()
            if not existing:
                content = ContentSource(
                    name='TED',
                    type='video',
                    url='https://ted.com/sample',
                    description=f'TED Talk: {title}',
                    difficulty_level='intermediate',
                    duration=900,
                    topic=topic
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
            ('CNN', 'Breaking News: Technology Advances in Education', 'Technology & Innovation'),
            ('BBC', 'Global Climate Summit: Key Takeaways', 'Environmental Science'),
            ('ABC', 'Economic Trends: Market Analysis', 'Business & Economics'),
            ('CNN', 'Health Update: Latest Medical Research', 'Medicine & Health'),
            ('BBC', 'Science Discovery: Space Exploration', 'Physics & Astronomy'),
            ('ABC', 'Archaeological Findings: Ancient Civilizations', 'History & Archaeology'),
            ('CNN', 'Social Psychology: Human Behavior Studies', 'Psychology & Social Science'),
            ('BBC', 'Biodiversity Conservation Efforts', 'Biology & Life Sciences'),
            ('ABC', 'Art Museum Exhibition Opens', 'Arts & Literature'),
            ('CNN', 'International Relations: Diplomatic Updates', 'Political Science'),
            ('BBC', 'Engineering Innovation in Infrastructure', 'Engineering & Technology'),
            ('ABC', 'Language Learning Research', 'Linguistics & Languages')
        ]
        
        count = 0
        for source, title, topic in news_items:
            content = ContentSource(
                name=source,
                type='audio',
                url='https://news-sample.com',
                description=title,
                difficulty_level='advanced',
                duration=300,
                topic=topic
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
            
            # Add sample podcast content with diverse topics
            self._create_sample_podcast_content()
            
            db.session.commit()
            return count
            
        except Exception as e:
            logging.error(f"Error syncing podcast content: {e}")
            return self._create_sample_podcast_content()
    
    def _create_sample_podcast_content(self):
        """Create sample podcast content with diverse topics"""
        podcast_content = [
            ('Science Podcast', 'The Mysteries of Quantum Physics', 'Physics & Astronomy', 'intermediate'),
            ('Health Podcast', 'Understanding Mental Health in Modern Society', 'Psychology & Social Science', 'intermediate'),
            ('Tech Talk', 'Artificial Intelligence and the Future of Work', 'Technology & Innovation', 'advanced'),
            ('History Show', 'Ancient Rome: Politics and Power', 'History & Archaeology', 'intermediate'),
            ('Nature Podcast', 'Climate Change and Biodiversity', 'Environmental Science', 'advanced'),
            ('Medical Series', 'Breakthroughs in Cancer Research', 'Medicine & Health', 'advanced'),
            ('Business Hour', 'Entrepreneurship in the Digital Age', 'Business & Economics', 'intermediate'),
            ('Art & Culture', 'Renaissance Art: Innovation and Influence', 'Arts & Literature', 'intermediate'),
            ('Language Learning', 'The Evolution of English Language', 'Linguistics & Languages', 'intermediate'),
            ('Engineering Talk', 'Sustainable Architecture and Design', 'Engineering & Technology', 'advanced')
        ]
        
        count = 0
        for podcast_name, episode_title, topic, difficulty in podcast_content:
            existing = ContentSource.query.filter(
                ContentSource.name == f'Podcast - {podcast_name}',
                ContentSource.description == episode_title
            ).first()
            if not existing:
                content = ContentSource(
                    name=f'Podcast - {podcast_name}',
                    type='audio',
                    url='https://podcast-sample.com',
                    description=episode_title,
                    difficulty_level=difficulty,
                    duration=1800,
                    topic=topic
                )
                db.session.add(content)
                count += 1
        
        return count
    
    def sync_discovery_content(self):
        """Sync Discovery Channel content"""
        try:
            discovery_content = [
                ('How the Universe Works', 'Physics & Astronomy', 'advanced'),
                ('Planet Earth: Wildlife Adventures', 'Biology & Life Sciences', 'intermediate'),
                ('Engineering Marvels of the Ancient World', 'Engineering & Technology', 'advanced'),
                ('The Science of Natural Disasters', 'Geography & Earth Sciences', 'intermediate'),
                ('Ocean Mysteries: Deep Sea Exploration', 'Environmental Science', 'intermediate'),
                ('Medical Breakthroughs: Saving Lives', 'Medicine & Health', 'advanced'),
                ('Technology Revolution: Changing the World', 'Technology & Innovation', 'advanced'),
                ('Archaeological Discoveries: Lost Civilizations', 'History & Archaeology', 'intermediate'),
                ('The Human Mind: Psychology Explained', 'Psychology & Social Science', 'intermediate'),
                ('Extreme Engineering: Building the Future', 'Engineering & Technology', 'advanced')
            ]
            
            count = 0
            for title, topic, difficulty in discovery_content:
                existing = ContentSource.query.filter_by(
                    name='Discovery',
                    description=title
                ).first()
                if not existing:
                    content = ContentSource(
                        name='Discovery',
                        type='video',
                        url='https://discovery-sample.com',
                        description=title,
                        difficulty_level=difficulty,
                        duration=2700,  # 45 minutes typical
                        topic=topic
                    )
                    db.session.add(content)
                    count += 1
            
            db.session.commit()
            return count
            
        except Exception as e:
            logging.error(f"Error syncing Discovery content: {e}")
            return 0
    
    def sync_national_geographic_content(self):
        """Sync National Geographic content"""
        try:
            natgeo_content = [
                ('Wildlife of Africa: Lion Kingdoms', 'Biology & Life Sciences', 'intermediate'),
                ('Ancient Civilizations: Maya Secrets', 'History & Archaeology', 'intermediate'),
                ('Climate Change: Polar Ice Melting', 'Environmental Science', 'advanced'),
                ('Ocean Exploration: Mariana Trench', 'Geography & Earth Sciences', 'advanced'),
                ('Space Exploration: Mars Mission', 'Physics & Astronomy', 'advanced'),
                ('Human Evolution: Our Ancient Ancestors', 'Anthropology & Cultural Studies', 'intermediate'),
                ('Natural Disasters: Earthquake Science', 'Geography & Earth Sciences', 'intermediate'),
                ('Conservation Heroes: Saving Species', 'Environmental Science', 'intermediate'),
                ('Lost Cities: Archaeological Wonders', 'History & Archaeology', 'intermediate'),
                ('The Science of Survival: Human Adaptation', 'Biology & Life Sciences', 'intermediate')
            ]
            
            count = 0
            for title, topic, difficulty in natgeo_content:
                existing = ContentSource.query.filter_by(
                    name='National Geographic',
                    description=title
                ).first()
                if not existing:
                    content = ContentSource(
                        name='National Geographic',
                        type='video',
                        url='https://nationalgeographic-sample.com',
                        description=title,
                        difficulty_level=difficulty,
                        duration=3000,  # 50 minutes typical
                        topic=topic
                    )
                    db.session.add(content)
                    count += 1
            
            db.session.commit()
            return count
            
        except Exception as e:
            logging.error(f"Error syncing National Geographic content: {e}")
            return 0
