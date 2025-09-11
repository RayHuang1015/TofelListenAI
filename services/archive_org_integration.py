import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app import db
from models import ContentSource

class ArchiveOrgIntegration:
    """Service for integrating ABC News content from Archive.org TV News Archive"""
    
    def __init__(self):
        self.base_url = "https://archive.org"
        self.search_url = "https://archive.org/advancedsearch.php"
        
        # ABC News shows for combining into 1-2 hour content
        self.abc_shows = [
            "ABC_World_News_Tonight_With_David_Muir",
            "ABC_News_Prime",
            "Good_Morning_America"
        ]
        
        # KGO is ABC's San Francisco affiliate with comprehensive coverage
        self.station_code = "KGO"
        
    def fetch_abc_news_for_date(self, target_date: datetime) -> Dict:
        """Fetch ABC News content for a specific date from Archive.org"""
        date_str = target_date.strftime('%Y%m%d')
        
        results = {
            'date': target_date.date(),
            'shows_found': [],
            'total_duration': 0,
            'combined_url': None,
            'description': '',
            'error': None
        }
        
        try:
            # Search for ABC shows on this date
            for show_name in self.abc_shows:
                show_data = self._search_archive_show(show_name, target_date)
                if show_data:
                    results['shows_found'].append(show_data)
                    results['total_duration'] += show_data.get('duration', 1800)  # Default 30 min
            
            if results['shows_found']:
                # Create combined content description
                results['description'] = self._create_combined_description(results['shows_found'], target_date)
                results['combined_url'] = results['shows_found'][0]['url']  # Use first show as main URL
                
                logging.info(f"Found {len(results['shows_found'])} ABC shows for {target_date.date()}")
            else:
                logging.warning(f"No ABC News content found for {target_date.date()}")
                
        except Exception as e:
            error_msg = f"Error fetching Archive.org content for {target_date.date()}: {e}"
            logging.error(error_msg)
            results['error'] = error_msg
            
        return results
    
    def _search_archive_show(self, show_name: str, target_date: datetime) -> Optional[Dict]:
        """Search for a specific ABC show on Archive.org for given date"""
        try:
            date_str = target_date.strftime('%Y%m%d')
            
            # Try multiple time slots for the show
            time_slots = ['223000', '003000', '013000', '233000']  # Common ABC news times
            
            for time_slot in time_slots:
                # Construct Archive.org URL pattern
                identifier = f"{self.station_code}_{date_str}_{time_slot}_{show_name}"
                archive_url = f"https://archive.org/details/{identifier}"
                
                # Check if this URL exists
                if self._check_archive_url_exists(archive_url):
                    # Get metadata for this show
                    metadata = self._get_archive_metadata(identifier)
                    
                    return {
                        'show_name': show_name,
                        'url': archive_url,
                        'identifier': identifier,
                        'duration': metadata.get('duration', 1800),
                        'title': metadata.get('title', f"{show_name.replace('_', ' ')} - {target_date.strftime('%B %d, %Y')}"),
                        'description': metadata.get('description', ''),
                        'time_slot': time_slot
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Error searching for {show_name} on {target_date.date()}: {e}")
            return None
    
    def _check_archive_url_exists(self, url: str) -> bool:
        """Check if an Archive.org URL exists"""
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _get_archive_metadata(self, identifier: str) -> Dict:
        """Get metadata for an Archive.org item"""
        try:
            metadata_url = f"https://archive.org/metadata/{identifier}"
            response = requests.get(metadata_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                metadata = data.get('metadata', {})
                
                # Extract useful information
                return {
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'duration': self._parse_duration(metadata.get('runtime', '0:30:00')),
                    'date': metadata.get('date', ''),
                    'subject': metadata.get('subject', [])
                }
            
            return {}
            
        except Exception as e:
            logging.error(f"Error getting metadata for {identifier}: {e}")
            return {}
    
    def _parse_duration(self, runtime_str: str) -> int:
        """Parse duration string to seconds"""
        try:
            if ':' in runtime_str:
                parts = runtime_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(int, parts)
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:  # MM:SS
                    minutes, seconds = map(int, parts)
                    return minutes * 60 + seconds
            
            # Default to 30 minutes if parsing fails
            return 1800
            
        except:
            return 1800
    
    def _create_combined_description(self, shows: List[Dict], target_date: datetime) -> str:
        """Create description for combined ABC News content"""
        date_str = target_date.strftime('%B %d, %Y')
        show_names = [show['show_name'].replace('_', ' ') for show in shows]
        
        total_duration_hours = sum(show.get('duration', 1800) for show in shows) // 3600
        total_duration_minutes = (sum(show.get('duration', 1800) for show in shows) % 3600) // 60
        
        duration_str = f"{total_duration_hours}h {total_duration_minutes}m" if total_duration_hours > 0 else f"{total_duration_minutes + (total_duration_hours * 60)}m"
        
        return f"ABC News Complete Coverage - {date_str} | {len(shows)} authentic segments, {duration_str}"
    
    def save_abc_news_to_database(self, news_data: Dict) -> bool:
        """Save ABC News content from Archive.org to database"""
        try:
            target_date = news_data['date']
            
            # Check if content for this date already exists (and is not live stream)
            existing = ContentSource.query.filter(
                ContentSource.name == 'ABC News',
                db.func.date(ContentSource.published_date) == target_date
            ).first()
            
            if existing and not existing.url.startswith('https://abcnews.go.com/Live'):
                logging.info(f"ABC News content for {target_date} already exists, skipping")
                return False
            
            # Remove existing entry if it's a live stream placeholder
            if existing:
                db.session.delete(existing)
            
            # Create content metadata
            content_metadata = {
                'source': 'archive_org',
                'authentic_date_content': True,
                'date': str(target_date),
                'total_duration': news_data['total_duration'],
                'show_count': len(news_data['shows_found']),
                'shows': news_data['shows_found'],
                'combined_content': True,
                'archive_org_urls': [show['url'] for show in news_data['shows_found']],
                'fetched_at': datetime.now().isoformat()
            }
            
            # Create ContentSource entry
            content = ContentSource(
                name='ABC News',
                type='news',
                url=news_data['combined_url'],
                description=news_data['description'],
                category='Daily News',
                difficulty_level='intermediate',
                duration=news_data['total_duration'],
                topic='ABC News Daily Coverage',
                published_date=datetime.combine(target_date, datetime.min.time()),
                content_metadata=json.dumps(content_metadata, ensure_ascii=False, default=str)
            )
            
            db.session.add(content)
            db.session.commit()
            
            logging.info(f"Saved authentic ABC News content for {target_date}: {len(news_data['shows_found'])} shows")
            return True
            
        except Exception as e:
            logging.error(f"Error saving ABC News content for {news_data.get('date')}: {e}")
            db.session.rollback()
            return False
    
    def sync_date_range(self, start_date: datetime, end_date: datetime) -> Dict:
        """Sync ABC News content for a date range"""
        results = {
            'total_days': 0,
            'successful_days': 0,
            'content_created': 0,
            'errors': []
        }
        
        current_date = start_date
        while current_date <= end_date:
            results['total_days'] += 1
            
            try:
                logging.info(f"Processing ABC News for {current_date.date()}")
                
                # Fetch content for this date
                news_data = self.fetch_abc_news_for_date(current_date)
                
                if news_data['shows_found'] and not news_data['error']:
                    # Save to database
                    if self.save_abc_news_to_database(news_data):
                        results['content_created'] += 1
                        results['successful_days'] += 1
                else:
                    if news_data['error']:
                        results['errors'].append(f"{current_date.date()}: {news_data['error']}")
                    else:
                        results['errors'].append(f"{current_date.date()}: No content found")
                
                # Rate limiting - be nice to Archive.org
                import time
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"{current_date.date()}: {e}"
                results['errors'].append(error_msg)
                logging.error(f"Error processing {current_date.date()}: {e}")
            
            current_date += timedelta(days=1)
        
        return results
    
    def sync_recent_content(self, days_back: int = 30) -> Dict:
        """Sync recent ABC News content from Archive.org"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        return self.sync_date_range(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.min.time())
        )
    
    def backfill_2024_2025_content(self) -> Dict:
        """Backfill authentic ABC News content for 2024-2025"""
        results = {
            'years_processed': [],
            'total_content_created': 0,
            'total_errors': 0,
            'year_results': {}
        }
        
        for year in [2024, 2025]:
            logging.info(f"Backfilling ABC News content for {year}")
            
            # Process year in monthly chunks to avoid overwhelming Archive.org
            year_content = 0
            year_errors = 0
            
            for month in range(1, 13):
                try:
                    start_date = datetime(year, month, 1)
                    
                    # Calculate end date for the month
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                    
                    # Don't process future dates
                    if start_date > datetime.now():
                        break
                    
                    # Ensure we don't go beyond today
                    if end_date > datetime.now():
                        end_date = datetime.now()
                    
                    logging.info(f"Processing {year}-{month:02d}: {start_date.date()} to {end_date.date()}")
                    
                    month_results = self.sync_date_range(start_date, end_date)
                    year_content += month_results['content_created']
                    year_errors += len(month_results['errors'])
                    
                    # Longer delay between months
                    import time
                    time.sleep(2)
                    
                except Exception as e:
                    logging.error(f"Error processing {year}-{month}: {e}")
                    year_errors += 1
            
            results['years_processed'].append(year)
            results['year_results'][year] = {
                'content_created': year_content,
                'errors': year_errors
            }
            results['total_content_created'] += year_content
            results['total_errors'] += year_errors
        
        return results