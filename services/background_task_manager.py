"""
Background Task Manager for Historical Content Loading
Handles large-scale content ingestion safely in the background
"""

import threading
import logging
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Callable
import queue
import json
from concurrent.futures import ThreadPoolExecutor, Future
import traceback

from app import app, db
from models import IngestionJob, DailyEdition
from services.real_content_providers import fetch_real_content_for_date
from services.daily_edition_composer import DailyEditionComposer


class BackgroundTaskManager:
    """Manages background tasks for historical content loading"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.task_queue = queue.Queue()
        self.active_tasks = {}
        self.is_running = False
        self.worker_thread = None
        self.max_concurrent_days = 3  # Process max 3 days simultaneously
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent_days)
        
    def start(self):
        """Start the background task manager"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            self.logger.info("Background task manager started")
    
    def stop(self):
        """Stop the background task manager"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
        self.executor.shutdown(wait=True)
        self.logger.info("Background task manager stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.is_running:
            try:
                # Process pending tasks
                self._process_pending_tasks()
                
                # Clean up completed tasks
                self._cleanup_completed_tasks()
                
                # Sleep briefly
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in worker loop: {e}")
                time.sleep(10)
    
    def _process_pending_tasks(self):
        """Process pending tasks from the queue"""
        try:
            # Get pending ingestion jobs from database
            with app.app_context():
                pending_jobs = IngestionJob.query.filter_by(status='pending').limit(5).all()
                
                for job in pending_jobs:
                    if len(self.active_tasks) >= self.max_concurrent_days:
                        break
                    
                    # Mark job as running
                    job.status = 'running'
                    db.session.commit()
                    
                    # Submit task to executor
                    future = self.executor.submit(self._process_historical_day, job.id)
                    self.active_tasks[job.id] = {
                        'job': job,
                        'future': future,
                        'started_at': datetime.utcnow()
                    }
                    
                    self.logger.info(f"Started processing job {job.id} for date {job.date}")
        
        except Exception as e:
            self.logger.error(f"Error processing pending tasks: {e}")
    
    def _cleanup_completed_tasks(self):
        """Clean up completed tasks"""
        completed_job_ids = []
        
        for job_id, task_info in self.active_tasks.items():
            future = task_info['future']
            
            if future.done():
                try:
                    result = future.result()
                    self._handle_task_completion(job_id, result)
                except Exception as e:
                    self._handle_task_error(job_id, e)
                
                completed_job_ids.append(job_id)
        
        # Remove completed tasks
        for job_id in completed_job_ids:
            del self.active_tasks[job_id]
    
    def _process_historical_day(self, job_id: int) -> Dict[str, any]:
        """Process content for a single historical day"""
        with app.app_context():
            try:
                job = IngestionJob.query.get(job_id)
                if not job:
                    return {'status': 'error', 'error': 'Job not found'}
                
                target_date = job.date
                self.logger.info(f"Processing historical content for {target_date}")
                
                # Step 1: Fetch real content from providers
                content_result = fetch_real_content_for_date(target_date)
                
                if content_result['status'] != 'success':
                    return {
                        'status': 'error',
                        'error': f"Content fetch failed: {content_result.get('error', 'Unknown error')}"
                    }
                
                # Step 2: Compose daily edition if we have enough content
                if content_result['items_saved'] > 0:
                    composer = DailyEditionComposer()
                    edition_result = composer.compose_daily_edition(target_date)
                    
                    if edition_result['status'] == 'success':
                        edition = edition_result['edition']
                        
                        # Validate edition quality
                        validation = self._validate_edition_quality(edition)
                        
                        if validation['valid']:
                            # Mark edition as ready
                            edition.status = 'ready'
                            db.session.commit()
                            
                            return {
                                'status': 'success',
                                'date': target_date,
                                'content_items': content_result['items_saved'],
                                'edition_id': edition.id,
                                'edition_duration': edition.total_duration_sec,
                                'validation': validation['metrics']
                            }
                        else:
                            return {
                                'status': 'quality_failed',
                                'date': target_date,
                                'content_items': content_result['items_saved'],
                                'edition_id': edition.id,
                                'validation_issues': validation['issues']
                            }
                    else:
                        return {
                            'status': 'composition_failed',
                            'date': target_date,
                            'content_items': content_result['items_saved'],
                            'error': edition_result.get('error', 'Composition failed')
                        }
                else:
                    return {
                        'status': 'no_content',
                        'date': target_date,
                        'content_items': 0,
                        'error': 'No content found for this date'
                    }
                
            except Exception as e:
                self.logger.error(f"Error processing job {job_id}: {e}")
                self.logger.error(traceback.format_exc())
                return {
                    'status': 'error',
                    'error': str(e)
                }
    
    def _validate_edition_quality(self, edition: DailyEdition) -> Dict[str, any]:
        """Validate edition quality"""
        validation = {
            'valid': True,
            'issues': [],
            'metrics': {}
        }
        
        # Check duration (target: 3 hours ± 20 minutes)
        target_duration = 10800  # 3 hours
        tolerance = 1200  # 20 minutes
        
        if edition.total_duration_sec < (target_duration - tolerance):
            validation['valid'] = False
            validation['issues'].append(f"Duration too short: {edition.total_duration_sec}s")
        elif edition.total_duration_sec > (target_duration + tolerance):
            validation['valid'] = False
            validation['issues'].append(f"Duration too long: {edition.total_duration_sec}s")
        
        # Check segment count
        segment_count = len(edition.segments) if edition.segments else 0
        if segment_count < 5:
            validation['valid'] = False
            validation['issues'].append(f"Too few segments: {segment_count}")
        
        # Check transcript coverage
        segments_with_transcript = sum(1 for s in edition.segments if s.transcript_text)
        transcript_coverage = segments_with_transcript / segment_count if segment_count > 0 else 0
        
        if transcript_coverage < 0.8:
            validation['valid'] = False
            validation['issues'].append(f"Poor transcript coverage: {transcript_coverage:.1%}")
        
        validation['metrics'] = {
            'duration_sec': edition.total_duration_sec,
            'segment_count': segment_count,
            'transcript_coverage': transcript_coverage
        }
        
        return validation
    
    def _handle_task_completion(self, job_id: int, result: Dict[str, any]):
        """Handle successful task completion"""
        with app.app_context():
            try:
                job = IngestionJob.query.get(job_id)
                if job:
                    if result['status'] == 'success':
                        job.status = 'completed'
                        job.stats.update({'items_processed': result.get('content_items', 0)})
                    else:
                        job.status = 'failed'
                        job.last_error = result.get('error', 'Unknown error')
                    
                    job.finished_at = datetime.utcnow()
                    job.stats.update(result)
                    db.session.commit()
                    
                    self.logger.info(f"Completed job {job_id} with status {result['status']}")
            
            except Exception as e:
                self.logger.error(f"Error handling task completion for job {job_id}: {e}")
    
    def _handle_task_error(self, job_id: int, error: Exception):
        """Handle task error"""
        with app.app_context():
            try:
                job = IngestionJob.query.get(job_id)
                if job:
                    job.status = 'failed'
                    job.last_error = str(error)
                    job.finished_at = datetime.utcnow()
                    db.session.commit()
                    
                    self.logger.error(f"Job {job_id} failed: {error}")
            
            except Exception as e:
                self.logger.error(f"Error handling task error for job {job_id}: {e}")
    
    def enqueue_historical_backfill(self, start_date: date, end_date: date) -> List[int]:
        """Enqueue historical backfill jobs in manageable batches"""
        # Restore full historical range as requested by user
        # User specifically wants content from 2018-01-01 onwards
        actual_start_date = start_date  # Use the original start_date (2018-01-01)
        actual_end_date = end_date      # Use the original end_date (2025-09-11)
        job_ids = []
        
        with app.app_context():
            current_date = actual_start_date
            batch_jobs = []
            
            while current_date <= actual_end_date:
                # Check if job already exists
                existing_job = IngestionJob.query.filter_by(date=current_date).first()
                
                if not existing_job:
                    # Create new job
                    job = IngestionJob()
                    job.date = current_date
                    job.status = 'pending'
                    job.attempts = 0
                    job.stats = {
                        'job_type': 'daily_backfill',
                        'providers': ['BBC World Service', 'Reuters International', 'AP News International']
                    }
                    batch_jobs.append(job)
                
                current_date += timedelta(days=1)
            
            # Bulk insert for efficiency
            if batch_jobs:
                db.session.add_all(batch_jobs)
                db.session.commit()
                
                for job in batch_jobs:
                    job_ids.append(job.id)
            
            self.logger.info(f"Enqueued {len(job_ids)} historical news jobs for {actual_start_date} to {actual_end_date}")
        
        return job_ids
    
    def get_backfill_status(self) -> Dict[str, any]:
        """Get current backfill status"""
        with app.app_context():
            # Count jobs by status (filter by stats containing job_type=daily_backfill)
            all_jobs = IngestionJob.query.all()
            backfill_jobs = [j for j in all_jobs if j.stats and j.stats.get('job_type') == 'daily_backfill']
            
            total_jobs = len(backfill_jobs)
            completed_jobs = len([j for j in backfill_jobs if j.status == 'completed'])
            running_jobs = len([j for j in backfill_jobs if j.status == 'running'])
            failed_jobs = len([j for j in backfill_jobs if j.status == 'failed'])
            pending_jobs = len([j for j in backfill_jobs if j.status == 'pending'])
            
            # Count completed editions
            total_editions = DailyEdition.query.filter_by(status='ready').count()
            
            progress_percent = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            
            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'running_jobs': running_jobs,
                'failed_jobs': failed_jobs,
                'pending_jobs': pending_jobs,
                'progress_percent': progress_percent,
                'total_editions': total_editions,
                'active_tasks': len(self.active_tasks)
            }


# Global task manager instance
_task_manager = None

def get_task_manager() -> BackgroundTaskManager:
    """Get the global task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
        _task_manager.start()
    return _task_manager

def start_full_historical_backfill(start_date: date, end_date: date) -> Dict[str, any]:
    """Start full historical backfill process"""
    task_manager = get_task_manager()
    
    try:
        job_ids = task_manager.enqueue_historical_backfill(start_date, end_date)
        
        return {
            'status': 'success',
            'jobs_created': len(job_ids),
            'start_date': start_date,
            'end_date': end_date,
            'message': f'Enqueued {len(job_ids)} days for historical backfill'
        }
        
    except Exception as e:
        logging.error(f"Error starting historical backfill: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_historical_backfill_status() -> Dict[str, any]:
    """Get historical backfill status"""
    task_manager = get_task_manager()
    return task_manager.get_backfill_status()