import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

class YouTubeContentFetcher:
    """Service for fetching ABC News Live content from YouTube"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable not set")
        
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.abc_news_channel_id = "UCBi2mrWuNuyYy4gbM6fU18Q"  # ABC News official channel
        
    def search_abc_news_live_videos(self, start_date: datetime, end_date: datetime, max_results: int = 50) -> List[Dict]:
        """Search for ABC News Live videos within a date range"""
        try:
            # Format dates for YouTube API
            published_after = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            published_before = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Search for ABC News Live videos
            search_url = f"{self.base_url}/search"
            search_params = {
                'part': 'snippet',
                'channelId': self.abc_news_channel_id,
                'q': 'ABC News Live',
                'type': 'video',
                'order': 'date',
                'publishedAfter': published_after,
                'publishedBefore': published_before,
                'maxResults': max_results,
                'key': self.api_key
            }
            
            search_response = requests.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if 'items' not in search_data:
                logging.warning("No video items found in search response")
                return []
            
            video_ids = [item['id']['videoId'] for item in search_data['items']]
            
            # Get detailed video information
            videos_url = f"{self.base_url}/videos"
            videos_params = {
                'part': 'snippet,contentDetails,statistics',
                'id': ','.join(video_ids),
                'key': self.api_key
            }
            
            videos_response = requests.get(videos_url, params=videos_params)
            videos_response.raise_for_status()
            videos_data = videos_response.json()
            
            return self._process_video_data(videos_data.get('items', []))
            
        except requests.RequestException as e:
            logging.error(f"YouTube API request failed: {e}")
            return []
        except Exception as e:
            logging.error(f"Error fetching YouTube content: {e}")
            return []
    
    def _process_video_data(self, video_items: List[Dict]) -> List[Dict]:
        """Process raw video data into structured format"""
        processed_videos = []
        
        for video in video_items:
            try:
                snippet = video.get('snippet', {})
                content_details = video.get('contentDetails', {})
                statistics = video.get('statistics', {})
                
                # Parse duration (PT format like PT1H23M45S)
                duration_str = content_details.get('duration', 'PT0S')
                duration_seconds = self._parse_duration(duration_str)
                
                # Skip videos shorter than 5 minutes (likely not full news broadcasts)
                if duration_seconds < 300:
                    continue
                
                # Determine category based on title and description
                title = snippet.get('title', '').lower()
                description = snippet.get('description', '').lower()
                category = self._determine_category(title, description)
                
                processed_video = {
                    'video_id': video['id'],
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'published_date': datetime.fromisoformat(snippet.get('publishedAt', '').replace('Z', '+00:00')),
                    'duration': duration_seconds,
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'video_url': f"https://www.youtube.com/watch?v={video['id']}",
                    'view_count': int(statistics.get('viewCount', 0)),
                    'category': category,
                    'channel_title': snippet.get('channelTitle', 'ABC News'),
                    'tags': snippet.get('tags', [])
                }
                
                processed_videos.append(processed_video)
                
            except Exception as e:
                logging.error(f"Error processing video {video.get('id', 'unknown')}: {e}")
                continue
        
        return processed_videos
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse YouTube duration format (PT1H23M45S) to seconds"""
        try:
            import re
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_str)
            
            if not match:
                return 0
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception:
            return 0
    
    def _determine_category(self, title: str, description: str) -> str:
        """Determine news category based on title and description"""
        text = f"{title} {description}".lower()
        
        # Define category keywords
        categories = {
            'Politics': ['election', 'president', 'congress', 'politics', 'government', 'senate', 'house', 'campaign', 'vote', 'democracy'],
            'International': ['ukraine', 'russia', 'china', 'europe', 'middle east', 'international', 'world', 'global', 'foreign', 'war'],
            'Health': ['covid', 'pandemic', 'health', 'medical', 'vaccine', 'virus', 'disease', 'hospital', 'doctor', 'cdc'],
            'Technology': ['tech', 'technology', 'ai', 'artificial intelligence', 'cyber', 'digital', 'internet', 'social media', 'data'],
            'Economy': ['economy', 'economic', 'market', 'stock', 'inflation', 'jobs', 'unemployment', 'business', 'finance', 'trade'],
            'Environment': ['climate', 'weather', 'environment', 'hurricane', 'wildfire', 'flood', 'storm', 'global warming', 'carbon'],
            'Crime': ['crime', 'police', 'shooting', 'murder', 'arrest', 'investigation', 'court', 'trial', 'verdict', 'justice'],
            'Entertainment': ['celebrity', 'entertainment', 'movie', 'music', 'sports', 'game', 'award', 'festival']
        }
        
        # Check for category keywords
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'General News'
    
    def fetch_abc_news_content_by_year(self, year: int, max_videos_per_month: int = 20) -> List[Dict]:
        """Fetch ABC News Live content for a specific year"""
        all_videos = []
        
        # Fetch content month by month for better results
        for month in range(1, 13):
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            # Don't fetch future dates
            if start_date > datetime.now():
                break
            
            logging.info(f"Fetching ABC News content for {year}-{month:02d}")
            
            month_videos = self.search_abc_news_live_videos(
                start_date, 
                end_date, 
                max_videos_per_month
            )
            
            all_videos.extend(month_videos)
            
            # Small delay to respect API rate limits
            import time
            time.sleep(0.1)
        
        return all_videos
    
    def get_video_transcript_placeholder(self, video_data: Dict) -> str:
        """Generate a placeholder transcript based on video metadata"""
        title = video_data.get('title', '')
        description = video_data.get('description', '')
        category = video_data.get('category', 'General News')
        
        # Create a realistic news transcript placeholder
        transcript = f"""Good evening, I'm reporting live for ABC News. Tonight's top story focuses on {category.lower()} developments.

{title}

{description[:500] if description else 'Breaking news developments continue to unfold as our team brings you the latest updates on this developing story.'}

Our correspondents are standing by with live reports from the field. We'll continue to monitor this situation and bring you updates as they become available.

This has been ABC News Live coverage. Thank you for joining us tonight."""
        
        return transcript[:1000]  # Limit length for TTS performance