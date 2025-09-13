#!/usr/bin/env python3
"""
Test script for the new TPO Audio URL Resolution System

This script tests the new TPO audio resolution system and imports legacy data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from services.tpo_audio_resolver import TPOAudioResolver, resolve_audio_url
from services.tpo_bulk_scraper import TPOBulkScraper, run_bulk_import
from models import TPOAudioMap, ContentSource
import logging

logging.basicConfig(level=logging.INFO)

def test_tpo_audio_resolution():
    """Test the TPO audio resolution system"""
    
    with app.app_context():
        print("🧪 Testing TPO Audio Resolution System")
        print("=" * 50)
        
        # 1. Import legacy GOOGLE_DOCS_TPO_URLS data
        print("\n📥 Importing legacy TPO URLs...")
        resolver = TPOAudioResolver()
        import_stats = resolver.bulk_import_legacy_urls()
        print(f"✅ Import complete: {import_stats}")
        
        # 2. Test resolve_audio_url function with various cases
        print("\n🔍 Testing URL resolution...")
        
        test_cases = [
            # TPO 35-75 range (should find URLs)
            {"tpo": 35, "section": 1, "part": 1, "name": "TPO 35 Section 1 Passage 1"},
            {"tpo": 36, "section": 1, "part": 2, "name": "TPO 36 Section 1 Passage 2"},
            {"tpo": 75, "section": 2, "part": 1, "name": "TPO 75 Section 2 Passage 1"},
            
            # Content name only
            {"name": "TPO 40 Section 1 Passage 1"},
            
            # TPO outside range (should generate fallback)
            {"tpo": 41, "section": 1, "part": 1, "name": "TPO 41 Section 1 Passage 1"},
            {"tpo": 50, "section": 2, "part": 2, "name": "TPO 50 Section 2 Passage 2"},
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test}")
            
            if test.get('tpo'):
                url = resolve_audio_url(
                    tpo_number=test['tpo'],
                    section=test['section'],
                    part=test['part'],
                    content_name=test.get('name')
                )
            else:
                url = resolve_audio_url(content_name=test['name'])
            
            if url:
                print(f"   ✅ Resolved: {url}")
            else:
                print(f"   ❌ No URL found")
        
        # 3. Check database state
        print(f"\n📊 Database Statistics:")
        total_mappings = TPOAudioMap.query.count()
        valid_mappings = TPOAudioMap.query.filter_by(url_status='valid').count()
        pending_mappings = TPOAudioMap.query.filter_by(url_status='pending').count()
        
        print(f"   Total mappings: {total_mappings}")
        print(f"   Valid mappings: {valid_mappings}")
        print(f"   Pending validation: {pending_mappings}")
        
        # 4. Test with actual database content
        print(f"\n🎯 Testing with actual TPO content from database...")
        
        # Find some TPO41-75 content
        tpo_content = ContentSource.query.filter(
            ContentSource.type == 'smallstation_tpo',
            ContentSource.name.like('%TPO 4%')
        ).limit(5).all()
        
        for content in tpo_content:
            print(f"\n   Testing: {content.name} (ID: {content.id})")
            print(f"   Original URL: {content.url}")
            
            # Try to resolve with new system
            import re
            tpo_match = re.search(r'TPO (\d+)', content.name)
            section_match = re.search(r'Section\s*(\d+)', content.name)
            part_match = re.search(r'Section\d+\-(\d+)', content.name)
            
            if tpo_match and section_match and part_match:
                tpo_num = int(tpo_match.group(1))
                section = int(section_match.group(1))
                part = int(part_match.group(1))
                
                new_url = resolve_audio_url(
                    tpo_number=tpo_num, 
                    section=section, 
                    part=part, 
                    content_name=content.name
                )
                
                if new_url:
                    print(f"   ✅ New resolver: {new_url}")
                    if new_url != content.url:
                        print(f"   📝 URL would be updated!")
                else:
                    print(f"   ❌ New resolver: No URL found")
            else:
                print(f"   ⚠️ Could not parse content name format")
        
        print(f"\n🎉 Test complete!")

def validate_sample_urls():
    """Validate a sample of URLs to test the validation system"""
    
    with app.app_context():
        print("\n🔗 Validating sample URLs...")
        
        resolver = TPOAudioResolver()
        validation_stats = resolver.validate_all_urls(limit=10)
        print(f"✅ Validation complete: {validation_stats}")

def run_comprehensive_test():
    """Run comprehensive tests"""
    test_tpo_audio_resolution()
    validate_sample_urls()
    
    print(f"\n🏁 All tests completed!")

if __name__ == "__main__":
    run_comprehensive_test()