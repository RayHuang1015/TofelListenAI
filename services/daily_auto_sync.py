import os
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict
from app import app, db
from models import ContentSource
from services.archive_org_integration import ArchiveOrgIntegration

class DailyAutoSync:
    """Service for automatically syncing daily ABC News content"""
    
    def __init__(self):
        self.archive_org = ArchiveOrgIntegration()
        self.is_running = False
        
    def sync_today_news(self) -> Dict:
        """Sync ABC News content for today if it doesn't exist"""
        today = datetime.now().date()
        
        with app.app_context():
            try:
                logging.info(f"Starting daily auto-sync for {today}")
                
                # Check if we already have content for today
                existing = ContentSource.query.filter(
                    ContentSource.name == 'ABC News',
                    db.func.date(ContentSource.published_date) == today
                ).first()
                
                # Skip if we already have authentic Archive.org content for this date
                if existing:
                    try:
                        if existing.content_metadata:
                            import json
                            metadata = json.loads(existing.content_metadata) if isinstance(existing.content_metadata, str) else existing.content_metadata
                            if metadata.get('source') == 'archive_org' and metadata.get('authentic_date_content'):
                                logging.info(f"Authentic ABC News content for {today} already exists, skipping")
                                return {
                                    'status': 'skipped',
                                    'message': f"Authentic content for {today} already exists",
                                    'date': str(today)
                                }
                    except:
                        pass
                
                # Fetch content for today from Archive.org
                today_datetime = datetime.combine(today, datetime.min.time())
                news_data = self.archive_org.fetch_abc_news_for_date(today_datetime)
                
                if news_data['shows_found'] and not news_data['error']:
                    # Save to database
                    saved = self.archive_org.save_abc_news_to_database(news_data)
                    
                    if saved:
                        logging.info(f"Successfully synced ABC News for {today}")
                        return {
                            'status': 'success',
                            'message': f"Synced {len(news_data['shows_found'])} shows for {today}",
                            'date': str(today),
                            'shows_count': len(news_data['shows_found']),
                            'total_duration': news_data['total_duration']
                        }
                    else:
                        logging.warning(f"Failed to save ABC News content for {today}")
                        return {
                            'status': 'error',
                            'message': f"Failed to save content for {today}",
                            'date': str(today)
                        }
                else:
                    error_msg = news_data.get('error', 'No content found')
                    logging.warning(f"No ABC News content found for {today}: {error_msg}")
                    return {
                        'status': 'no_content',
                        'message': f"No content found for {today}: {error_msg}",
                        'date': str(today)
                    }
                    
            except Exception as e:
                logging.error(f"Error during daily auto-sync for {today}: {e}")
                return {
                    'status': 'error',
                    'message': f"Error syncing {today}: {str(e)}",
                    'date': str(today)
                }
    
    def sync_yesterday_news(self) -> Dict:
        """Sync ABC News content for yesterday (more reliable for Archive.org)"""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        with app.app_context():
            try:
                logging.info(f"Starting daily auto-sync for yesterday: {yesterday}")
                
                # Check if we already have content for yesterday
                existing = ContentSource.query.filter(
                    ContentSource.name == 'ABC News',
                    db.func.date(ContentSource.published_date) == yesterday
                ).first()
                
                # Skip if we already have authentic Archive.org content for this date
                if existing:
                    try:
                        if existing.content_metadata:
                            import json
                            metadata = json.loads(existing.content_metadata) if isinstance(existing.content_metadata, str) else existing.content_metadata
                            if metadata.get('source') == 'archive_org' and metadata.get('authentic_date_content'):
                    logging.info(f"ABC News content for {yesterday} already exists, skipping")
                    return {
                        'status': 'skipped',
                        'message': f"Content for {yesterday} already exists",
                        'date': str(yesterday)
                    }
                
                # Fetch content for yesterday from Archive.org
                yesterday_datetime = datetime.combine(yesterday, datetime.min.time())
                news_data = self.archive_org.fetch_abc_news_for_date(yesterday_datetime)
                
                if news_data['shows_found'] and not news_data['error']:
                    # Save to database
                    saved = self.archive_org.save_abc_news_to_database(news_data)
                    
                    if saved:
                        logging.info(f"Successfully synced ABC News for {yesterday}")
                        return {
                            'status': 'success',
                            'message': f"Synced {len(news_data['shows_found'])} shows for {yesterday}",
                            'date': str(yesterday),
                            'shows_count': len(news_data['shows_found']),
                            'total_duration': news_data['total_duration']
                        }
                    else:
                        logging.warning(f"Failed to save ABC News content for {yesterday}")
                        return {
                            'status': 'error',
                            'message': f"Failed to save content for {yesterday}",
                            'date': str(yesterday)
                        }
                else:
                    error_msg = news_data.get('error', 'No content found')
                    logging.warning(f"No ABC News content found for {yesterday}: {error_msg}")
                    return {
                        'status': 'no_content',
                        'message': f"No content found for {yesterday}: {error_msg}",
                        'date': str(yesterday)
                    }
                    
            except Exception as e:
                logging.error(f"Error during daily auto-sync for {yesterday}: {e}")
                return {
                    'status': 'error',
                    'message': f"Error syncing {yesterday}: {str(e)}",
                    'date': str(yesterday)
                }
    
    def sync_recent_missing_days(self, days_back: int = 7) -> Dict:
        """Sync any missing ABC News content for recent days"""
        results = {
            'total_days_checked': 0,
            'days_synced': 0,
            'days_skipped': 0,
            'errors': 0,
            'synced_dates': []
        }
        
        with app.app_context():
            try:
                for i in range(days_back):
                    check_date = (datetime.now() - timedelta(days=i)).date()
                    results['total_days_checked'] += 1
                    
                    # Check if we already have content for this date
                    existing = ContentSource.query.filter(
                        ContentSource.name == 'ABC News',
                        db.func.date(ContentSource.published_date) == check_date
                    ).first()
                    
                    # Skip if we already have authentic Archive.org content for this date
                if existing:
                    try:
                        if existing.content_metadata:
                            import json
                            metadata = json.loads(existing.content_metadata) if isinstance(existing.content_metadata, str) else existing.content_metadata
                            if metadata.get('source') == 'archive_org' and metadata.get('authentic_date_content'):
                        results['days_skipped'] += 1
                        continue
                    
                    # Try to sync this date
                    check_datetime = datetime.combine(check_date, datetime.min.time())
                    news_data = self.archive_org.fetch_abc_news_for_date(check_datetime)
                    
                    if news_data['shows_found'] and not news_data['error']:
                        saved = self.archive_org.save_abc_news_to_database(news_data)
                        if saved:
                            results['days_synced'] += 1
                            results['synced_dates'].append(str(check_date))
                            logging.info(f"Synced missing content for {check_date}")
                        else:
                            results['errors'] += 1
                    else:
                        results['errors'] += 1
                    
                    # Rate limiting
                    time.sleep(1)
                
                return results
                
            except Exception as e:
                logging.error(f"Error during recent missing days sync: {e}")
                results['errors'] += 1
                return results
    
    def schedule_daily_sync(self):
        """Set up scheduled daily sync"""
        # Schedule sync at 9 AM daily (after Archive.org likely has yesterday's content)
        schedule.every().day.at("09:00").do(self.sync_yesterday_news)
        
        # Also try to sync today's content at 11 PM (Archive.org might have same-day content)
        schedule.every().day.at("23:00").do(self.sync_today_news)
        
        # Weekly check for any missing recent content on Sundays at 10 AM
        schedule.every().sunday.at("10:00").do(self.sync_recent_missing_days)
        
        logging.info("Scheduled daily ABC News sync at 9 AM and 11 PM")
    
    def run_scheduler(self):
        """Run the scheduler (for production use)"""
        self.is_running = True
        logging.info("Starting ABC News daily auto-sync scheduler")
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logging.info("Stopped ABC News daily auto-sync scheduler")
    
    def manual_sync_date(self, target_date: str) -> Dict:
        """Manually sync a specific date (YYYY-MM-DD format)"""
        try:
            # Parse date string
            date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            date_datetime = datetime.combine(date_obj, datetime.min.time())
            
            with app.app_context():
                # Check if content already exists
                existing = ContentSource.query.filter(
                    ContentSource.name == 'ABC News',
                    db.func.date(ContentSource.published_date) == date_obj
                ).first()
                
                # Skip if we already have authentic Archive.org content for this date
                if existing:
                    try:
                        if existing.content_metadata:
                            import json
                            metadata = json.loads(existing.content_metadata) if isinstance(existing.content_metadata, str) else existing.content_metadata
                            if metadata.get('source') == 'archive_org' and metadata.get('authentic_date_content'):
                    return {
                        'status': 'skipped',
                        'message': f"Content for {date_obj} already exists",
                        'date': target_date
                    }
                
                # Fetch and save content
                news_data = self.archive_org.fetch_abc_news_for_date(date_datetime)
                
                if news_data['shows_found'] and not news_data['error']:
                    saved = self.archive_org.save_abc_news_to_database(news_data)
                    
                    if saved:
                        return {
                            'status': 'success',
                            'message': f"Successfully synced {len(news_data['shows_found'])} shows",
                            'date': target_date,
                            'shows_count': len(news_data['shows_found']),
                            'total_duration': news_data['total_duration']
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': f"Failed to save content for {date_obj}",
                            'date': target_date
                        }
                else:
                    error_msg = news_data.get('error', 'No content found')
                    return {
                        'status': 'no_content',
                        'message': f"No content found: {error_msg}",
                        'date': target_date
                    }
                    
        except ValueError:
            return {
                'status': 'error',
                'message': f"Invalid date format. Use YYYY-MM-DD",
                'date': target_date
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error syncing {target_date}: {str(e)}",
                'date': target_date
            }
    
    def get_sync_status(self) -> Dict:
        """Get status of daily sync system"""
        with app.app_context():
            try:
                # Get total ABC News content
                total_content = ContentSource.query.filter_by(name='ABC News').count()
                
                # Get content by source
                archive_content = ContentSource.query.filter(
                    ContentSource.name == 'ABC News',
                    ContentSource.content_metadata.contains('"source": "archive_org"')
                ).count()
                
                live_stream_content = ContentSource.query.filter(
                    ContentSource.name == 'ABC News',
                    ContentSource.url.like('https://abcnews.go.com/Live%')
                ).count()
                
                # Get recent content (last 7 days)
                recent_date = datetime.now() - timedelta(days=7)
                recent_content = ContentSource.query.filter(
                    ContentSource.name == 'ABC News',
                    ContentSource.published_date >= recent_date
                ).count()
                
                return {
                    'scheduler_running': self.is_running,
                    'total_abc_content': total_content,
                    'archive_org_content': archive_content,
                    'live_stream_content': live_stream_content,
                    'recent_content_7_days': recent_content,
                    'last_sync_time': datetime.now().isoformat()
                }
                
            except Exception as e:
                logging.error(f"Error getting sync status: {e}")
                return {'error': str(e)}