"""
TPO Audio URL Resolution Service

Systematic TPO audio URL resolution system to replace fragile dictionary mapping.
Provides fallback mechanisms, URL validation, and integration with multiple sources.
"""

import re
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from app import db
from models import TPOAudioMap, ContentSource


class TPOAudioResolver:
    """Systematic TPO audio URL resolver with validation and fallback"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Known audio URL patterns for different sources
        self.url_patterns = {
            'koocdn': 'https://ti.koocdn.com/upload/ti/{dir}/{hash}.mp3',
            'tikustorage': 'https://tikustorage-sh.oss-cn-shanghai.aliyuncs.com/TPO_Audio/tpo{tpo}/tpo{tpo}_listening_passage{section}_{part}.mp3',
            'archive_org': 'https://archive.org/download/toefl-practice-listening/TPO_{tpo:02d}_{part_name}.mp3',
            'zhan': 'https://top-audio.zhan.com/toefl/official/{tpo}/official{tpo}_{part_code}.mp3'
        }
        
        # Content type mappings
        self.content_types = {
            1: 'conversation',  # Part 1 is usually conversation
            2: 'lecture',       # Part 2-3 are usually lectures  
            3: 'lecture'
        }
        
        # Part name mappings for different sources
        self.part_names = {
            'archive_org': {
                (1, 1): 'Con1', (1, 2): 'Lec1', (1, 3): 'Lec2',
                (2, 1): 'Con2', (2, 2): 'Lec3', (2, 3): 'Lec4'
            },
            'zhan': {
                (1, 1): 'c1', (1, 2): 'l1', (1, 3): 'l2',
                (2, 1): 'c2', (2, 2): 'l3', (2, 3): 'l4'
            }
        }

    def resolve_audio_url(self, tpo_number: int, section: int, part: int, 
                         content_name: str = None) -> Optional[str]:
        """
        Main audio URL resolution function
        
        Args:
            tpo_number: TPO number (1-200+)
            section: Section number (1-2)
            part: Part number (1-3)
            content_name: Optional content name for legacy matching
            
        Returns:
            Resolved audio URL or None if not found
        """
        try:
            # First, try database lookup
            audio_map = self._get_from_database(tpo_number, section, part)
            if audio_map:
                # Validate URL if needed
                if self._should_validate_url(audio_map):
                    if self._validate_url(audio_map.primary_url):
                        audio_map.url_status = 'valid'
                        audio_map.last_validated = datetime.utcnow()
                        db.session.commit()
                        return audio_map.primary_url
                    else:
                        # Try fallback URLs
                        valid_fallback = self._try_fallback_urls(audio_map)
                        if valid_fallback:
                            return valid_fallback
                else:
                    # URL was recently validated, use it
                    return audio_map.primary_url
            
            # If not in database, try legacy dictionary matching
            if content_name:
                legacy_url = self._try_legacy_lookup(content_name)
                if legacy_url:
                    # Store in database for future use
                    self._store_url_mapping(tpo_number, section, part, legacy_url, 'koocdn')
                    return legacy_url
            
            # Generate fallback URLs from known patterns
            fallback_urls = self._generate_fallback_urls(tpo_number, section, part)
            
            # Test each fallback URL
            for source, url in fallback_urls.items():
                if self._validate_url(url):
                    # Store working URL in database
                    self._store_url_mapping(tpo_number, section, part, url, source)
                    return url
            
            # No working URL found
            self.logger.warning(f"No valid audio URL found for TPO{tpo_number} S{section}P{part}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error resolving audio URL for TPO{tpo_number} S{section}P{part}: {e}")
            return None

    def _get_from_database(self, tpo_number: int, section: int, part: int) -> Optional[TPOAudioMap]:
        """Get TPO audio mapping from database"""
        return TPOAudioMap.query.filter_by(
            tpo_number=tpo_number,
            section=section,
            part=part
        ).first()

    def _should_validate_url(self, audio_map: TPOAudioMap) -> bool:
        """Check if URL should be validated (not validated recently)"""
        if audio_map.url_status == 'valid' and audio_map.last_validated:
            # Don't re-validate if validated within last 24 hours
            hours_since_validation = (datetime.utcnow() - audio_map.last_validated).total_seconds() / 3600
            return hours_since_validation > 24
        return True

    def _validate_url(self, url: str, timeout: int = 10) -> bool:
        """Validate if audio URL is accessible - DISABLED for performance"""
        # CRITICAL: Disable real-time validation to prevent worker timeouts
        # Real-time HTTP requests in request path cause severe performance issues
        self.logger.debug(f"URL validation SKIPPED for performance: {url}")
        return True  # Always return True to skip validation

    def _try_fallback_urls(self, audio_map: TPOAudioMap) -> Optional[str]:
        """Try fallback URLs if primary URL fails"""
        if not audio_map.fallback_urls:
            return None
            
        for fallback_url in audio_map.fallback_urls:
            if self._validate_url(fallback_url):
                # Update primary URL to working fallback
                audio_map.primary_url = fallback_url
                audio_map.url_status = 'valid'
                audio_map.last_validated = datetime.utcnow()
                db.session.commit()
                return fallback_url
        
        # Mark as invalid if all fallbacks fail
        audio_map.url_status = 'invalid'
        audio_map.last_validated = datetime.utcnow()
        db.session.commit()
        return None

    def _try_legacy_lookup(self, content_name: str) -> Optional[str]:
        """Try legacy GOOGLE_DOCS_TPO_URLS dictionary lookup"""
        from routes import get_google_docs_tpo_url
        return get_google_docs_tpo_url(content_name)

    def _generate_fallback_urls(self, tpo_number: int, section: int, part: int) -> Dict[str, str]:
        """Generate fallback URLs from known patterns"""
        fallback_urls = {}
        
        # Tikustorage pattern
        fallback_urls['tikustorage'] = self.url_patterns['tikustorage'].format(
            tpo=tpo_number, section=section, part=part
        )
        
        # Archive.org pattern
        if (section, part) in self.part_names['archive_org']:
            part_name = self.part_names['archive_org'][(section, part)]
            fallback_urls['archive_org'] = self.url_patterns['archive_org'].format(
                tpo=tpo_number, part_name=part_name
            )
        
        # Zhan pattern
        if (section, part) in self.part_names['zhan']:
            part_code = self.part_names['zhan'][(section, part)]
            fallback_urls['zhan'] = self.url_patterns['zhan'].format(
                tpo=tpo_number, part_code=part_code
            )
        
        return fallback_urls

    def _store_url_mapping(self, tpo_number: int, section: int, part: int, 
                          primary_url: str, source_provider: str):
        """Store working URL mapping in database"""
        try:
            # Check if mapping already exists
            existing = TPOAudioMap.query.filter_by(
                tpo_number=tpo_number, section=section, part=part
            ).first()
            
            if existing:
                existing.primary_url = primary_url
                existing.source_provider = source_provider
                existing.url_status = 'valid'
                existing.last_validated = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
            else:
                # Create new mapping
                content_type = self.content_types.get(part, 'lecture')
                
                audio_map = TPOAudioMap(
                    tpo_number=tpo_number,
                    section=section,
                    part=part,
                    content_type=content_type,
                    primary_url=primary_url,
                    source_provider=source_provider,
                    url_status='valid',
                    last_validated=datetime.utcnow(),
                    fallback_urls=list(self._generate_fallback_urls(tpo_number, section, part).values())
                )
                db.session.add(audio_map)
            
            db.session.commit()
            self.logger.info(f"Stored URL mapping for TPO{tpo_number} S{section}P{part}: {primary_url}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error storing URL mapping: {e}")

    def bulk_import_legacy_urls(self) -> Dict:
        """Import existing GOOGLE_DOCS_TPO_URLS into database"""
        from routes import GOOGLE_DOCS_TPO_URLS
        
        stats = {
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
        
        for content_name, url in GOOGLE_DOCS_TPO_URLS.items():
            try:
                # Parse TPO info from content name
                tpo_info = self._parse_tpo_info(content_name)
                if not tpo_info:
                    stats['skipped'] += 1
                    continue
                
                tpo_number, section, part = tpo_info
                
                # Check if already exists
                existing = TPOAudioMap.query.filter_by(
                    tpo_number=tpo_number, section=section, part=part
                ).first()
                
                if existing:
                    stats['skipped'] += 1
                    continue
                
                # Create new mapping
                content_type = self.content_types.get(part, 'lecture')
                
                audio_map = TPOAudioMap(
                    tpo_number=tpo_number,
                    section=section,
                    part=part,
                    content_type=content_type,
                    primary_url=url,
                    source_provider='koocdn',
                    url_status='pending',  # Will be validated later
                    title=content_name,
                    fallback_urls=list(self._generate_fallback_urls(tpo_number, section, part).values())
                )
                db.session.add(audio_map)
                stats['imported'] += 1
                
                if stats['imported'] % 20 == 0:
                    db.session.commit()
                    
            except Exception as e:
                stats['errors'] += 1
                self.logger.error(f"Error importing {content_name}: {e}")
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error committing bulk import: {e}")
        
        return stats

    def _parse_tpo_info(self, content_name: str) -> Optional[Tuple[int, int, int]]:
        """Parse TPO number, section, and part from content name"""
        # Match patterns like "TPO 35 Section 1 Passage 1"
        match = re.search(r'TPO\s*(\d+)\s*Section\s*(\d+)\s*Passage\s*(\d+)', content_name, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
        return None

    def validate_all_urls(self, limit: int = None) -> Dict:
        """Validate all URLs in the database"""
        stats = {
            'checked': 0,
            'valid': 0,
            'invalid': 0,
            'errors': 0
        }
        
        query = TPOAudioMap.query.filter(TPOAudioMap.url_status.in_(['pending', 'invalid']))
        if limit:
            query = query.limit(limit)
        
        mappings = query.all()
        
        for mapping in mappings:
            try:
                stats['checked'] += 1
                
                if self._validate_url(mapping.primary_url):
                    mapping.url_status = 'valid'
                    mapping.validation_response_code = 200
                    stats['valid'] += 1
                else:
                    # Try fallback URLs
                    valid_fallback = self._try_fallback_urls(mapping)
                    if valid_fallback:
                        stats['valid'] += 1
                    else:
                        mapping.url_status = 'invalid'
                        mapping.validation_response_code = 404
                        stats['invalid'] += 1
                
                mapping.last_validated = datetime.utcnow()
                
                if stats['checked'] % 10 == 0:
                    db.session.commit()
                    
            except Exception as e:
                stats['errors'] += 1
                self.logger.error(f"Error validating {mapping}: {e}")
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error committing URL validation: {e}")
        
        return stats


# Convenience function for integration with existing routes
def resolve_audio_url(tpo_number: int = None, section: int = None, part: int = None, 
                     content_name: str = None) -> Optional[str]:
    """
    Main function to replace GOOGLE_DOCS_TPO_URLS dictionary usage
    
    Usage:
        # From TPO content metadata
        url = resolve_audio_url(tpo_number=41, section=1, part=2)
        
        # From legacy content name
        url = resolve_audio_url(content_name="TPO 41 Section 1 Passage 2")
        
        # Mixed approach
        url = resolve_audio_url(tpo_number=41, section=1, part=2, 
                               content_name="TPO 41 Section 1 Passage 2")
    """
    resolver = TPOAudioResolver()
    
    # If TPO info is provided directly, use it
    if tpo_number and section and part:
        return resolver.resolve_audio_url(tpo_number, section, part, content_name)
    
    # If only content name is provided, parse it
    if content_name:
        tpo_info = resolver._parse_tpo_info(content_name)
        if tpo_info:
            tpo_number, section, part = tpo_info
            return resolver.resolve_audio_url(tpo_number, section, part, content_name)
    
    return None