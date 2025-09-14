#!/usr/bin/env python3
"""
Database Table Updater

Updates the tpo_audio_map database table with new TPO35-46 mappings.
Safely handles existing data and provides rollback capability.
"""

import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# Add current directory to path to import Flask app
sys.path.insert(0, os.getcwd())

try:
    from app import app, db
    from models import TPOAudioMap
    from sqlalchemy.exc import IntegrityError
except ImportError as e:
    print(f"❌ Error importing Flask app: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

logger = logging.getLogger(__name__)

class DatabaseUpdater:
    """Updates tpo_audio_map database table with new mappings"""
    
    def __init__(self):
        self.app = app
        self.db = db
        
    def get_existing_mappings(self, tpo_range: Tuple[int, int] = (35, 46)) -> List[TPOAudioMap]:
        """Get existing TPO mappings from database"""
        with self.app.app_context():
            return TPOAudioMap.query.filter(
                TPOAudioMap.tpo_number.between(tpo_range[0], tpo_range[1])
            ).all()
    
    def parse_key_to_components(self, key: str) -> Optional[Tuple[int, int, int, str]]:
        """Parse TPO key into components (tpo_number, section, part, content_type)"""
        match = re.match(r'TPO (\d+) Section (\d+) Passage (\d+)', key)
        if not match:
            return None
        
        tpo_num = int(match.group(1))
        section = int(match.group(2))
        part = int(match.group(3))
        
        # Determine content type (conversation for part 1, lecture for parts 2-3)
        content_type = 'conversation' if part == 1 else 'lecture'
        
        return tpo_num, section, part, content_type
    
    def create_mapping_record(self, key: str, url: str) -> Optional[TPOAudioMap]:
        """Create a new TPOAudioMap record from key and URL"""
        components = self.parse_key_to_components(key)
        if not components:
            logger.error(f"Could not parse key: {key}")
            return None
        
        tpo_num, section, part, content_type = components
        
        # Create new record
        record = TPOAudioMap(
            tpo_number=tpo_num,
            section=section,
            part=part,
            content_type=content_type,
            primary_url=url,
            url_status='valid',
            source_provider='koocdn',
            title=f"TPO {tpo_num} Section {section} Part {part}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return record
    
    def backup_existing_data(self) -> str:
        """Create backup of existing TPO35-46 data"""
        with self.app.app_context():
            existing = self.get_existing_mappings()
            
            backup_file = f"tpo_audio_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            with open(backup_file, 'w') as f:
                f.write("-- TPO Audio Map Backup\n")
                f.write(f"-- Created: {datetime.now()}\n")
                f.write("-- Backup of TPO35-46 mappings before update\n\n")
                
                for record in existing:
                    f.write(f"INSERT INTO tpo_audio_map (tpo_number, section, part, content_type, primary_url, url_status, source_provider, title, created_at, updated_at) VALUES ")
                    f.write(f"({record.tpo_number}, {record.section}, {record.part}, '{record.content_type}', '{record.primary_url}', '{record.url_status}', '{record.source_provider}', '{record.title}', '{record.created_at}', '{record.updated_at}');\n")
            
            logger.info(f"Backup created: {backup_file}")
            return backup_file
    
    def update_mappings(self, new_mappings: Dict[str, str], dry_run: bool = True) -> bool:
        """
        Update database with new mappings
        
        Args:
            new_mappings: Dictionary of TPO keys to URLs
            dry_run: If True, show changes without modifying database
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.app.app_context():
                # Filter for TPO35-46 only
                filtered_mappings = {k: v for k, v in new_mappings.items() 
                                   if re.match(r'TPO (3[5-9]|4[0-6]) Section', k)}
                
                if not filtered_mappings:
                    logger.warning("No TPO35-46 mappings found in input")
                    return True
                
                # Get existing mappings
                existing = self.get_existing_mappings()
                existing_keys = set()
                
                for record in existing:
                    key = f"TPO {record.tpo_number} Section {record.section} Passage {record.part}"
                    existing_keys.add(key)
                
                # Determine what to add, update, or skip
                to_add = []
                to_update = []
                to_skip = []
                
                for key, url in filtered_mappings.items():
                    if key in existing_keys:
                        # Find existing record to check if URL is different
                        components = self.parse_key_to_components(key)
                        if components:
                            tpo_num, section, part, _ = components
                            existing_record = TPOAudioMap.query.filter_by(
                                tpo_number=tpo_num, section=section, part=part
                            ).first()
                            
                            if existing_record and existing_record.primary_url != url:
                                to_update.append((existing_record, url))
                            else:
                                to_skip.append(key)
                    else:
                        new_record = self.create_mapping_record(key, url)
                        if new_record:
                            to_add.append(new_record)
                
                if dry_run:
                    logger.info("DRY RUN: Database changes that would be made:")
                    logger.info(f"  Records to add: {len(to_add)}")
                    for record in to_add:
                        logger.info(f"    Add: TPO {record.tpo_number} S{record.section}P{record.part} -> {record.primary_url}")
                    
                    logger.info(f"  Records to update: {len(to_update)}")
                    for record, new_url in to_update:
                        logger.info(f"    Update: TPO {record.tpo_number} S{record.section}P{record.part} -> {new_url}")
                    
                    logger.info(f"  Records to skip (no change): {len(to_skip)}")
                    return True
                
                # Create backup before making changes
                backup_file = self.backup_existing_data()
                
                # Execute changes
                changes_made = 0
                
                # Add new records
                for record in to_add:
                    try:
                        self.db.session.add(record)
                        changes_made += 1
                        logger.info(f"Added: TPO {record.tpo_number} S{record.section}P{record.part}")
                    except IntegrityError as e:
                        logger.error(f"Integrity error adding record: {e}")
                        self.db.session.rollback()
                        return False
                
                # Update existing records
                for record, new_url in to_update:
                    try:
                        old_url = record.primary_url
                        record.primary_url = new_url
                        record.updated_at = datetime.utcnow()
                        record.url_status = 'valid'  # Mark as valid since it's a new URL
                        changes_made += 1
                        logger.info(f"Updated: TPO {record.tpo_number} S{record.section}P{record.part}")
                        logger.info(f"  Old: {old_url}")
                        logger.info(f"  New: {new_url}")
                    except Exception as e:
                        logger.error(f"Error updating record: {e}")
                        self.db.session.rollback()
                        return False
                
                # Commit all changes
                self.db.session.commit()
                
                logger.info(f"✅ Database update completed successfully")
                logger.info(f"   Total changes: {changes_made}")
                logger.info(f"   Backup file: {backup_file}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating database: {str(e)}")
            self.db.session.rollback()
            return False
    
    def verify_coverage(self) -> Dict[str, List[str]]:
        """Verify TPO35-46 coverage in database"""
        with self.app.app_context():
            existing = self.get_existing_mappings()
            
            found_segments = set()
            for record in existing:
                found_segments.add((record.tpo_number, record.section, record.part))
            
            # Expected segments for TPO35-46
            expected_segments = set()
            for tpo in range(35, 47):
                for section in [1, 2]:
                    for part in [1, 2, 3]:
                        expected_segments.add((tpo, section, part))
            
            missing_segments = expected_segments - found_segments
            complete_segments = expected_segments & found_segments
            
            return {
                'complete': [f"TPO {t} Section {s} Passage {p}" for t, s, p in sorted(complete_segments)],
                'missing': [f"TPO {t} Section {s} Passage {p}" for t, s, p in sorted(missing_segments)],
                'total_expected': len(expected_segments),
                'total_found': len(complete_segments)
            }


def update_database_with_mappings(mappings: Dict[str, str], dry_run: bool = True) -> bool:
    """
    Convenience function to update database with new mappings
    
    Args:
        mappings: Dictionary of TPO keys to URLs
        dry_run: If True, show changes without modifying database
        
    Returns:
        True if successful, False otherwise
    """
    updater = DatabaseUpdater()
    return updater.update_mappings(mappings, dry_run)


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Update tpo_audio_map database table')
    parser.add_argument('--mappings', '-m', help='JSON file with new mappings', required=True)
    parser.add_argument('--dry-run', action='store_true', help='Show changes without modifying database')
    parser.add_argument('--execute', action='store_true', help='Execute the updates')
    parser.add_argument('--verify', action='store_true', help='Verify coverage after update')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("Error: Please specify either --dry-run or --execute")
        sys.exit(1)
    
    try:
        with open(args.mappings, 'r') as f:
            mappings = json.load(f)
        
        updater = DatabaseUpdater()
        success = updater.update_mappings(mappings, dry_run=args.dry_run)
        
        if success:
            print("✅ Database update completed successfully")
            
            if args.verify:
                coverage = updater.verify_coverage()
                print(f"\nCoverage Report:")
                print(f"  Found: {coverage['total_found']}/{coverage['total_expected']} segments")
                if coverage['missing']:
                    print(f"  Missing segments: {len(coverage['missing'])}")
                    for missing in coverage['missing'][:5]:  # Show first 5
                        print(f"    - {missing}")
                    if len(coverage['missing']) > 5:
                        print(f"    ... and {len(coverage['missing']) - 5} more")
        else:
            print("❌ Database update failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)