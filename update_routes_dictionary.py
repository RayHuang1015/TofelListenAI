#!/usr/bin/env python3
"""
Routes.py Dictionary Updater

Updates the GOOGLE_DOCS_TPO_URLS dictionary in routes.py with new TPO35-46 mappings.
Safely modifies the existing file while preserving other content.
"""

import re
import os
import shutil
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RoutesUpdater:
    """Updates GOOGLE_DOCS_TPO_URLS dictionary in routes.py"""
    
    def __init__(self, routes_file: str = "routes.py"):
        self.routes_file = routes_file
        self.backup_file = f"{routes_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def backup_file(self):
        """Create backup of routes.py"""
        shutil.copy2(self.routes_file, self.backup_file)
        logger.info(f"Backup created: {self.backup_file}")
    
    def update_dictionary(self, new_mappings: Dict[str, str], dry_run: bool = True) -> bool:
        """
        Update GOOGLE_DOCS_TPO_URLS dictionary with new mappings
        
        Args:
            new_mappings: Dictionary of TPO keys to URLs
            dry_run: If True, show changes without modifying file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read current file
            with open(self.routes_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the GOOGLE_DOCS_TPO_URLS dictionary
            dict_pattern = r'(GOOGLE_DOCS_TPO_URLS\s*=\s*\{)(.*?)(\n\})'
            match = re.search(dict_pattern, content, re.DOTALL)
            
            if not match:
                logger.error("Could not find GOOGLE_DOCS_TPO_URLS dictionary in routes.py")
                return False
            
            dict_start, current_content, dict_end = match.groups()
            
            # Parse existing mappings
            existing_mappings = self._parse_existing_mappings(current_content)
            
            # Filter new mappings for TPO35-46
            filtered_mappings = {k: v for k, v in new_mappings.items() 
                               if re.match(r'TPO (3[5-9]|4[0-6]) Section', k)}
            
            # Remove existing TPO35-46 mappings to avoid duplicates
            for key in list(existing_mappings.keys()):
                if re.match(r'TPO (3[5-9]|4[0-6]) Section', key):
                    del existing_mappings[key]
            
            # Combine existing and new mappings
            all_mappings = {**existing_mappings, **filtered_mappings}
            
            # Generate new dictionary content
            new_dict_content = self._generate_dictionary_content(all_mappings)
            
            # Replace dictionary in content
            new_content = content.replace(
                dict_start + current_content + dict_end,
                dict_start + new_dict_content + dict_end
            )
            
            if dry_run:
                logger.info("DRY RUN: Would update the following mappings:")
                for key, url in filtered_mappings.items():
                    logger.info(f"  {key}: {url}")
                logger.info(f"Total new TPO35-46 mappings: {len(filtered_mappings)}")
                return True
            else:
                # Create backup before modifying
                self.backup_file()
                
                # Write updated content
                with open(self.routes_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"Successfully updated {self.routes_file}")
                logger.info(f"Added {len(filtered_mappings)} new TPO35-46 mappings")
                return True
                
        except Exception as e:
            logger.error(f"Error updating routes.py: {str(e)}")
            return False
    
    def _parse_existing_mappings(self, dict_content: str) -> Dict[str, str]:
        """Parse existing dictionary mappings from string content"""
        mappings = {}
        
        # Pattern to match dictionary entries
        entry_pattern = r'"([^"]+)":\s*"([^"]+)"'
        matches = re.findall(entry_pattern, dict_content)
        
        for key, url in matches:
            mappings[key] = url
        
        return mappings
    
    def _generate_dictionary_content(self, mappings: Dict[str, str]) -> str:
        """Generate formatted dictionary content"""
        lines = []
        
        # Group by TPO number for better organization
        grouped = {}
        other_entries = {}
        
        for key, url in mappings.items():
            tpo_match = re.match(r'TPO (\d+)', key)
            if tpo_match:
                tpo_num = int(tpo_match.group(1))
                if tpo_num not in grouped:
                    grouped[tpo_num] = {}
                grouped[tpo_num][key] = url
            else:
                other_entries[key] = url
        
        # Sort TPO numbers
        sorted_tpos = sorted(grouped.keys())
        
        for i, tpo_num in enumerate(sorted_tpos):
            if i > 0:
                lines.append("")  # Empty line between TPO groups
            
            lines.append(f"    # TPO{tpo_num}")
            
            # Sort entries within each TPO
            tpo_entries = grouped[tpo_num]
            sorted_keys = sorted(tpo_entries.keys())
            
            for key in sorted_keys:
                url = tpo_entries[key]
                lines.append(f'    "{key}": "{url}",')
        
        # Add other entries at the end
        if other_entries:
            if lines:
                lines.append("")
            lines.append("    # Other entries")
            for key in sorted(other_entries.keys()):
                url = other_entries[key]
                lines.append(f'    "{key}": "{url}",')
        
        return "\n" + "\n".join(lines) + "\n"


def update_routes_with_mappings(mappings: Dict[str, str], dry_run: bool = True) -> bool:
    """
    Convenience function to update routes.py with new mappings
    
    Args:
        mappings: Dictionary of TPO keys to URLs  
        dry_run: If True, show changes without modifying file
        
    Returns:
        True if successful, False otherwise
    """
    updater = RoutesUpdater()
    return updater.update_dictionary(mappings, dry_run)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update GOOGLE_DOCS_TPO_URLS in routes.py')
    parser.add_argument('--mappings', '-m', help='JSON file with new mappings', required=True)
    parser.add_argument('--dry-run', action='store_true', help='Show changes without modifying file')
    parser.add_argument('--execute', action='store_true', help='Execute the updates')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("Error: Please specify either --dry-run or --execute")
        exit(1)
    
    try:
        import json
        with open(args.mappings, 'r') as f:
            mappings = json.load(f)
        
        success = update_routes_with_mappings(mappings, dry_run=args.dry_run)
        
        if success:
            print("✅ Routes update completed successfully")
        else:
            print("❌ Routes update failed")
            exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)