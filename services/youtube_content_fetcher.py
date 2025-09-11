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
    
    def search_abc_daily_news_videos(self, target_date: datetime, max_results: int = 20) -> Dict:
        """Search for ABC News daily videos for a specific date and create composite playlist"""
        try:
            # Search for videos published on the target date (24-hour window)
            start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59)
            
            published_after = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            published_before = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Multiple searches for different types of daily content
            search_queries = [
                'World News Tonight', 
                'ABC News Prime',
                'Good Morning America',
                'breaking news',
                'full episode'
            ]
            
            all_videos = []
            
            for query in search_queries:
                search_url = f"{self.base_url}/search"
                search_params = {
                    'part': 'snippet',
                    'channelId': self.abc_news_channel_id,
                    'q': query,
                    'type': 'video',
                    'order': 'relevance',
                    'publishedAfter': published_after,
                    'publishedBefore': published_before,
                    'maxResults': 10,
                    'key': self.api_key
                }
                
                search_response = requests.get(search_url, params=search_params)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                if 'items' in search_data:
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
                    
                    query_videos = self._process_video_data(videos_data.get('items', []))
                    all_videos.extend(query_videos)
                
                # Small delay between searches
                import time
                time.sleep(0.1)
            
            # Remove duplicates and sort by duration (longest first)
            unique_videos = {}
            for video in all_videos:
                video_id = video['video_id']
                if video_id not in unique_videos or video['duration'] > unique_videos[video_id]['duration']:
                    unique_videos[video_id] = video
            
            sorted_videos = sorted(unique_videos.values(), key=lambda x: x['duration'], reverse=True)
            
            # Create composite playlist to reach 1-2 hours (3600-7200 seconds)
            return self._create_daily_composite_playlist(sorted_videos, target_date)
            
        except Exception as e:
            logging.error(f"Error searching daily ABC News for {target_date.date()}: {e}")
            return self._create_empty_daily_playlist(target_date)
    
    def _create_daily_composite_playlist(self, videos: List[Dict], target_date: datetime) -> Dict:
        """Create a composite playlist from videos to reach 1-2 hour target duration"""
        target_min = 3600  # 1 hour minimum
        target_max = 7200  # 2 hours maximum
        
        selected_videos = []
        total_duration = 0
        
        # First, try to find one long video that meets the requirement
        for video in videos:
            if target_min <= video['duration'] <= target_max:
                selected_videos = [video]
                total_duration = video['duration']
                break
        
        # If no single video meets requirement, combine multiple videos
        if not selected_videos:
            for video in videos:
                if total_duration + video['duration'] <= target_max:
                    selected_videos.append(video)
                    total_duration += video['duration']
                    
                    if total_duration >= target_min:
                        break
        
        # If still no videos, take the longest available ones
        if not selected_videos and videos:
            selected_videos = videos[:3]  # Take top 3 longest videos
            total_duration = sum(v['duration'] for v in selected_videos)
        
        return {
            'date': target_date.date(),
            'total_duration': total_duration,
            'video_count': len(selected_videos),
            'videos': selected_videos,
            'composite': True,
            'title': f'ABC News Daily Edition - {target_date.strftime("%B %d, %Y")}',
            'description': f'Compiled ABC News content from {target_date.strftime("%B %d, %Y")} ({len(selected_videos)} segments, {total_duration//3600}h {(total_duration%3600)//60}m)',
            'playlist_url': self._generate_playlist_url(selected_videos) if selected_videos else None
        }
    
    def _create_empty_daily_playlist(self, target_date: datetime) -> Dict:
        """Create empty playlist when no videos found"""
        return {
            'date': target_date.date(),
            'total_duration': 0,
            'video_count': 0,
            'videos': [],
            'composite': True,
            'title': f'ABC News Daily Edition - {target_date.strftime("%B %d, %Y")} (No Content)',
            'description': f'No ABC News content available for {target_date.strftime("%B %d, %Y")}',
            'playlist_url': None
        }
    
    def _generate_playlist_url(self, videos: List[Dict]) -> str:
        """Generate YouTube playlist URL for multiple videos"""
        if not videos:
            return None
        
        # Use first video as main video, add others as playlist
        main_video_id = videos[0]['video_id']
        
        if len(videos) == 1:
            return f"https://www.youtube.com/watch?v={main_video_id}"
        
        # Create playlist parameter with video IDs
        video_ids = [v['video_id'] for v in videos]
        playlist_param = ','.join(video_ids)
        
        return f"https://www.youtube.com/watch?v={main_video_id}&list={playlist_param}"

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
    
    def fetch_daily_editions_for_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch daily editions for a range of dates"""
        daily_editions = []
        current_date = start_date
        
        while current_date <= end_date:
            logging.info(f"Fetching daily edition for {current_date.date()}")
            
            daily_edition = self.search_abc_daily_news_videos(current_date)
            if daily_edition['video_count'] > 0:
                daily_editions.append(daily_edition)
            
            current_date += timedelta(days=1)
            
            # Rate limiting
            import time
            time.sleep(0.2)
        
        return daily_editions
    
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