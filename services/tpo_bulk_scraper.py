"""
TPO Bulk Scraper Framework

Framework for systematically collecting TPO audio URLs from multiple sources.
Designed to replace fragile dictionary mappings with comprehensive URL collection.
"""

import re
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json

from app import db
from models import TPOAudioMap
from services.tpo_audio_resolver import TPOAudioResolver


class TPOBulkScraper:
    """Comprehensive TPO audio URL scraper framework"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.resolver = TPOAudioResolver()
        
        # Rate limiting settings
        self.request_delay = 1.0  # seconds between requests
        self.timeout = 15  # request timeout
        
        # User agent to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def scrape_google_docs_tpo_urls(self, doc_url: str, tpo_range: Tuple[int, int] = (35, 75)) -> Dict:
        """
        Scrape TPO URLs from Google Docs document
        
        Args:
            doc_url: Google Docs URL containing TPO audio links
            tpo_range: TPO range to scrape (start, end)
            
        Returns:
            Dictionary with scraping results and statistics
        """
        stats = {
            'scraped_urls': 0,
            'new_mappings': 0,
            'updated_mappings': 0,
            'errors': 0,
            'tpo_range': tpo_range,
            'urls_found': {}
        }
        
        try:
            self.logger.info(f"Scraping Google Docs for TPO{tpo_range[0]}-{tpo_range[1]}: {doc_url}")
            
            # Convert Google Docs URL to export format for plain text access
            export_url = self._convert_to_export_url(doc_url)
            
            response = self.session.get(export_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse document content
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            
            # Extract URLs using multiple patterns
            extracted_urls = self._extract_tpo_urls_from_text(text_content, tpo_range)
            
            stats['urls_found'] = extracted_urls
            stats['scraped_urls'] = len(extracted_urls)
            
            # Store extracted URLs in database
            for content_name, url in extracted_urls.items():
                try:
                    result = self._store_scraped_url(content_name, url, 'google_docs')
                    if result['created']:
                        stats['new_mappings'] += 1
                    elif result['updated']:
                        stats['updated_mappings'] += 1
                        
                except Exception as e:
                    stats['errors'] += 1
                    self.logger.error(f"Error storing {content_name}: {e}")
            
            db.session.commit()
            self.logger.info(f"Scraping complete: {stats}")
            
        except Exception as e:
            stats['errors'] += 1
            self.logger.error(f"Google Docs scraping failed: {e}")
            db.session.rollback()
        
        return stats

    def scrape_koocdn_pattern_urls(self, tpo_range: Tuple[int, int] = (1, 200)) -> Dict:
        """
        Generate and validate koocdn.com pattern URLs
        
        Args:
            tpo_range: TPO range to generate URLs for
            
        Returns:
            Dictionary with generation and validation results
        """
        stats = {
            'generated_urls': 0,
            'valid_urls': 0,
            'invalid_urls': 0,
            'new_mappings': 0,
            'errors': 0
        }
        
        try:
            for tpo_num in range(tpo_range[0], tpo_range[1] + 1):
                for section in [1, 2]:
                    for part in [1, 2, 3]:
                        try:
                            # Generate potential koocdn URLs
                            potential_urls = self._generate_koocdn_urls(tpo_num, section, part)
                            
                            for url in potential_urls:
                                stats['generated_urls'] += 1
                                
                                # Validate URL
                                if self.resolver._validate_url(url):
                                    stats['valid_urls'] += 1
                                    
                                    # Store valid URL
                                    result = self._store_discovered_url(
                                        tpo_num, section, part, url, 'koocdn_pattern'
                                    )
                                    if result['created']:
                                        stats['new_mappings'] += 1
                                        
                                    break  # Found working URL, no need to try others
                                else:
                                    stats['invalid_urls'] += 1
                            
                            # Rate limiting
                            time.sleep(self.request_delay)
                            
                        except Exception as e:
                            stats['errors'] += 1
                            self.logger.error(f"Error processing TPO{tpo_num} S{section}P{part}: {e}")
            
            db.session.commit()
            self.logger.info(f"Koocdn pattern scraping complete: {stats}")
            
        except Exception as e:
            stats['errors'] += 1
            self.logger.error(f"Koocdn pattern scraping failed: {e}")
            db.session.rollback()
        
        return stats

    def scrape_tikustorage_urls(self, tpo_range: Tuple[int, int] = (1, 75)) -> Dict:
        """
        Validate and store tikustorage URLs
        
        Args:
            tpo_range: TPO range to validate
            
        Returns:
            Dictionary with validation results
        """
        stats = {
            'checked_urls': 0,
            'valid_urls': 0,
            'invalid_urls': 0,
            'new_mappings': 0,
            'errors': 0
        }
        
        try:
            for tpo_num in range(tpo_range[0], tpo_range[1] + 1):
                for section in [1, 2]:
                    for part in [1, 2, 3]:
                        try:
                            # Generate tikustorage URL
                            url = f"https://tikustorage-sh.oss-cn-shanghai.aliyuncs.com/TPO_Audio/tpo{tpo_num}/tpo{tpo_num}_listening_passage{section}_{part}.mp3"
                            stats['checked_urls'] += 1
                            
                            # Validate URL
                            if self.resolver._validate_url(url):
                                stats['valid_urls'] += 1
                                
                                # Store valid URL
                                result = self._store_discovered_url(
                                    tpo_num, section, part, url, 'tikustorage'
                                )
                                if result['created']:
                                    stats['new_mappings'] += 1
                            else:
                                stats['invalid_urls'] += 1
                            
                            # Rate limiting
                            time.sleep(self.request_delay)
                            
                        except Exception as e:
                            stats['errors'] += 1
                            self.logger.error(f"Error processing TPO{tpo_num} S{section}P{part}: {e}")
            
            db.session.commit()
            self.logger.info(f"Tikustorage validation complete: {stats}")
            
        except Exception as e:
            stats['errors'] += 1
            self.logger.error(f"Tikustorage validation failed: {e}")
            db.session.rollback()
        
        return stats

    def comprehensive_tpo_scan(self, tpo_range: Tuple[int, int] = (35, 75)) -> Dict:
        """
        Comprehensive scan of all TPO sources
        
        Args:
            tpo_range: TPO range to scan
            
        Returns:
            Combined statistics from all sources
        """
        combined_stats = {
            'total_scanned': 0,
            'total_found': 0,
            'total_new': 0,
            'source_results': {},
            'start_time': datetime.utcnow(),
            'end_time': None
        }
        
        try:
            self.logger.info(f"Starting comprehensive TPO scan for range {tpo_range}")
            
            # 1. Validate tikustorage URLs (most reliable)
            self.logger.info("Phase 1: Validating tikustorage URLs...")
            tikustorage_stats = self.scrape_tikustorage_urls(tpo_range)
            combined_stats['source_results']['tikustorage'] = tikustorage_stats
            
            # 2. Try koocdn pattern generation
            self.logger.info("Phase 2: Generating koocdn pattern URLs...")
            koocdn_stats = self.scrape_koocdn_pattern_urls(tpo_range)
            combined_stats['source_results']['koocdn'] = koocdn_stats
            
            # 3. Archive.org URLs
            self.logger.info("Phase 3: Validating Archive.org URLs...")
            archive_stats = self._validate_archive_org_urls(tpo_range)
            combined_stats['source_results']['archive_org'] = archive_stats
            
            # Calculate totals
            for source_stats in combined_stats['source_results'].values():
                combined_stats['total_scanned'] += source_stats.get('checked_urls', 0) + source_stats.get('generated_urls', 0)
                combined_stats['total_found'] += source_stats.get('valid_urls', 0)
                combined_stats['total_new'] += source_stats.get('new_mappings', 0)
            
            combined_stats['end_time'] = datetime.utcnow()
            duration = (combined_stats['end_time'] - combined_stats['start_time']).total_seconds()
            
            self.logger.info(f"Comprehensive scan complete in {duration:.1f}s: {combined_stats}")
            
        except Exception as e:
            self.logger.error(f"Comprehensive scan failed: {e}")
            combined_stats['error'] = str(e)
        
        return combined_stats

    def _convert_to_export_url(self, doc_url: str) -> str:
        """Convert Google Docs URL to export format"""
        # Extract document ID from various Google Docs URL formats
        doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', doc_url)
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            return f"https://docs.google.com/document/d/{doc_id}/export?format=html"
        return doc_url

    def _extract_tpo_urls_from_text(self, text: str, tpo_range: Tuple[int, int]) -> Dict[str, str]:
        """Extract TPO URLs from document text"""
        urls_found = {}
        
        # Multiple URL patterns to match
        patterns = [
            # koocdn.com pattern
            r'(https://ti\.koocdn\.com/upload/ti/[^\s"\'<>]+\.mp3)',
            # tikustorage pattern
            r'(https://tikustorage[^\s"\'<>]+\.mp3)',
            # Archive.org pattern
            r'(https://archive\.org/download/[^\s"\'<>]+\.mp3)',
            # General mp3 URLs
            r'(https?://[^\s"\'<>]+\.mp3)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for url in matches:
                # Try to associate URL with TPO content
                content_name = self._guess_tpo_content_from_url(url, tpo_range)
                if content_name:
                    urls_found[content_name] = url
        
        # Also look for structured content patterns
        # Pattern: "TPO XX Section Y Passage Z: URL"
        structured_pattern = r'TPO\s*(\d+)\s*Section\s*(\d+)\s*Passage\s*(\d+)[:\s]+(https?://[^\s"\'<>]+\.mp3)'
        structured_matches = re.findall(structured_pattern, text, re.IGNORECASE)
        
        for match in structured_matches:
            tpo_num, section, part, url = match
            tpo_num = int(tpo_num)
            
            if tpo_range[0] <= tpo_num <= tpo_range[1]:
                content_name = f"TPO {tpo_num} Section {section} Passage {part}"
                urls_found[content_name] = url
        
        return urls_found

    def _guess_tpo_content_from_url(self, url: str, tpo_range: Tuple[int, int]) -> Optional[str]:
        """Guess TPO content name from URL pattern"""
        # Extract TPO number from URL
        tpo_match = re.search(r'tpo[\s_-]*(\d+)', url, re.IGNORECASE)
        if not tpo_match:
            return None
        
        tpo_num = int(tpo_match.group(1))
        if not (tpo_range[0] <= tpo_num <= tpo_range[1]):
            return None
        
        # Try to extract section and part information
        section_match = re.search(r'(?:section|passage)[\s_-]*(\d+)', url, re.IGNORECASE)
        part_match = re.search(r'(?:part|_)(\d+)(?:\.mp3|$)', url, re.IGNORECASE)
        
        section = int(section_match.group(1)) if section_match else 1
        part = int(part_match.group(1)) if part_match else 1
        
        return f"TPO {tpo_num} Section {section} Passage {part}"

    def _generate_koocdn_urls(self, tpo_num: int, section: int, part: int) -> List[str]:
        """Generate potential koocdn URLs based on patterns"""
        urls = []
        
        # Common hash patterns observed in existing URLs
        base_patterns = [
            "https://ti.koocdn.com/upload/ti/2423000-2424000/{hash}.mp3",
            "https://ti.koocdn.com/upload/ti/2422000-2423000/{hash}.mp3",
            "https://ti.koocdn.com/upload/ti/2334000-2335000/{hash}.mp3"
        ]
        
        # Generate potential hashes (this would need real data to be accurate)
        # For now, return empty list as we don't have the hash patterns
        return urls

    def _validate_archive_org_urls(self, tpo_range: Tuple[int, int]) -> Dict:
        """Validate Archive.org TPO URLs"""
        stats = {
            'checked_urls': 0,
            'valid_urls': 0,
            'invalid_urls': 0,
            'new_mappings': 0,
            'errors': 0
        }
        
        part_names = ['Con1', 'Lec1', 'Lec2', 'Con2', 'Lec3']
        
        for tpo_num in range(tpo_range[0], tpo_range[1] + 1):
            for i, part_name in enumerate(part_names):
                try:
                    url = f"https://archive.org/download/toefl-practice-listening/TPO_{tpo_num:02d}_{part_name}.mp3"
                    stats['checked_urls'] += 1
                    
                    if self.resolver._validate_url(url):
                        stats['valid_urls'] += 1
                        
                        # Calculate section and part from part name
                        section = 1 if i < 3 else 2
                        part = (i % 3) + 1
                        
                        result = self._store_discovered_url(
                            tpo_num, section, part, url, 'archive_org'
                        )
                        if result['created']:
                            stats['new_mappings'] += 1
                    else:
                        stats['invalid_urls'] += 1
                    
                    time.sleep(self.request_delay)
                    
                except Exception as e:
                    stats['errors'] += 1
                    self.logger.error(f"Error validating Archive.org URL for TPO{tpo_num} {part_name}: {e}")
        
        return stats

    def _store_scraped_url(self, content_name: str, url: str, source: str) -> Dict:
        """Store scraped URL in database"""
        result = {'created': False, 'updated': False}
        
        # Parse TPO info from content name
        tpo_info = self.resolver._parse_tpo_info(content_name)
        if not tpo_info:
            return result
        
        tpo_number, section, part = tpo_info
        return self._store_discovered_url(tpo_number, section, part, url, source)

    def _store_discovered_url(self, tpo_number: int, section: int, part: int, 
                            url: str, source: str) -> Dict:
        """Store discovered URL in database"""
        result = {'created': False, 'updated': False}
        
        try:
            # Check if mapping already exists
            existing = TPOAudioMap.query.filter_by(
                tpo_number=tpo_number, section=section, part=part
            ).first()
            
            if existing:
                # Update existing mapping if URL is different or better source
                if existing.primary_url != url:
                    if existing.fallback_urls is None:
                        existing.fallback_urls = []
                    
                    # Add current primary_url to fallbacks if not already there
                    if existing.primary_url not in existing.fallback_urls:
                        existing.fallback_urls.append(existing.primary_url)
                    
                    # Update primary URL
                    existing.primary_url = url
                    existing.source_provider = source
                    existing.url_status = 'valid'
                    existing.last_validated = datetime.utcnow()
                    existing.updated_at = datetime.utcnow()
                    
                    result['updated'] = True
            else:
                # Create new mapping
                content_type = 'conversation' if part == 1 else 'lecture'
                
                audio_map = TPOAudioMap(
                    tpo_number=tpo_number,
                    section=section,
                    part=part,
                    content_type=content_type,
                    primary_url=url,
                    source_provider=source,
                    url_status='valid',
                    last_validated=datetime.utcnow(),
                    fallback_urls=[]
                )
                db.session.add(audio_map)
                result['created'] = True
            
        except Exception as e:
            self.logger.error(f"Error storing URL mapping: {e}")
        
        return result

    def export_mappings_to_json(self, filepath: str) -> Dict:
        """Export current TPO audio mappings to JSON file"""
        try:
            mappings = TPOAudioMap.query.all()
            
            export_data = {
                'export_timestamp': datetime.utcnow().isoformat(),
                'total_mappings': len(mappings),
                'mappings': []
            }
            
            for mapping in mappings:
                export_data['mappings'].append({
                    'tpo_number': mapping.tpo_number,
                    'section': mapping.section,
                    'part': mapping.part,
                    'content_type': mapping.content_type,
                    'primary_url': mapping.primary_url,
                    'fallback_urls': mapping.fallback_urls,
                    'url_status': mapping.url_status,
                    'source_provider': mapping.source_provider,
                    'title': mapping.title,
                    'topic': mapping.topic,
                    'last_validated': mapping.last_validated.isoformat() if mapping.last_validated else None
                })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'exported_count': len(mappings),
                'filepath': filepath
            }
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Convenience functions for manual usage
def run_bulk_import():
    """Import existing GOOGLE_DOCS_TPO_URLS into database"""
    resolver = TPOAudioResolver()
    return resolver.bulk_import_legacy_urls()

def run_comprehensive_scan(tpo_range: Tuple[int, int] = (35, 75)):
    """Run comprehensive TPO URL scan"""
    scraper = TPOBulkScraper()
    return scraper.comprehensive_tpo_scan(tpo_range)

def validate_all_tpo_urls(limit: int = None):
    """Validate all TPO URLs in database"""
    resolver = TPOAudioResolver()
    return resolver.validate_all_urls(limit)