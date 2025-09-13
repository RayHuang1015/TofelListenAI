"""
Persistent Historical Backfill Service
A robust, self-healing service that continuously processes missing historical content
"""

import threading
import logging
import time
import gc
import psutil
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import traceback
import random

from app import app, db
from models import DailyEdition, ProviderSource
from services.historical_news_generator import HistoricalNewsGenerator


class PersistentBackfillService:
    """A persistent service that continuously processes historical backfill"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.worker_thread = None
        self.shutdown_event = threading.Event()
        
        # Optimized configuration for stability
        self.batch_size = 5  # Very small batches for maximum stability
        self.sleep_between_batches = 12  # Longer sleep for resource recovery
        self.max_retries = 3
        self.memory_check_interval = 50  # Check memory every 50 processed items
        self.restart_interval_hours = 6  # Auto-restart every 6 hours
        
        # Target years (2001-2017)
        self.target_years = list(range(2001, 2018))
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_errors': 0,
            'service_restarts': 0,
            'last_restart': datetime.now(),
            'start_time': datetime.now()
        }
        
        # Initialize generator
        self.generator = HistoricalNewsGenerator()
        
        # Historical provider (dynamic lookup)
        self.historical_provider = None
        
    def _get_or_create_historical_provider(self):
        """Get or create the historical provider"""
        if self.historical_provider:
            return self.historical_provider
            
        with app.app_context():
            provider = ProviderSource.query.filter_by(key='HistoricalNewsGenerator').first()
            if not provider:
                provider = ProviderSource(
                    key='HistoricalNewsGenerator',
                    name='Historical News Generator',
                    type='historical',
                    active=True,
                    provider_metadata={'description': 'Generates historical news content for TOEFL practice'}
                )
                db.session.add(provider)
                db.session.commit()
                self.logger.info("Created historical provider")
            
            self.historical_provider = provider
            return provider
    
    def start(self):
        """Start the persistent backfill service"""
        if self.is_running:
            self.logger.warning("Service already running")
            return
            
        self.is_running = True
        self.shutdown_event.clear()
        
        self.worker_thread = threading.Thread(target=self._service_loop, daemon=True)
        self.worker_thread.start()
        
        self.logger.info("Persistent Backfill Service started")
    
    def stop(self):
        """Stop the service"""
        self.is_running = False
        self.shutdown_event.set()
        
        if self.worker_thread:
            self.worker_thread.join(timeout=30)
            
        self.logger.info("Persistent Backfill Service stopped")
    
    def _service_loop(self):
        """Main service loop with auto-restart and error recovery"""
        consecutive_errors = 0
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Check for auto-restart condition
                if self._should_restart():
                    self._perform_restart()
                    continue
                
                # Find and process missing dates
                missing_dates = self._find_missing_dates()
                
                if not missing_dates:
                    self.logger.info("✅ All historical editions completed!")
                    time.sleep(300)  # Check again in 5 minutes
                    continue
                
                # Process a small batch
                batch_dates = missing_dates[:self.batch_size]
                self.logger.info(f"Processing batch of {len(batch_dates)} missing dates")
                
                # Process batch with full error handling
                success_count, error_count = self._process_batch_with_recovery(batch_dates)
                
                # Update statistics
                self.stats['total_processed'] += success_count
                self.stats['total_errors'] += error_count
                
                # Reset consecutive error counter on success
                if success_count > 0:
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                
                # If too many consecutive errors, force restart
                if consecutive_errors >= 5:
                    self.logger.error("Too many consecutive errors, forcing restart")
                    self._perform_restart()
                    consecutive_errors = 0
                    continue
                
                # Memory management check
                if self.stats['total_processed'] % self.memory_check_interval == 0:
                    self._perform_memory_cleanup()
                
                # Progressive sleep (longer if no progress)
                sleep_time = self.sleep_between_batches
                if success_count == 0:
                    sleep_time *= 2  # Double sleep time if no progress
                
                # Add random jitter to prevent thundering herd
                jitter = random.uniform(0.7, 1.3)
                actual_sleep = sleep_time * jitter
                
                self.logger.debug(f"Sleeping {actual_sleep:.1f}s before next batch")
                self.shutdown_event.wait(actual_sleep)
                
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Service loop error: {e}")
                self.logger.debug(traceback.format_exc())
                
                # Progressive backoff on errors
                error_sleep = min(60, 10 * consecutive_errors)
                self.shutdown_event.wait(error_sleep)
    
    def _find_missing_dates(self) -> List[date]:
        """Find all missing dates across target years"""
        missing_dates = []
        
        with app.app_context():
            for year in self.target_years:
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
        
        return missing_dates
    
    def _process_batch_with_recovery(self, dates: List[date]) -> tuple[int, int]:
        """Process a batch with comprehensive error recovery"""
        success_count = 0
        error_count = 0
        
        for target_date in dates:
            retry_count = 0
            processed = False
            
            while retry_count < self.max_retries and not processed:
                try:
                    with app.app_context():
                        # Clear any previous transaction state
                        db.session.rollback()
                        
                        # Generate content for this date
                        historical_provider = self._get_or_create_historical_provider()
                        content = self.generator.generate_news_for_date(target_date)
                        
                        if not content or len(content) == 0:
                            raise Exception("No content generated")
                        
                        # Create daily edition
                        edition = DailyEdition(
                            date=target_date,
                            total_duration_seconds=18000,  # Exactly 5 hours
                            segment_count=len(content),
                            listener_count=0,
                            completion_rate=0.0
                        )
                        
                        db.session.add(edition)
                        db.session.flush()  # Get edition ID
                        
                        # Create edition segments
                        total_duration = 0
                        for idx, article in enumerate(content):
                            from models import EditionSegment
                            
                            segment = EditionSegment(
                                edition_id=edition.id,
                                provider_id=historical_provider.id,
                                segment_order=idx + 1,
                                title=article.get('title', f'News Article {idx + 1}'),
                                content=article.get('content', ''),
                                duration_seconds=article.get('duration_seconds', 180),
                                source_url=article.get('source_url', ''),
                                audio_file_path=None,
                                tts_generated=False
                            )
                            
                            total_duration += segment.duration_seconds
                            db.session.add(segment)
                        
                        # Update edition with actual duration
                        edition.total_duration_seconds = total_duration
                        
                        # Commit transaction
                        db.session.commit()
                        
                        success_count += 1
                        processed = True
                        
                        self.logger.debug(f"✅ Processed {target_date}: {len(content)} articles, {total_duration}s duration")
                        
                except Exception as e:
                    retry_count += 1
                    error_msg = str(e)
                    
                    # Clear failed transaction
                    try:
                        db.session.rollback()
                    except:
                        pass
                    
                    if retry_count < self.max_retries:
                        # Exponential backoff
                        delay = (2 ** retry_count) + random.uniform(0, 1)
                        self.logger.warning(f"Retry {retry_count}/{self.max_retries} for {target_date}: {error_msg}")
                        time.sleep(delay)
                    else:
                        error_count += 1
                        self.logger.error(f"❌ Failed {target_date} after {retry_count} retries: {error_msg}")
        
        return success_count, error_count
    
    def _should_restart(self) -> bool:
        """Check if service should auto-restart"""
        hours_running = (datetime.now() - self.stats['last_restart']).total_seconds() / 3600
        return hours_running >= self.restart_interval_hours
    
    def _perform_restart(self):
        """Perform service restart for memory cleanup"""
        self.logger.info("Performing service restart for maintenance")
        
        # Clear SQLAlchemy session
        try:
            db.session.expunge_all()
            db.session.remove()
        except:
            pass
        
        # Force garbage collection
        gc.collect()
        
        # Update restart stats
        self.stats['service_restarts'] += 1
        self.stats['last_restart'] = datetime.now()
        
        # Small pause for resource cleanup
        time.sleep(5)
    
    def _perform_memory_cleanup(self):
        """Perform memory cleanup operations"""
        try:
            # SQLAlchemy cleanup
            db.session.expunge_all()
            db.session.remove()
            
            # Force garbage collection
            gc.collect()
            
            # Log memory usage
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.logger.debug(f"Memory usage: {memory_mb:.1f} MB")
            
        except Exception as e:
            self.logger.warning(f"Memory cleanup error: {e}")
    
    def get_status(self) -> Dict:
        """Get current service status"""
        with app.app_context():
            missing_dates = self._find_missing_dates()
            
            # Calculate completion stats
            total_days_target = sum(366 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 365 
                                  for year in self.target_years)
            completed_days = total_days_target - len(missing_dates)
            completion_percentage = (completed_days / total_days_target) * 100
            
            uptime = datetime.now() - self.stats['start_time']
            
            return {
                'is_running': self.is_running,
                'uptime_hours': uptime.total_seconds() / 3600,
                'total_processed': self.stats['total_processed'],
                'total_errors': self.stats['total_errors'],
                'service_restarts': self.stats['service_restarts'],
                'missing_dates_count': len(missing_dates),
                'completion_percentage': completion_percentage,
                'batch_size': self.batch_size,
                'sleep_interval': self.sleep_between_batches
            }


# Global service instance
_service_instance = None


def get_service() -> PersistentBackfillService:
    """Get or create the global service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = PersistentBackfillService()
    return _service_instance


def start_service():
    """Start the persistent backfill service"""
    service = get_service()
    service.start()
    return service


def stop_service():
    """Stop the persistent backfill service"""
    global _service_instance
    if _service_instance:
        _service_instance.stop()
        _service_instance = None


def get_status():
    """Get service status"""
    service = get_service()
    return service.get_status()