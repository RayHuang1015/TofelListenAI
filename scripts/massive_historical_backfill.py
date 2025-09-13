"""
Massive Historical Backfill Script
Generate complete 5-hour daily news editions for years 2001-2017
This creates approximately 6,209 daily editions (17 years * 365.25 days/year)
"""

import logging
import sys
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import json
import time

# Add project root to path
sys.path.insert(0, '/home/runner/workspace')

from app import app, db
from models import DailyEdition, EditionSegment, ProviderSource
from services.historical_news_generator import HistoricalNewsGenerator
from services.daily_auto_generator import DailyAutoGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MassiveHistoricalBackfill:
    """Generate daily editions for years 2001-2017"""
    
    TARGET_YEARS = list(range(2001, 2018))  # 2001-2017 inclusive
    TARGET_DURATION = 18000  # 5 hours in seconds
    
    YEAR_DETAILS = {
        # Year: (days, leap_year_status)
        2001: 365, 2002: 365, 2003: 365, 2004: 366,  # 2004 leap
        2005: 365, 2006: 365, 2007: 365, 2008: 366,  # 2008 leap
        2009: 365, 2010: 365, 2011: 365, 2012: 366,  # 2012 leap
        2013: 365, 2014: 365, 2015: 365, 2016: 366,  # 2016 leap
        2017: 365
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.news_generator = HistoricalNewsGenerator()
        self.auto_generator = DailyAutoGenerator()
        
        # Get or create the Historical News Generator provider
        with app.app_context():
            self.historical_provider = self._get_or_create_historical_provider()
        
        # Statistics tracking
        self.stats = {
            'total_dates_to_process': 0,
            'editions_created': 0,
            'segments_created': 0,
            'audio_files_generated': 0,
            'errors': [],
            'start_time': None,
            'end_time': None
        }
        
        self.logger.info("Massive Historical Backfill System initialized")
    
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
    
    def calculate_scope(self) -> Dict[str, int]:
        """Calculate the complete scope of the backfill operation"""
        
        total_days = sum(self.YEAR_DETAILS.values())
        estimated_segments = total_days * 100  # ~100 segments per day for 5 hours
        
        scope = {
            'years_to_process': len(self.TARGET_YEARS),
            'total_days': total_days,
            'estimated_segments': estimated_segments,
            'estimated_audio_files': total_days,
            'target_duration_hours': total_days * 5,  # 5 hours per day
            'database_size_estimate_mb': total_days * 2  # ~2MB per day in database
        }
        
        self.logger.info(f"Backfill scope: {json.dumps(scope, indent=2)}")
        return scope
    
    def find_missing_dates(self, year_range: Optional[List[int]] = None) -> List[date]:
        """Find all missing dates in the specified year range"""
        
        if year_range is None:
            year_range = self.TARGET_YEARS
        
        with app.app_context():
            missing_dates = []
            
            for year in year_range:
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
                
                # Get existing dates for this year
                existing_dates = set()
                editions = DailyEdition.query.filter(
                    DailyEdition.date >= start_date,
                    DailyEdition.date <= end_date
                ).all()
                
                for edition in editions:
                    existing_dates.add(edition.date)
                
                # Find missing dates
                current_date = start_date
                while current_date <= end_date:
                    if current_date not in existing_dates:
                        missing_dates.append(current_date)
                    current_date += timedelta(days=1)
                
                self.logger.info(f"Year {year}: {len(existing_dates)} existing, {self.YEAR_DETAILS[year] - len(existing_dates)} missing")
        
        self.logger.info(f"Total missing dates found: {len(missing_dates)}")
        return missing_dates
    
    def generate_batch_editions(self, dates: List[date], batch_size: int = 15) -> Dict[str, Any]:
        """Generate editions in batches to manage memory and processing"""
        
        total_dates = len(dates)
        batches_needed = (total_dates + batch_size - 1) // batch_size
        
        self.logger.info(f"Processing {total_dates} dates in {batches_needed} batches of {batch_size}")
        
        results = {
            'batches_processed': 0,
            'editions_created': 0,
            'total_errors': 0,
            'processing_times': []
        }
        
        for batch_idx in range(batches_needed):
            batch_start_time = time.time()
            
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_dates)
            batch_dates = dates[start_idx:end_idx]
            
            self.logger.info(f"Processing batch {batch_idx + 1}/{batches_needed}: {len(batch_dates)} dates")
            
            # Process this batch
            batch_result = self._process_date_batch(batch_dates)
            
            results['editions_created'] += batch_result.get('editions_created', 0)
            results['total_errors'] += batch_result.get('errors', 0)
            
            batch_time = time.time() - batch_start_time
            results['processing_times'].append(batch_time)
            
            self.logger.info(f"Batch {batch_idx + 1} completed in {batch_time:.1f}s: "
                           f"{batch_result.get('editions_created', 0)} editions, "
                           f"{batch_result.get('errors', 0)} errors")
            
            results['batches_processed'] += 1
            
            # Small delay between batches to avoid overwhelming the system
            if batch_idx < batches_needed - 1:
                time.sleep(2)
        
        return results
    
    def _process_date_batch(self, dates: List[date]) -> Dict[str, Any]:
        """Process a single batch of dates"""
        
        batch_results = {
            'editions_created': 0,
            'segments_created': 0,
            'errors': 0,
            'error_details': []
        }
        
        with app.app_context():
            for target_date in dates:
                try:
                    result = self._create_single_edition(target_date)
                    
                    if result.get('status') == 'success':
                        batch_results['editions_created'] += 1
                        batch_results['segments_created'] += result.get('segments_created', 0)
                    else:
                        batch_results['errors'] += 1
                        batch_results['error_details'].append({
                            'date': str(target_date),
                            'error': result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    batch_results['errors'] += 1
                    batch_results['error_details'].append({
                        'date': str(target_date),
                        'error': str(e)
                    })
                    self.logger.error(f"Failed to process {target_date}: {e}")
        
        return batch_results
    
    def _process_date_batch_with_retry(self, dates: List[date], max_retries: int = 3) -> Dict[str, Any]:
        """Process a batch of dates with retry mechanism and timeout handling"""
        
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        import random
        
        batch_results = {
            'editions_created': 0,
            'segments_created': 0,
            'errors': 0,
            'error_details': []
        }
        
        for target_date in dates:
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    # Use direct processing with app context (avoid threading issues)
                    with app.app_context():
                        result = self._create_single_edition(target_date)
                        
                        if result.get('status') == 'success':
                            batch_results['editions_created'] += 1
                            batch_results['segments_created'] += result.get('segments_created', 0)
                            success = True
                            self.logger.debug(f"✅ Successfully processed {target_date}")
                        else:
                            raise Exception(result.get('error', 'Unknown error'))
                        
                except Exception as e:
                    retry_count += 1
                    error_msg = str(e)
                    
                    # Check if this is a retryable error
                    retryable_errors = ['timeout', 'connection', 'temporary', 'deadlock', 'lock']
                    is_retryable = any(keyword in error_msg.lower() for keyword in retryable_errors)
                    
                    if retry_count < max_retries and is_retryable:
                        # Exponential backoff with jitter
                        delay = (2 ** retry_count) + random.uniform(0, 1)
                        self.logger.warning(f"Retry {retry_count}/{max_retries} for {target_date} after {delay:.1f}s: {error_msg}")
                        time.sleep(delay)
                        
                        # Clear any failed transaction state
                        try:
                            db.session.rollback()
                        except:
                            pass
                    else:
                        # Final failure
                        batch_results['errors'] += 1
                        batch_results['error_details'].append({
                            'date': str(target_date),
                            'error': error_msg,
                            'retries_attempted': retry_count
                        })
                        
                        self.logger.error(f"❌ Failed to process {target_date} after {retry_count} retries: {error_msg}")
                        break
        
        return batch_results
    
    def _create_single_edition(self, target_date: date) -> Dict[str, Any]:
        """Create a single daily edition using efficient direct database operations"""
        
        try:
            # Generate content for this date
            articles = self.news_generator.generate_news_for_date(target_date)
            
            if not articles:
                return {
                    'status': 'error',
                    'error': f'No content generated for {target_date}'
                }
            
            # Create daily edition
            edition = DailyEdition()
            edition.date = target_date
            edition.title = f"International News - {target_date.strftime('%B %d, %Y')}"
            edition.status = 'ready'  # Mark as ready immediately for efficiency
            edition.total_duration_sec = self.TARGET_DURATION
            edition.word_count = sum(len(article.get('content', '').split()) for article in articles[:100])
            edition.edition_number = 1
            edition.edition_metadata = {
                'auto_generated': True,
                'backfill_generated': True,
                'generation_date': datetime.now().isoformat(),
                'target_duration': self.TARGET_DURATION,
                'content_sources': ['HistoricalNewsGenerator'],
                'articles_used': len(articles[:100]),
                'historical_backfill': True
            }
            
            db.session.add(edition)
            db.session.flush()  # Get the edition.id
            
            # Create segments (limit to 100 articles for 5 hours)
            segments_created = 0
            duration_per_article = 180  # 3 minutes each
            
            for i, article_data in enumerate(articles[:100]):
                try:
                    segment = EditionSegment()
                    segment.edition_id = edition.id
                    segment.provider_id = self.historical_provider.id  # Dynamic provider lookup
                    segment.seq = i + 1
                    segment.duration_sec = duration_per_article
                    segment.headline = article_data.get('title', f'Historical News {i+1}')[:200]  # Limit length
                    segment.transcript_text = article_data.get('content', '')
                    segment.category = article_data.get('category', 'general')
                    segment.region = 'global'
                    segment.segment_metadata = {
                        'auto_generated': True,
                        'backfill_generated': True,
                        'theme': article_data.get('theme', 'general'),
                        'generation_date': datetime.now().isoformat(),
                        'historical_year': target_date.year
                    }
                    
                    db.session.add(segment)
                    segments_created += 1
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create segment {i} for {target_date}: {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            return {
                'status': 'success',
                'edition_id': edition.id,
                'segments_created': segments_created,
                'date': str(target_date)
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to create edition for {target_date}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'date': str(target_date)
            }
    
    def run_full_backfill(self, years: Optional[List[int]] = None, batch_size: int = 50) -> Dict[str, Any]:
        """Run the complete historical backfill process"""
        
        self.stats['start_time'] = datetime.now()
        
        if years is None:
            years = self.TARGET_YEARS
        
        self.logger.info(f"Starting massive historical backfill for years: {years}")
        
        # Calculate scope
        scope = self.calculate_scope()
        
        # Find missing dates
        missing_dates = self.find_missing_dates(years)
        
        if not missing_dates:
            self.logger.info("No missing dates found - backfill complete!")
            return {
                'status': 'complete',
                'message': 'All historical dates already have editions'
            }
        
        self.stats['total_dates_to_process'] = len(missing_dates)
        
        # Process in batches
        batch_results = self.generate_batch_editions(missing_dates, batch_size)
        
        self.stats['editions_created'] = batch_results['editions_created']
        self.stats['end_time'] = datetime.now()
        
        # Calculate final statistics
        duration = self.stats['end_time'] - self.stats['start_time']
        
        final_results = {
            'status': 'completed',
            'scope': scope,
            'processing_stats': {
                'total_dates_processed': len(missing_dates),
                'editions_created': batch_results['editions_created'],
                'total_errors': batch_results['total_errors'],
                'processing_duration': str(duration),
                'average_batch_time': sum(batch_results['processing_times']) / len(batch_results['processing_times']) if batch_results['processing_times'] else 0,
                'editions_per_minute': (batch_results['editions_created'] / duration.total_seconds()) * 60 if duration.total_seconds() > 0 else 0
            }
        }
        
        self.logger.info(f"Massive backfill completed: {json.dumps(final_results, indent=2)}")
        
        return final_results
    
    def run_year_backfill(self, year: int, batch_size: int = 15) -> Dict[str, Any]:
        """Run backfill for a specific year"""
        
        if year not in self.TARGET_YEARS:
            return {
                'status': 'error',
                'error': f'Year {year} not in target range {self.TARGET_YEARS[0]}-{self.TARGET_YEARS[-1]}'
            }
        
        self.logger.info(f"Starting backfill for year {year}")
        
        return self.run_full_backfill([year], batch_size)
    
    def run_continuous_backfill(self, max_iterations: int = 100, batch_size: int = 15, 
                               sleep_between_batches: int = 10) -> Dict[str, Any]:
        """Run backfill continuously until all dates are complete or max iterations reached"""
        
        iteration = 0
        total_processed = 0
        
        self.logger.info(f"Starting continuous backfill with max {max_iterations} iterations")
        
        while iteration < max_iterations:
            iteration += 1
            
            # Find missing dates for all years
            missing_dates = self.find_missing_dates()
            
            if not missing_dates:
                self.logger.info("✅ All historical editions completed!")
                return {
                    'status': 'completed',
                    'iterations_run': iteration,
                    'total_dates_processed': total_processed
                }
            
            # Process only a small batch to maintain stability
            batch_dates = missing_dates[:batch_size]
            self.logger.info(f"Iteration {iteration}: Processing {len(batch_dates)} missing dates")
            
            try:
                # Process this small batch
                with app.app_context():
                    batch_results = self._process_date_batch_with_retry(batch_dates)
                    
                    # Clear SQLAlchemy session to prevent memory buildup
                    db.session.expunge_all()
                    db.session.remove()
                
                processed_count = batch_results.get('editions_created', 0)
                total_processed += processed_count
                
                self.logger.info(f"Iteration {iteration} completed: {processed_count} editions created, "
                               f"{batch_results.get('errors', 0)} errors")
                
                # If no progress made, increase sleep time
                if processed_count == 0:
                    sleep_time = sleep_between_batches * 2
                    self.logger.warning(f"No progress in iteration {iteration}, sleeping {sleep_time}s")
                else:
                    sleep_time = sleep_between_batches
                
                # Sleep between iterations to avoid overwhelming the system
                import random
                jitter = random.uniform(0.5, 1.5)  # Add randomness to avoid thundering herd
                time.sleep(sleep_time * jitter)
                
            except Exception as e:
                self.logger.error(f"Error in iteration {iteration}: {e}")
                time.sleep(sleep_between_batches * 3)  # Longer sleep on error
                continue
        
        self.logger.info(f"Reached max iterations ({max_iterations}), processed {total_processed} total dates")
        return {
            'status': 'max_iterations_reached',
            'iterations_run': iteration,
            'total_dates_processed': total_processed,
            'remaining_missing': len(self.find_missing_dates()) if iteration == max_iterations else 0
        }
    
    def get_backfill_status(self) -> Dict[str, Any]:
        """Get current backfill status across all target years"""
        
        with app.app_context():
            status_by_year = {}
            total_missing = 0
            total_existing = 0
            
            for year in self.TARGET_YEARS:
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
                
                existing_count = DailyEdition.query.filter(
                    DailyEdition.date >= start_date,
                    DailyEdition.date <= end_date
                ).count()
                
                expected_count = self.YEAR_DETAILS[year]
                missing_count = expected_count - existing_count
                
                status_by_year[year] = {
                    'expected': expected_count,
                    'existing': existing_count,
                    'missing': missing_count,
                    'completion_percentage': (existing_count / expected_count) * 100
                }
                
                total_existing += existing_count
                total_missing += missing_count
            
            return {
                'years_covered': self.TARGET_YEARS,
                'total_days_expected': sum(self.YEAR_DETAILS.values()),
                'total_existing': total_existing,
                'total_missing': total_missing,
                'overall_completion_percentage': (total_existing / sum(self.YEAR_DETAILS.values())) * 100,
                'status_by_year': status_by_year
            }


def main():
    """Main execution function"""
    
    backfill = MassiveHistoricalBackfill()
    
    # Check current status
    print("=== CURRENT BACKFILL STATUS ===")
    status = backfill.get_backfill_status()
    print(json.dumps(status, indent=2))
    
    # Ask for confirmation before proceeding with massive operation
    print(f"\n=== BACKFILL SCOPE ===")
    print(f"Years to process: 2001-2017 ({len(backfill.TARGET_YEARS)} years)")
    print(f"Total missing editions: {status['total_missing']}")
    print(f"Estimated processing time: {status['total_missing'] // 50} minutes")
    
    if status['total_missing'] == 0:
        print("✅ All historical editions already exist!")
        return
    
    # For testing, start with just one year
    print("\n=== STARTING WITH 2001 FOR TESTING ===")
    result_2001 = backfill.run_year_backfill(2001, batch_size=30)
    print(f"2001 Results: {json.dumps(result_2001, indent=2)}")
    
    # If 2001 succeeds, can proceed with other years
    if result_2001.get('status') == 'completed':
        print("\n✅ 2001 completed successfully!")
        print("Ready to process remaining years 2002-2017...")
        
        # Process remaining years (uncomment when ready for full backfill)
        # remaining_years = list(range(2002, 2018))
        # full_result = backfill.run_full_backfill(remaining_years, batch_size=30)
        # print(f"Full backfill result: {json.dumps(full_result, indent=2)}")


if __name__ == '__main__':
    main()