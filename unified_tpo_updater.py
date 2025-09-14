#!/usr/bin/env python3
"""
Unified TPO Audio URL Updater

Complete solution for parsing Google Doc content and updating TPO35-46 audio URL mappings.
Combines all operations: parsing, validation, dictionary updates, and database updates.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Optional

# Import our custom modules
from tpo_audio_batch_updater import TPOAudioBatchUpdater
from update_routes_dictionary import RoutesUpdater
from update_database_table import DatabaseUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedTPOUpdater:
    """Unified system for complete TPO audio URL updates"""
    
    def __init__(self):
        self.parser = TPOAudioBatchUpdater()
        self.routes_updater = RoutesUpdater()
        self.db_updater = DatabaseUpdater()
        self.results = {
            'parsing': None,
            'routes_update': None,
            'database_update': None,
            'coverage_verification': None
        }
    
    def process_complete_update(self, content: str, dry_run: bool = True) -> Dict:
        """
        Complete TPO update process: parse -> validate -> update routes -> update database
        
        Args:
            content: Google Doc content to parse
            dry_run: If True, show changes without applying them
            
        Returns:
            Dictionary with results of each step
        """
        logger.info("🚀 Starting unified TPO audio URL update process")
        
        # Step 1: Parse Google Doc content
        logger.info("📖 Step 1: Parsing Google Doc content...")
        try:
            parsed_urls = self.parser.parse_google_doc_content(content)
            self.results['parsing'] = {
                'success': True,
                'urls_found': len(parsed_urls),
                'stats': self.parser.stats,
                'errors': self.parser.errors,
                'warnings': self.parser.warnings
            }
            logger.info(f"✅ Parsing complete: {len(parsed_urls)} URLs found")
        except Exception as e:
            self.results['parsing'] = {'success': False, 'error': str(e)}
            logger.error(f"❌ Parsing failed: {e}")
            return self.results
        
        if not parsed_urls:
            logger.warning("⚠️ No URLs found in content, stopping process")
            return self.results
        
        # Step 2: Update routes.py dictionary
        logger.info("📝 Step 2: Updating GOOGLE_DOCS_TPO_URLS dictionary...")
        try:
            routes_success = self.routes_updater.update_dictionary(parsed_urls, dry_run=dry_run)
            self.results['routes_update'] = {
                'success': routes_success,
                'dry_run': dry_run
            }
            if routes_success:
                logger.info("✅ Routes dictionary update completed")
            else:
                logger.error("❌ Routes dictionary update failed")
        except Exception as e:
            self.results['routes_update'] = {'success': False, 'error': str(e)}
            logger.error(f"❌ Routes update failed: {e}")
        
        # Step 3: Update database table
        logger.info("💾 Step 3: Updating tpo_audio_map database table...")
        try:
            db_success = self.db_updater.update_mappings(parsed_urls, dry_run=dry_run)
            self.results['database_update'] = {
                'success': db_success,
                'dry_run': dry_run
            }
            if db_success:
                logger.info("✅ Database update completed")
            else:
                logger.error("❌ Database update failed")
        except Exception as e:
            self.results['database_update'] = {'success': False, 'error': str(e)}
            logger.error(f"❌ Database update failed: {e}")
        
        # Step 4: Verify coverage
        logger.info("🔍 Step 4: Verifying TPO35-46 coverage...")
        try:
            coverage = self.parser.validate_coverage()
            db_coverage = self.db_updater.verify_coverage()
            
            self.results['coverage_verification'] = {
                'success': True,
                'parser_coverage': coverage,
                'database_coverage': db_coverage
            }
            
            missing_count = len(coverage['missing'])
            total_expected = 72  # 12 TPOs × 6 segments each
            found_count = total_expected - missing_count
            
            logger.info(f"✅ Coverage verification complete")
            logger.info(f"   Found: {found_count}/{total_expected} segments")
            if missing_count > 0:
                logger.warning(f"   Missing: {missing_count} segments")
            
        except Exception as e:
            self.results['coverage_verification'] = {'success': False, 'error': str(e)}
            logger.error(f"❌ Coverage verification failed: {e}")
        
        logger.info("🏁 Unified update process completed")
        return self.results
    
    def print_final_report(self):
        """Print comprehensive final report"""
        print("\n" + "="*80)
        print("UNIFIED TPO AUDIO URL UPDATE REPORT")
        print("="*80)
        
        # Parsing results
        parsing = self.results.get('parsing', {})
        if parsing.get('success'):
            print(f"\n📖 PARSING: ✅ SUCCESS")
            print(f"   URLs found: {parsing['urls_found']}")
            print(f"   Valid URLs: {parsing['stats']['valid_urls']}")
            print(f"   Invalid URLs: {parsing['stats']['invalid_urls']}")
            print(f"   Duplicates removed: {parsing['stats']['duplicates_removed']}")
            if parsing['errors']:
                print(f"   Errors: {len(parsing['errors'])} (see logs for details)")
        else:
            print(f"\n📖 PARSING: ❌ FAILED")
            if 'error' in parsing:
                print(f"   Error: {parsing['error']}")
        
        # Routes update results
        routes = self.results.get('routes_update', {})
        if routes.get('success'):
            status = "DRY RUN" if routes.get('dry_run') else "EXECUTED"
            print(f"\n📝 ROUTES UPDATE: ✅ {status}")
        else:
            print(f"\n📝 ROUTES UPDATE: ❌ FAILED")
            if 'error' in routes:
                print(f"   Error: {routes['error']}")
        
        # Database update results
        database = self.results.get('database_update', {})
        if database.get('success'):
            status = "DRY RUN" if database.get('dry_run') else "EXECUTED"
            print(f"\n💾 DATABASE UPDATE: ✅ {status}")
        else:
            print(f"\n💾 DATABASE UPDATE: ❌ FAILED")
            if 'error' in database:
                print(f"   Error: {database['error']}")
        
        # Coverage verification results
        coverage = self.results.get('coverage_verification', {})
        if coverage.get('success'):
            print(f"\n🔍 COVERAGE VERIFICATION: ✅ SUCCESS")
            
            parser_cov = coverage['parser_coverage']
            db_cov = coverage['database_coverage']
            
            print(f"   Parser coverage: {len(parser_cov['complete'])}/72 segments")
            print(f"   Database coverage: {db_cov['total_found']}/{db_cov['total_expected']} segments")
            
            if parser_cov['missing']:
                print(f"   Missing from parsed data: {len(parser_cov['missing'])} segments")
            
            if db_cov['missing']:
                print(f"   Missing from database: {len(db_cov['missing'])} segments")
                
        else:
            print(f"\n🔍 COVERAGE VERIFICATION: ❌ FAILED")
            if 'error' in coverage:
                print(f"   Error: {coverage['error']}")
        
        print(f"\n" + "="*80)


def create_sample_google_doc_content() -> str:
    """Create sample Google Doc content to demonstrate the system"""
    return """
TPO Audio URLs - Updated Collection

TPO 37 Section 1 Passage 2: https://ti.koocdn.com/upload/ti/2423000-2424000/2423048/example_s1p2.mp3
TPO 37 Section 1 Passage 3: https://ti.koocdn.com/upload/ti/2423000-2424000/2423049/example_s1p3.mp3
TPO 37 Section 2 Passage 1: https://ti.koocdn.com/upload/ti/2423000-2424000/2423050/example_s2p1.mp3
TPO 37 Section 2 Passage 2: https://ti.koocdn.com/upload/ti/2423000-2424000/2423051/example_s2p2.mp3
TPO 37 Section 2 Passage 3: https://ti.koocdn.com/upload/ti/2423000-2424000/2423052/example_s2p3.mp3

TPO 38 Section 1 Passage 2: https://ti.koocdn.com/upload/ti/2422000-2423000/2422931/example_s1p2.mp3
TPO 38 Section 1 Passage 3: https://ti.koocdn.com/upload/ti/2422000-2423000/2422932/example_s1p3.mp3
TPO 38 Section 2 Passage 1: https://ti.koocdn.com/upload/ti/2422000-2423000/2422933/example_s2p1.mp3
TPO 38 Section 2 Passage 2: https://ti.koocdn.com/upload/ti/2422000-2423000/2422934/example_s2p2.mp3
TPO 38 Section 2 Passage 3: https://ti.koocdn.com/upload/ti/2422000-2423000/2422935/example_s2p3.mp3

TPO 39 Section 1 Passage 2: https://ti.koocdn.com/upload/ti/2422000-2423000/2422906/example_s1p2.mp3
TPO 39 Section 1 Passage 3: https://ti.koocdn.com/upload/ti/2422000-2423000/2422907/example_s1p3.mp3
TPO 39 Section 2 Passage 1: https://ti.koocdn.com/upload/ti/2422000-2423000/2422908/example_s2p1.mp3
TPO 39 Section 2 Passage 2: https://ti.koocdn.com/upload/ti/2422000-2423000/2422909/example_s2p2.mp3
TPO 39 Section 2 Passage 3: https://ti.koocdn.com/upload/ti/2422000-2423000/2422910/example_s2p3.mp3

TPO 40 Section 1 Passage 2: https://ti.koocdn.com/upload/ti/2334000-2335000/2334192/example_s1p2.mp3
TPO 40 Section 1 Passage 3: https://ti.koocdn.com/upload/ti/2334000-2335000/2334193/example_s1p3.mp3
TPO 40 Section 2 Passage 1: https://ti.koocdn.com/upload/ti/2334000-2335000/2334194/example_s2p1.mp3
TPO 40 Section 2 Passage 2: https://ti.koocdn.com/upload/ti/2334000-2335000/2334195/example_s2p2.mp3
TPO 40 Section 2 Passage 3: https://ti.koocdn.com/upload/ti/2334000-2335000/2334196/example_s2p3.mp3

TPO 41 Section 1 Passage 1: https://ti.koocdn.com/upload/ti/2334000-2335000/2334197/example_s1p1.mp3
TPO 41 Section 1 Passage 2: https://ti.koocdn.com/upload/ti/2334000-2335000/2334198/example_s1p2.mp3
TPO 41 Section 1 Passage 3: https://ti.koocdn.com/upload/ti/2334000-2335000/2334199/example_s1p3.mp3
TPO 41 Section 2 Passage 1: https://ti.koocdn.com/upload/ti/2334000-2335000/2334200/example_s2p1.mp3
TPO 41 Section 2 Passage 2: https://ti.koocdn.com/upload/ti/2334000-2335000/2334201/example_s2p2.mp3
TPO 41 Section 2 Passage 3: https://ti.koocdn.com/upload/ti/2334000-2335000/2334202/example_s2p3.mp3

TPO 42 Section 1 Passage 1: https://ti.koocdn.com/upload/ti/2334000-2335000/2334203/example_s1p1.mp3
TPO 42 Section 1 Passage 2: https://ti.koocdn.com/upload/ti/2334000-2335000/2334204/example_s1p2.mp3
TPO 42 Section 1 Passage 3: https://ti.koocdn.com/upload/ti/2334000-2335000/2334205/example_s1p3.mp3
TPO 42 Section 2 Passage 1: https://ti.koocdn.com/upload/ti/2334000-2335000/2334206/example_s2p1.mp3
TPO 42 Section 2 Passage 2: https://ti.koocdn.com/upload/ti/2334000-2335000/2334207/example_s2p2.mp3
TPO 42 Section 2 Passage 3: https://ti.koocdn.com/upload/ti/2334000-2335000/2334208/example_s2p3.mp3
"""


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Unified TPO Audio URL Updater')
    parser.add_argument('--input', '-i', help='Input file with Google Doc content')
    parser.add_argument('--content', '-c', help='Direct content input')
    parser.add_argument('--sample', action='store_true', help='Use sample data for demonstration')
    parser.add_argument('--dry-run', action='store_true', help='Dry run - show changes without applying')
    parser.add_argument('--execute', action='store_true', help='Execute the updates')
    parser.add_argument('--output-json', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Determine run mode
    if not args.dry_run and not args.execute:
        print("❌ Error: Please specify either --dry-run or --execute")
        return 1
    
    # Get content source
    content = None
    if args.sample:
        content = create_sample_google_doc_content()
        logger.info("Using sample Google Doc content for demonstration")
    elif args.input:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Read content from {args.input}")
        except Exception as e:
            print(f"❌ Error reading input file: {e}")
            return 1
    elif args.content:
        content = args.content
        logger.info("Using direct content input")
    else:
        print("❌ Error: Please provide content via --input, --content, or --sample")
        print("\nExample usage:")
        print("  python unified_tpo_updater.py --sample --dry-run")
        print("  python unified_tpo_updater.py --input google_doc.txt --execute")
        return 1
    
    # Process update
    try:
        updater = UnifiedTPOUpdater()
        results = updater.process_complete_update(content, dry_run=args.dry_run)
        
        # Print report
        updater.print_final_report()
        
        # Save results to JSON if requested
        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {args.output_json}")
        
        # Determine exit code based on results
        success = all(
            result.get('success', False) for result in results.values()
            if result is not None
        )
        
        if success:
            print("\n🎉 All operations completed successfully!")
            return 0
        else:
            print("\n⚠️ Some operations failed. Check the report above.")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())