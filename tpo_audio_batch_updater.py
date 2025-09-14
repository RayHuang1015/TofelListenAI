#!/usr/bin/env python3
"""
TPO Audio URL Batch Updater

Comprehensive system to parse Google Doc content and batch update TPO35-46 audio URL mappings.
Handles line breaks, format issues, URL validation, and ensures complete coverage.

Usage:
    python tpo_audio_batch_updater.py --input google_doc_content.txt --dry-run
    python tpo_audio_batch_updater.py --input google_doc_content.txt --execute
"""

import re
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from urllib.parse import urlparse
import argparse
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TPOAudioBatchUpdater:
    """Main class for parsing Google Doc content and updating TPO audio URL mappings"""
    
    def __init__(self):
        self.tpo_urls = {}
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_parsed': 0,
            'valid_urls': 0,
            'invalid_urls': 0,
            'duplicates_removed': 0,
            'missing_segments': 0
        }
        
        # Expected segments for TPO35-46
        self.expected_segments = self._generate_expected_segments()
        
        # URL validation patterns
        self.valid_url_patterns = [
            r'https://ti\.koocdn\.com/upload/ti/\d+-\d+/\d+/[a-f0-9]+\.mp3',
            r'https://daxue-cos\.koocdn\.com/upload/ti/sardine/\d+-\d+/\d+/[a-f0-9]+\.mp3',
            r'https://tikustorage-sh\.oss-cn-shanghai\.aliyuncs\.com/TPO_Audio/tpo\d+/tpo\d+_listening_passage\d+_\d+\.mp3'
        ]

    def _generate_expected_segments(self) -> Set[Tuple[int, int, int]]:
        """Generate expected (tpo_number, section, part) tuples for TPO35-46"""
        expected = set()
        for tpo in range(35, 47):  # TPO35-46
            for section in [1, 2]:  # Section 1 and 2
                for part in [1, 2, 3]:  # Part 1, 2, 3
                    expected.add((tpo, section, part))
        return expected

    def parse_google_doc_content(self, content: str) -> Dict[str, str]:
        """
        Parse Google Doc content and extract TPO audio URL mappings
        
        Handles various formats:
        - "TPO 35 Section 1 Passage 1: https://..."
        - "TPO35S1P1: https://..."
        - "TPO 35 - Section 1 - Passage 1\nhttps://..."
        - Lines with breaks and formatting issues
        """
        logger.info("Starting Google Doc content parsing...")
        
        # Clean and normalize content
        content = self._clean_content(content)
        
        # Split into lines and process
        lines = content.split('\n')
        current_tpo_info = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                # Try to parse TPO info and URL from the line
                tpo_info, url = self._parse_line(line, current_tpo_info)
                
                if tpo_info and url:
                    key = self._format_tpo_key(tpo_info)
                    if self._validate_url(url):
                        if key in self.tpo_urls:
                            self.warnings.append(f"Line {line_num}: Duplicate mapping for {key}")
                            self.stats['duplicates_removed'] += 1
                        else:
                            self.tpo_urls[key] = url
                            self.stats['valid_urls'] += 1
                    else:
                        self.errors.append(f"Line {line_num}: Invalid URL format: {url}")
                        self.stats['invalid_urls'] += 1
                    
                    self.stats['total_parsed'] += 1
                elif tpo_info:
                    # Line contains TPO info but no URL, save for next line
                    current_tpo_info = tpo_info
                elif self._is_url(line) and current_tpo_info:
                    # Line is a URL and we have pending TPO info
                    if self._validate_url(line):
                        key = self._format_tpo_key(current_tpo_info)
                        self.tpo_urls[key] = line
                        self.stats['valid_urls'] += 1
                        self.stats['total_parsed'] += 1
                        current_tpo_info = None
                    else:
                        self.errors.append(f"Line {line_num}: Invalid URL format: {line}")
                        self.stats['invalid_urls'] += 1
                        current_tpo_info = None
                        
            except Exception as e:
                self.errors.append(f"Line {line_num}: Parse error: {str(e)}")
        
        logger.info(f"Parsing complete. Found {len(self.tpo_urls)} valid mappings")
        return self.tpo_urls

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content to handle formatting issues"""
        # Remove BOM if present
        content = content.lstrip('\ufeff')
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace
        content = re.sub(r' +', ' ', content)
        
        # Handle broken lines (URL on next line)
        content = re.sub(r'(TPO \d+[^:]*?):\s*\n\s*(https?://[^\s]+)', r'\1: \2', content)
        
        return content

    def _parse_line(self, line: str, current_tpo_info: Optional[Tuple[int, int, int]] = None) -> Tuple[Optional[Tuple[int, int, int]], Optional[str]]:
        """Parse a single line to extract TPO info and URL"""
        
        # Pattern 1: "TPO 35 Section 1 Passage 1: https://..."
        pattern1 = r'TPO\s*(\d+)\s*Section\s*(\d+)\s*Passage\s*(\d+)\s*[:：]\s*(https?://[^\s]+)'
        match = re.search(pattern1, line, re.IGNORECASE)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3))), match.group(4)
        
        # Pattern 2: "TPO35S1P1: https://..."
        pattern2 = r'TPO\s*(\d+)\s*S\s*(\d+)\s*P\s*(\d+)\s*[:：]\s*(https?://[^\s]+)'
        match = re.search(pattern2, line, re.IGNORECASE)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3))), match.group(4)
        
        # Pattern 3: TPO info only (URL on next line)
        pattern3 = r'TPO\s*(\d+)(?:\s*[-–—]\s*)?Section\s*(\d+)(?:\s*[-–—]\s*)?Passage\s*(\d+)'
        match = re.search(pattern3, line, re.IGNORECASE)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3))), None
        
        # Pattern 4: Short format TPO info only
        pattern4 = r'TPO\s*(\d+)\s*S\s*(\d+)\s*P\s*(\d+)'
        match = re.search(pattern4, line, re.IGNORECASE)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3))), None
        
        # Check if line is just a URL
        if self._is_url(line):
            return current_tpo_info, line
        
        return None, None

    def _is_url(self, text: str) -> bool:
        """Check if text is a URL"""
        return bool(re.match(r'https?://[^\s]+', text.strip()))

    def _validate_url(self, url: str) -> bool:
        """Validate URL format against known patterns"""
        url = url.strip()
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
        except:
            return False
        
        # Check against known patterns
        for pattern in self.valid_url_patterns:
            if re.match(pattern, url):
                return True
        
        # Allow other valid-looking audio URLs
        if url.endswith('.mp3') and ('koocdn.com' in url or 'aliyuncs.com' in url):
            return True
        
        return False

    def _format_tpo_key(self, tpo_info: Tuple[int, int, int]) -> str:
        """Format TPO info tuple into standard key format"""
        tpo_num, section, part = tpo_info
        return f"TPO {tpo_num} Section {section} Passage {part}"

    def validate_coverage(self) -> Dict[str, List[str]]:
        """Validate that all expected TPO35-46 segments are covered"""
        logger.info("Validating TPO35-46 coverage...")
        
        coverage_report = {
            'complete': [],
            'missing': [],
            'extra': []
        }
        
        # Parse found mappings
        found_segments = set()
        for key in self.tpo_urls.keys():
            match = re.match(r'TPO (\d+) Section (\d+) Passage (\d+)', key)
            if match:
                tpo_num, section, part = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 35 <= tpo_num <= 46:
                    found_segments.add((tpo_num, section, part))
                else:
                    coverage_report['extra'].append(key)
        
        # Check for missing segments
        missing_segments = self.expected_segments - found_segments
        complete_segments = self.expected_segments & found_segments
        
        coverage_report['complete'] = [f"TPO {t} Section {s} Passage {p}" for t, s, p in sorted(complete_segments)]
        coverage_report['missing'] = [f"TPO {t} Section {s} Passage {p}" for t, s, p in sorted(missing_segments)]
        
        self.stats['missing_segments'] = len(missing_segments)
        
        logger.info(f"Coverage: {len(complete_segments)}/{len(self.expected_segments)} segments found")
        return coverage_report

    def generate_routes_py_update(self) -> str:
        """Generate Python code to update GOOGLE_DOCS_TPO_URLS in routes.py"""
        logger.info("Generating routes.py update code...")
        
        # Filter for TPO35-46 only
        tpo35_46_urls = {k: v for k, v in self.tpo_urls.items() 
                        if re.match(r'TPO (3[5-9]|4[0-6]) Section', k)}
        
        code_lines = ['# TPO35-46 Audio URLs - Auto-generated from Google Doc']
        code_lines.append('GOOGLE_DOCS_TPO_URLS.update({')
        
        for key in sorted(tpo35_46_urls.keys()):
            url = tpo35_46_urls[key]
            code_lines.append(f'    "{key}": "{url}",')
        
        code_lines.append('})')
        
        return '\n'.join(code_lines)

    def generate_database_update_sql(self) -> str:
        """Generate SQL to update tpo_audio_map database table"""
        logger.info("Generating database update SQL...")
        
        sql_lines = ['-- TPO35-46 Audio URLs Database Update - Auto-generated from Google Doc']
        sql_lines.append('-- Delete existing TPO35-46 mappings')
        sql_lines.append('DELETE FROM tpo_audio_map WHERE tpo_number BETWEEN 35 AND 46;')
        sql_lines.append('')
        sql_lines.append('-- Insert new mappings')
        
        for key, url in sorted(self.tpo_urls.items()):
            match = re.match(r'TPO (\d+) Section (\d+) Passage (\d+)', key)
            if match:
                tpo_num, section, part = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 35 <= tpo_num <= 46:
                    content_type = 'conversation' if part == 1 else 'lecture'
                    title = f"TPO {tpo_num} Section {section} Part {part}"
                    
                    sql_lines.append(f"""INSERT INTO tpo_audio_map (tpo_number, section, part, content_type, primary_url, url_status, source_provider, title, created_at, updated_at) 
VALUES ({tpo_num}, {section}, {part}, '{content_type}', '{url}', 'valid', 'koocdn', '{title}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);""")
        
        return '\n'.join(sql_lines)

    def print_report(self):
        """Print comprehensive processing report"""
        print("\n" + "="*80)
        print("TPO AUDIO BATCH UPDATE REPORT")
        print("="*80)
        
        print(f"\nParsing Statistics:")
        print(f"  Total lines parsed: {self.stats['total_parsed']}")
        print(f"  Valid URLs found: {self.stats['valid_urls']}")
        print(f"  Invalid URLs: {self.stats['invalid_urls']}")
        print(f"  Duplicates removed: {self.stats['duplicates_removed']}")
        print(f"  Missing segments: {self.stats['missing_segments']}")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"  ❌ {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more errors")
        
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"  ⚠️  {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
        
        # Coverage report
        coverage = self.validate_coverage()
        print(f"\nCoverage Report:")
        print(f"  ✅ Complete: {len(coverage['complete'])}/72 segments")
        print(f"  ❌ Missing: {len(coverage['missing'])} segments")
        
        if coverage['missing']:
            print(f"\nMissing segments (first 10):")
            for missing in coverage['missing'][:10]:
                print(f"    - {missing}")
            if len(coverage['missing']) > 10:
                print(f"    ... and {len(coverage['missing']) - 10} more")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='TPO Audio URL Batch Updater')
    parser.add_argument('--input', '-i', help='Input file with Google Doc content', required=False)
    parser.add_argument('--content', '-c', help='Direct content input', required=False)
    parser.add_argument('--dry-run', action='store_true', help='Dry run - show what would be updated')
    parser.add_argument('--execute', action='store_true', help='Execute the updates')
    parser.add_argument('--output-routes', help='Output file for routes.py updates')
    parser.add_argument('--output-sql', help='Output file for SQL updates')
    
    args = parser.parse_args()
    
    if not args.input and not args.content:
        print("❌ Error: Please provide either --input file or --content")
        print("\nExample usage:")
        print("  python tpo_audio_batch_updater.py --content 'TPO 35 Section 1 Passage 1: https://...' --dry-run")
        print("  python tpo_audio_batch_updater.py --input google_doc.txt --execute")
        return 1
    
    # Initialize updater
    updater = TPOAudioBatchUpdater()
    
    # Read content
    try:
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Read content from {args.input}")
        else:
            content = args.content
        
        # Parse content
        urls = updater.parse_google_doc_content(content)
        
        # Generate updates
        routes_update = updater.generate_routes_py_update()
        sql_update = updater.generate_database_update_sql()
        
        # Save outputs if requested
        if args.output_routes:
            with open(args.output_routes, 'w', encoding='utf-8') as f:
                f.write(routes_update)
            logger.info(f"Routes update saved to {args.output_routes}")
        
        if args.output_sql:
            with open(args.output_sql, 'w', encoding='utf-8') as f:
                f.write(sql_update)
            logger.info(f"SQL update saved to {args.output_sql}")
        
        # Print report
        updater.print_report()
        
        if args.dry_run:
            print(f"\n🔍 DRY RUN MODE - No changes made")
            print(f"\nGenerated routes.py update:")
            print(routes_update[:500] + "..." if len(routes_update) > 500 else routes_update)
            print(f"\nGenerated SQL update:")
            print(sql_update[:500] + "..." if len(sql_update) > 500 else sql_update)
        
        if args.execute:
            print(f"\n🚀 EXECUTE MODE - Updates would be applied")
            print("⚠️  This functionality requires database connection")
            print("⚠️  Manual application of updates recommended for safety")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())