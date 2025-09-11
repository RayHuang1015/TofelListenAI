"""
Historical Backfill Orchestrator for Daily News Area
Handles large-scale ingestion of 3-hour daily international news content from 2018-2025
"""

import logging
import time
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

from app import db
from models import DailyEdition, EditionSegment, ProviderSource, ContentSource, IngestionJob
from services.international_news_integration import InternationalNewsIntegration
from services.daily_edition_composer import DailyEditionComposer


class HistoricalBackfillOrchestrator:
    """Orchestrates large-scale historical content backfill for daily news area"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.news_integration = InternationalNewsIntegration()
        self.edition_composer = DailyEditionComposer()
        
        # Configuration
        self.TARGET_DURATION_SEC = 10800  # 3 hours
        self.DURATION_TOLERANCE_SEC = 1200  # ±20 minutes
        self.BATCH_SIZE_DAYS = 30  # Process monthly batches
        self.MAX_CONCURRENT_PROVIDERS = 3
        self.MAX_CONCURRENT_DAYS = 5
        self.RETRY_ATTEMPTS = 3
        self.RETRY_DELAY_BASE = 2  # seconds
        
        # International news providers for historical content
        self.historical_providers = [
            {
                'name': 'BBC World Service',
                'type': 'podcast',
                'feeds': [
                    'https://podcasts.files.bbci.co.uk/p02nq0gn.rss',  # Global News Podcast
                    'https://podcasts.files.bbci.co.uk/p02nqff4.rss'   # World Business Report
                ],
                'priority': 1
            },
            {
                'name': 'Reuters Audio',
                'type': 'rss',
                'feeds': [
                    'https://news.yahoo.com/rss/world',
                    'https://feeds.reuters.com/reuters/worldNews'
                ],
                'priority': 2
            },
            {
                'name': 'AP News International',
                'type': 'rss',
                'feeds': [
                    'https://feeds.apnews.com/rss/apf-intlnews',
                    'https://feeds.apnews.com/rss/apf-topnews'
                ],
                'priority': 2
            },
            {
                'name': 'Deutsche Welle English',
                'type': 'youtube',
                'channel_id': 'UCknLrEdhRCp1aegoMqRaCBg',
                'priority': 3
            },
            {
                'name': 'Al Jazeera English',
                'type': 'youtube',
                'channel_id': 'UCNye-wNBqNL5ZzHSJj3l8Bg',
                'priority': 3
            }
        ]
    
    def calculate_date_range(self, start_date: str = "2018-01-01", end_date: str = "2025-09-11") -> List[date]:
        """Calculate all dates that need processing"""
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
        
        self.logger.info(f"Calculated {len(dates)} days for backfill: {start} to {end}")
        return dates
    
    def get_monthly_batches(self, dates: List[date]) -> List[List[date]]:
        """Group dates into monthly batches for processing"""
        batches = []
        current_batch = []
        current_month = None
        
        for date_obj in dates:
            month_key = (date_obj.year, date_obj.month)
            
            if current_month != month_key:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [date_obj]
                current_month = month_key
            else:
                current_batch.append(date_obj)
        
        if current_batch:
            batches.append(current_batch)
        
        self.logger.info(f"Created {len(batches)} monthly batches")
        return batches
    
    def check_existing_edition(self, target_date: date) -> Optional[DailyEdition]:
        """Check if edition already exists for date"""
        return DailyEdition.query.filter_by(date=target_date).first()
    
    def validate_edition_quality(self, edition: DailyEdition) -> Dict[str, any]:
        """Validate if edition meets quality requirements"""
        validation = {
            'valid': True,
            'issues': [],
            'metrics': {}
        }
        
        # Check duration requirements
        min_duration = self.TARGET_DURATION_SEC - self.DURATION_TOLERANCE_SEC
        max_duration = self.TARGET_DURATION_SEC + self.DURATION_TOLERANCE_SEC
        
        if edition.total_duration_sec < min_duration:
            validation['valid'] = False
            validation['issues'].append(f"Duration too short: {edition.total_duration_sec}s < {min_duration}s")
        elif edition.total_duration_sec > max_duration:
            validation['valid'] = False
            validation['issues'].append(f"Duration too long: {edition.total_duration_sec}s > {max_duration}s")
        
        # Check segment count and transcripts
        segments = EditionSegment.query.filter_by(edition_id=edition.id).all()
        segments_without_transcript = [s for s in segments if not s.transcript_text or s.transcript_text.strip() == '']
        
        if len(segments) < 4:
            validation['valid'] = False
            validation['issues'].append(f"Too few segments: {len(segments)} < 4")
        
        if segments_without_transcript:
            validation['valid'] = False
            validation['issues'].append(f"{len(segments_without_transcript)} segments missing transcripts")
        
        # Check provider diversity
        providers = set()
        for s in segments:
            if s.source_content and hasattr(s.source_content, 'name'):
                providers.add(s.source_content.name)
        if len(providers) < 2:
            validation['valid'] = False
            validation['issues'].append(f"Insufficient provider diversity: {len(providers)} providers")
        
        validation['metrics'] = {
            'duration_sec': edition.total_duration_sec,
            'segment_count': len(segments),
            'provider_count': len(providers),
            'transcript_coverage': (len(segments) - len(segments_without_transcript)) / len(segments) if len(segments) > 0 else 0
        }
        
        return validation
    
    def process_single_date(self, target_date: date, force_rebuild: bool = False) -> Dict[str, any]:
        """Process content for a single date"""
        result = {
            'date': target_date,
            'status': 'started',
            'edition_id': None,
            'metrics': {},
            'errors': []
        }
        
        try:
            # Check if edition already exists
            existing_edition = self.check_existing_edition(target_date)
            if existing_edition and not force_rebuild:
                validation = self.validate_edition_quality(existing_edition)
                if validation['valid']:
                    result['status'] = 'exists_valid'
                    result['edition_id'] = existing_edition.id
                    result['metrics'] = validation['metrics']
                    return result
                else:
                    self.logger.info(f"Existing edition for {target_date} invalid: {validation['issues']}")
                    # Will rebuild below
            
            # Start ingestion for this date
            self.logger.info(f"Starting content ingestion for {target_date}")
            
            # Parallel provider ingestion
            ingestion_results = []
            with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENT_PROVIDERS) as executor:
                futures = []
                
                for provider in self.historical_providers:
                    future = executor.submit(self._ingest_provider_for_date, provider, target_date)
                    futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        provider_result = future.result(timeout=300)  # 5 min timeout
                        ingestion_results.append(provider_result)
                    except Exception as e:
                        self.logger.error(f"Provider ingestion failed for {target_date}: {e}")
                        result['errors'].append(str(e))
            
            # Compose daily edition
            if ingestion_results:
                total_items = sum(r.get('items_saved', 0) for r in ingestion_results)
                self.logger.info(f"Ingested {total_items} items for {target_date}, composing edition")
                
                composition_result = self.edition_composer.compose_daily_edition(target_date)
                
                if composition_result['status'] == 'success':
                    edition = composition_result['edition']
                    validation = self.validate_edition_quality(edition)
                    
                    if validation['valid']:
                        result['status'] = 'success'
                        result['edition_id'] = edition.id
                        result['metrics'] = validation['metrics']
                        
                        # Update edition status
                        edition.status = 'ready'
                        db.session.commit()
                    else:
                        result['status'] = 'quality_failed'
                        result['errors'].extend(validation['issues'])
                        result['metrics'] = validation['metrics']
                else:
                    result['status'] = 'composition_failed'
                    result['errors'].append(composition_result.get('error', 'Unknown composition error'))
            else:
                result['status'] = 'no_content'
                result['errors'].append('No content ingested from any provider')
        
        except Exception as e:
            self.logger.error(f"Error processing {target_date}: {e}")
            self.logger.error(traceback.format_exc())
            result['status'] = 'error'
            result['errors'].append(str(e))
        
        return result
    
    def _ingest_provider_for_date(self, provider: Dict, target_date: date) -> Dict[str, any]:
        """Ingest content from a specific provider for a date"""
        result = {
            'provider': provider['name'],
            'date': target_date,
            'items_saved': 0,
            'status': 'success'
        }
        
        try:
            if provider['type'] == 'rss':
                for feed_url in provider['feeds']:
                    feed_result = self.news_integration.ingest_for_date(target_date, feed_url)
                    result['items_saved'] += feed_result.get('items_saved', 0)
            
            elif provider['type'] == 'podcast':
                for feed_url in provider['feeds']:
                    # Use RSS ingestion for podcast feeds
                    feed_result = self.news_integration.ingest_for_date(target_date, feed_url)
                    result['items_saved'] += feed_result.get('items_saved', 0)
            
            elif provider['type'] == 'youtube':
                # YouTube ingestion would need API implementation
                self.logger.info(f"YouTube ingestion for {provider['name']} not yet implemented")
                result['status'] = 'skipped'
        
        except Exception as e:
            self.logger.error(f"Provider {provider['name']} failed for {target_date}: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def run_batch_backfill(self, start_date: str = "2018-01-01", end_date: str = "2025-09-11", 
                          resume_from: Optional[str] = None) -> Dict[str, any]:
        """Run complete historical backfill process"""
        start_time = time.time()
        
        self.logger.info(f"Starting historical backfill: {start_date} to {end_date}")
        
        # Calculate date range
        all_dates = self.calculate_date_range(start_date, end_date)
        
        # Resume from specific date if provided
        if resume_from:
            resume_date = datetime.strptime(resume_from, "%Y-%m-%d").date()
            all_dates = [d for d in all_dates if d >= resume_date]
            self.logger.info(f"Resuming from {resume_from}, processing {len(all_dates)} dates")
        
        # Group into monthly batches
        monthly_batches = self.get_monthly_batches(all_dates)
        
        # Process results tracking
        batch_results = []
        total_processed = 0
        total_success = 0
        total_errors = 0
        
        for batch_idx, batch_dates in enumerate(monthly_batches):
            batch_start_time = time.time()
            batch_month = f"{batch_dates[0].year}-{batch_dates[0].month:02d}"
            
            self.logger.info(f"Processing batch {batch_idx + 1}/{len(monthly_batches)}: {batch_month} ({len(batch_dates)} days)")
            
            batch_result = {
                'batch_month': batch_month,
                'dates_count': len(batch_dates),
                'processed': 0,
                'success': 0,
                'errors': 0,
                'results': []
            }
            
            # Process dates in parallel within batch
            with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENT_DAYS) as executor:
                futures = {
                    executor.submit(self.process_single_date, date_obj): date_obj 
                    for date_obj in batch_dates
                }
                
                for future in as_completed(futures):
                    date_obj = futures[future]
                    try:
                        date_result = future.result(timeout=600)  # 10 min timeout per date
                        batch_result['results'].append(date_result)
                        batch_result['processed'] += 1
                        
                        if date_result['status'] in ['success', 'exists_valid']:
                            batch_result['success'] += 1
                        else:
                            batch_result['errors'] += 1
                            
                    except Exception as e:
                        self.logger.error(f"Future failed for {date_obj}: {e}")
                        batch_result['errors'] += 1
                        batch_result['results'].append({
                            'date': date_obj,
                            'status': 'timeout_error',
                            'errors': [str(e)]
                        })
            
            batch_time = time.time() - batch_start_time
            batch_result['processing_time_sec'] = batch_time
            batch_results.append(batch_result)
            
            # Update totals
            total_processed += batch_result['processed']
            total_success += batch_result['success']
            total_errors += batch_result['errors']
            
            self.logger.info(f"Batch {batch_month} completed: {batch_result['success']}/{batch_result['processed']} success in {batch_time:.1f}s")
            
            # Small delay between batches to be respectful to providers
            time.sleep(5)
        
        total_time = time.time() - start_time
        
        # Summary
        summary = {
            'status': 'completed',
            'total_dates': len(all_dates),
            'total_processed': total_processed,
            'total_success': total_success,
            'total_errors': total_errors,
            'success_rate': total_success / total_processed if total_processed > 0 else 0,
            'total_time_sec': total_time,
            'batches': batch_results
        }
        
        self.logger.info(f"Backfill completed: {total_success}/{total_processed} success ({summary['success_rate']:.1%}) in {total_time:.1f}s")
        
        return summary
    
    def get_backfill_status(self) -> Dict[str, any]:
        """Get current status of historical backfill"""
        # Count existing editions by year
        editions_by_year = {}
        all_editions = DailyEdition.query.all()
        
        for edition in all_editions:
            year = edition.date.year
            if year not in editions_by_year:
                editions_by_year[year] = 0
            editions_by_year[year] += 1
        
        # Calculate expected dates
        all_expected_dates = self.calculate_date_range()
        expected_by_year = {}
        for date_obj in all_expected_dates:
            year = date_obj.year
            if year not in expected_by_year:
                expected_by_year[year] = 0
            expected_by_year[year] += 1
        
        # Calculate completion percentage
        total_existing = sum(editions_by_year.values())
        total_expected = len(all_expected_dates)
        completion_rate = total_existing / total_expected if total_expected > 0 else 0
        
        return {
            'total_expected_days': total_expected,
            'total_existing_editions': total_existing,
            'completion_rate': completion_rate,
            'editions_by_year': editions_by_year,
            'expected_by_year': expected_by_year,
            'missing_days': total_expected - total_existing
        }


# Convenience functions for route usage
def start_historical_backfill(start_date: str = "2018-01-01", end_date: str = "2025-09-11"):
    """Start the historical backfill process"""
    orchestrator = HistoricalBackfillOrchestrator()
    return orchestrator.run_batch_backfill(start_date, end_date)


def get_backfill_progress():
    """Get progress of historical backfill"""
    orchestrator = HistoricalBackfillOrchestrator()
    return orchestrator.get_backfill_status()


def start_sample_backfill():
    """Start sample backfill to demonstrate functionality"""
    from models import DailyEdition, EditionSegment, ProviderSource, ContentSource
    from datetime import datetime, date, timedelta
    import random
    
    result = {
        'status': 'success',
        'editions_created': 0,
        'message': ''
    }
    
    try:
        # Create sample provider sources if they don't exist
        providers = [
            ('BBC World Service', 'International news from BBC'),
            ('Reuters International', 'Global news coverage'),
            ('AP News World', 'Associated Press international'),
            ('Deutsche Welle English', 'German international broadcaster'),
            ('Al Jazeera English', 'Middle East and global news')
        ]
        
        for provider_name, description in providers:
            existing = ProviderSource.query.filter_by(name=provider_name).first()
            if not existing:
                provider = ProviderSource()
                provider.key = provider_name.lower().replace(' ', '_')
                provider.name = provider_name
                provider.type = 'news'
                provider.base_url = 'https://example.com'
                provider.active = True
                provider.provider_metadata = {'description': description}
                db.session.add(provider)
        
        db.session.commit()
        
        # Create sample daily editions for recent dates
        sample_dates = []
        today = date.today()
        for i in range(10):  # Create 10 sample days
            sample_date = today - timedelta(days=i)
            sample_dates.append(sample_date)
        
        for sample_date in sample_dates:
            # Check if edition already exists
            existing_edition = DailyEdition.query.filter_by(date=sample_date).first()
            if existing_edition:
                continue
            
            # Create sample edition
            edition = DailyEdition()
            edition.date = sample_date
            edition.title = f"International News Digest - {sample_date.strftime('%B %d, %Y')}"
            edition.edition_number = 1
            edition.total_duration_sec = 10800 + random.randint(-600, 600)  # ~3 hours ±10 min
            edition.word_count = random.randint(20000, 25000)
            edition.status = 'ready'
            edition.edition_metadata = {
                'categories': ['world', 'politics', 'business'],
                'regions': ['europe', 'asia', 'americas'],
                'quality_score': random.uniform(0.8, 0.95)
            }
            db.session.add(edition)
            db.session.flush()  # Get edition ID
            
            # Create sample segments
            segment_count = random.randint(15, 25)
            total_duration = 0
            target_duration = 10800
            
            for seg_num in range(segment_count):
                # Calculate segment duration to reach target
                remaining_segments = segment_count - seg_num
                remaining_duration = target_duration - total_duration
                
                if remaining_segments == 1:
                    segment_duration = remaining_duration
                else:
                    avg_remaining = remaining_duration // remaining_segments
                    segment_duration = random.randint(
                        max(60, avg_remaining - 120), 
                        min(600, avg_remaining + 120)
                    )
                
                total_duration += segment_duration
                
                # Create sample content source
                content = ContentSource()
                content.name = random.choice([p[0] for p in providers])
                content.url = f'https://example.com/news/{sample_date.strftime("%Y%m%d")}_{seg_num}'
                content.type = 'news'
                content.language = 'en'
                content.duration = segment_duration
                content.description = f'International news segment {seg_num + 1}'
                content.published_date = datetime.combine(sample_date, datetime.min.time())
                content.transcript_text = f'Sample transcript for {content.name} segment {seg_num + 1}'
                db.session.add(content)
                db.session.flush()
                
                # Create segment
                segment = EditionSegment()
                segment.edition_id = edition.id
                segment.source_content_id = content.id
                segment.provider_id = 1  # Use first provider
                segment.seq = seg_num + 1
                segment.start_sec = total_duration - segment_duration
                segment.duration_sec = segment_duration
                segment.headline = f'International News Update {seg_num + 1}'
                segment.transcript_text = f'This is a sample transcript for segment {seg_num + 1} covering international news topics including politics, economics, and world events. The content is approximately {segment_duration} seconds long and provides comprehensive coverage of current affairs.'
                segment.region = random.choice(['global', 'europe', 'asia', 'americas', 'africa'])
                segment.category = random.choice(['politics', 'business', 'technology', 'world'])
                segment.segment_metadata = {
                    'importance': random.uniform(0.6, 1.0),
                    'source_type': 'sample'
                }
                db.session.add(segment)
            
            # Update edition with actual total duration
            edition.total_duration_sec = total_duration
            result['editions_created'] += 1
        
        db.session.commit()
        
        if result['editions_created'] == 0:
            result['message'] = 'Sample editions already exist for recent dates'
        else:
            result['message'] = f'Created {result["editions_created"]} sample daily editions with 3-hour content'
            
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error in sample backfill: {e}')
        result['status'] = 'error'
        result['message'] = str(e)
    
    return result