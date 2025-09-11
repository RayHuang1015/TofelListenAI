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
        """Fetch ABC News content for a specific date from Archive.org using advanced search"""
        date_str = target_date.strftime('%Y-%m-%d')
        
        results = {
            'date': target_date.date(),
            'shows_found': [],
            'total_duration': 0,
            'combined_url': None,
            'playlist_urls': [],
            'description': '',
            'error': None
        }
        
        try:
            logging.info(f"Searching Archive.org for ABC News content on {target_date.date()}")
            
            # Use Archive.org advanced search API to find ABC News content for this date
            abc_content = self._search_abc_news_by_date(target_date)
            
            if abc_content:
                # Sort by duration and quality to get the best content
                abc_content = sorted(abc_content, key=lambda x: x.get('duration', 0), reverse=True)
                
                target_duration = 3600  # Target 1 hour minimum
                max_duration = 7200     # Maximum 2 hours
                current_duration = 0
                
                # Aggregate content until we reach 60-120 minutes
                for content_item in abc_content:
                    if current_duration >= max_duration:
                        break
                        
                    duration = content_item.get('duration', 1800)  # Default 30 min
                    
                    # Add this content if it helps us reach the target
                    if current_duration < target_duration or (current_duration + duration) <= max_duration:
                        results['shows_found'].append(content_item)
                        results['playlist_urls'].append(content_item['url'])
                        current_duration += duration
                
                results['total_duration'] = current_duration
                
                if results['shows_found']:
                    # Create combined playlist URL and description
                    results['combined_url'] = self._create_combined_playlist_url(results['shows_found'])
                    results['description'] = self._create_combined_description(results['shows_found'], target_date)
                    
                    logging.info(f"Found {len(results['shows_found'])} ABC News segments for {target_date.date()}, total duration: {current_duration//60} minutes")
                else:
                    logging.warning(f"No suitable ABC News content found for {target_date.date()}")
            else:
                logging.warning(f"No ABC News content found in Archive.org for {target_date.date()}")
                
        except Exception as e:
            error_msg = f"Error fetching Archive.org content for {target_date.date()}: {e}"
            logging.error(error_msg)
            results['error'] = error_msg
            
        return results
    
    def _search_abc_news_by_date(self, target_date: datetime) -> List[Dict]:
        """Search for ABC News content on Archive.org using advanced search API"""
        try:
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Multiple search strategies to find ABC content
            search_queries = [
                f"collection:tv AND ABC AND date:{date_str}",
                f"collection:tv AND \"ABC News\" AND date:{date_str}",
                f"collection:television AND ABC AND date:{date_str}*",
                f"title:ABC AND mediatype:movies AND date:[{date_str} TO {date_str}]",
                f"ABC AND World News AND date:{date_str}",
                f"ABC AND Good Morning America AND date:{date_str}"
            ]
            
            all_content = []
            
            for query in search_queries:
                try:
                    content = self._execute_archive_search(query, target_date)
                    if content:
                        all_content.extend(content)
                        
                    # Rate limiting between searches
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    logging.warning(f"Search query failed: {query} - {e}")
                    continue
            
            # Remove duplicates based on identifier
            seen_identifiers = set()
            unique_content = []
            
            for item in all_content:
                identifier = item.get('identifier', '')
                if identifier and identifier not in seen_identifiers:
                    seen_identifiers.add(identifier)
                    unique_content.append(item)
            
            logging.info(f"Found {len(unique_content)} unique ABC News items for {target_date.date()}")
            return unique_content
            
        except Exception as e:
            logging.error(f"Error searching ABC News for {target_date.date()}: {e}")
            return []
    
    def _execute_archive_search(self, query: str, target_date: datetime) -> List[Dict]:
        """Execute a search query against Archive.org advanced search API"""
        try:
            params = {
                'q': query,
                'output': 'json',
                'rows': 50,  # Limit results per query
                'fl': 'identifier,title,description,date,runtime,subject,mediatype',
                'sort[]': 'date desc'
            }
            
            response = requests.get(self.search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                
                content_items = []
                for doc in docs:
                    identifier = doc.get('identifier', '')
                    if not identifier:
                        continue
                    
                    # Get detailed metadata for this item
                    metadata = self._get_archive_metadata(identifier)
                    
                    # Filter for video/audio content with reasonable duration
                    runtime = metadata.get('duration', 0)
                    if runtime > 300:  # At least 5 minutes
                        content_item = {
                            'identifier': identifier,
                            'url': f"https://archive.org/details/{identifier}",
                            'title': doc.get('title', metadata.get('title', '')),
                            'description': doc.get('description', metadata.get('description', '')),
                            'duration': runtime,
                            'date': doc.get('date', ''),
                            'subject': doc.get('subject', []),
                            'quality_score': self._calculate_content_quality(doc, metadata)
                        }
                        content_items.append(content_item)
                
                logging.info(f"Archive search '{query}' returned {len(content_items)} items")
                return content_items
            else:
                logging.warning(f"Archive.org search failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error executing archive search: {e}")
            return []
    
    def _calculate_content_quality(self, doc: Dict, metadata: Dict) -> int:
        """Calculate a quality score for content to prioritize better items"""
        score = 0
        
        title = doc.get('title', '').lower()
        duration = metadata.get('duration', 0)
        
        # Prefer ABC content
        if 'abc' in title:
            score += 10
        if 'world news' in title:
            score += 8
        if 'good morning america' in title:
            score += 6
        
        # Prefer reasonable durations (15-60 minutes)
        if 900 <= duration <= 3600:
            score += 5
        elif 600 <= duration <= 900:
            score += 3
        
        # Prefer items with good metadata
        if metadata.get('description'):
            score += 2
        if metadata.get('subject'):
            score += 1
            
        return score
    
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
    
    def _create_combined_playlist_url(self, shows: List[Dict]) -> str:
        """Create a combined playlist URL for multiple Archive.org items"""
        try:
            if not shows:
                return ""
            
            # Create a custom playlist URL using Archive.org's playlist feature
            identifiers = [show.get('identifier', '') for show in shows if show.get('identifier')]
            
            if len(identifiers) == 1:
                return f"https://archive.org/details/{identifiers[0]}"
            elif len(identifiers) > 1:
                # Create a multi-item playlist URL
                playlist_param = ",".join(identifiers)
                return f"https://archive.org/embed/{identifiers[0]}?playlist={playlist_param}"
            else:
                # Fallback to first show URL
                return shows[0].get('url', '')
                
        except Exception as e:
            logging.error(f"Error creating combined playlist URL: {e}")
            return shows[0].get('url', '') if shows else ""
    
    def _create_combined_description(self, shows: List[Dict], target_date: datetime) -> str:
        """Create description for combined ABC News content"""
        date_str = target_date.strftime('%B %d, %Y')
        
        # Extract show titles instead of show names
        show_titles = []
        for show in shows:
            title = show.get('title', '')
            if title:
                # Clean up title
                clean_title = title.replace('ABC News:', '').replace('ABC', '').strip()
                if len(clean_title) > 50:
                    clean_title = clean_title[:47] + '...'
                show_titles.append(clean_title)
        
        total_duration_seconds = sum(show.get('duration', 1800) for show in shows)
        total_duration_hours = total_duration_seconds // 3600
        total_duration_minutes = (total_duration_seconds % 3600) // 60
        
        if total_duration_hours > 0:
            duration_str = f"{total_duration_hours}h {total_duration_minutes}m"
        else:
            duration_str = f"{total_duration_minutes}m"
        
        description = f"ABC News Complete Coverage - {date_str}"
        description += f" | {len(shows)} authentic segments, {duration_str}"
        
        if show_titles:
            # Add first 2-3 show titles as preview
            preview_titles = show_titles[:3]
            description += f" | Includes: {', '.join(preview_titles)}"
            if len(show_titles) > 3:
                description += f" and {len(show_titles) - 3} more"
        
        return description
    
    def save_abc_news_to_database(self, news_data: Dict) -> bool:
        """Save ABC News content from Archive.org to database with upsert logic"""
        try:
            target_date = news_data['date']
            
            # Check if content for this date already exists
            existing = ContentSource.query.filter(
                ContentSource.name == 'ABC News',
                db.func.date(ContentSource.published_date) == target_date
            ).first()
            
            # Skip if we already have authentic Archive.org content for this date
            if existing:
                try:
                    if existing.content_metadata:
                        metadata = json.loads(existing.content_metadata) if isinstance(existing.content_metadata, str) else existing.content_metadata
                        if metadata.get('source') == 'archive_org' and metadata.get('authentic_date_content'):
                            logging.info(f"Authentic ABC News content for {target_date} already exists, skipping")
                            return False
                except:
                    pass
                
                # Remove existing placeholder or YouTube content
                logging.info(f"Replacing existing content for {target_date} with Archive.org content")
                db.session.delete(existing)
            
            # Only save if we have meaningful content
            if not news_data['shows_found'] or news_data['total_duration'] < 600:  # At least 10 minutes
                logging.warning(f"Insufficient content for {target_date}: {news_data['total_duration']} seconds")
                return False
            
            # Create enhanced content metadata with playlist information
            content_metadata = {
                'source': 'archive_org',
                'authentic_date_content': True,
                'date': str(target_date),
                'total_duration': news_data['total_duration'],
                'show_count': len(news_data['shows_found']),
                'shows': news_data['shows_found'],
                'combined_content': True,
                'playlist_urls': news_data.get('playlist_urls', []),
                'archive_org_urls': [show['url'] for show in news_data['shows_found']],
                'archive_identifiers': [show.get('identifier', '') for show in news_data['shows_found']],
                'playlist_url': news_data['combined_url'],
                'content_quality': {
                    'total_segments': len(news_data['shows_found']),
                    'duration_minutes': news_data['total_duration'] // 60,
                    'has_playlist': len(news_data['shows_found']) > 1
                },
                'fetched_at': datetime.now().isoformat()
            }
            
            # Create ContentSource entry with enhanced information
            content = ContentSource(
                name='ABC News',
                type='news',
                url=news_data['combined_url'],
                description=news_data['description'],
                category='Daily News Coverage',
                difficulty_level='intermediate',
                duration=news_data['total_duration'],
                topic=f"ABC News {target_date.strftime('%B %Y')}",
                published_date=datetime.combine(target_date, datetime.min.time()),
                content_metadata=json.dumps(content_metadata, ensure_ascii=False, default=str)
            )
            
            db.session.add(content)
            db.session.commit()
            
            duration_minutes = news_data['total_duration'] // 60
            logging.info(f"✓ Saved authentic ABC News content for {target_date}: {len(news_data['shows_found'])} segments, {duration_minutes} minutes")
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