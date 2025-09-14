# TPO Audio URL Batch Update System

## Overview

This comprehensive system parses Google Doc content and batch updates TPO35-46 audio URL mappings to fix the issue where most TPO audio files cannot be played. The system handles line breaks, format issues, URL validation, and ensures complete coverage.

## 🚨 Current Status Analysis

Based on our analysis of the current TPO35-46 audio URL mapping system:

### Existing Coverage
- **TPO35-36**: ✅ Complete (all 6 segments each - 12 total)  
- **TPO37-40**: ❌ Incomplete (only S1P1 exists - missing 20 segments)
- **TPO41-46**: ❌ Missing completely (missing 36 segments)

### Total Gap: 56 missing segments out of 72 expected

## 📁 System Components

The batch update system consists of these key files:

1. **`tpo_audio_batch_updater.py`** - Core Google Doc content parser
2. **`update_routes_dictionary.py`** - Updates GOOGLE_DOCS_TPO_URLS in routes.py  
3. **`update_database_table.py`** - Updates tpo_audio_map database table
4. **`unified_tpo_updater.py`** - Complete workflow orchestrator

## 🔧 Usage Instructions

### Method 1: Unified Workflow (Recommended)

```bash
# Step 1: Test with sample data (dry run)
python unified_tpo_updater.py --sample --dry-run

# Step 2: Use your Google Doc content (dry run)
python unified_tpo_updater.py --input google_doc.txt --dry-run

# Step 3: Execute actual updates  
python unified_tpo_updater.py --input google_doc.txt --execute
```

### Method 2: Individual Components

```bash
# Parse Google Doc content only
python tpo_audio_batch_updater.py --input google_doc.txt --dry-run

# Update routes.py dictionary only
python update_routes_dictionary.py --mappings parsed_urls.json --dry-run

# Update database table only  
python update_database_table.py --mappings parsed_urls.json --dry-run
```

## 📋 Google Doc Content Format

The parser handles multiple formats:

### Supported Formats
```
TPO 37 Section 1 Passage 2: https://ti.koocdn.com/upload/ti/...
TPO37S1P2: https://ti.koocdn.com/upload/ti/...
TPO 37 - Section 1 - Passage 2
https://ti.koocdn.com/upload/ti/...
```

### URL Validation
Accepts URLs from:
- `ti.koocdn.com` (primary source)
- `daxue-cos.koocdn.com` (secondary source)  
- `tikustorage-sh.oss-cn-shanghai.aliyuncs.com` (fallback)

## 🎯 Expected Segments for TPO35-46

Each TPO should have 6 segments:
- Section 1: Passage 1 (Conversation), Passage 2 (Lecture), Passage 3 (Lecture)
- Section 2: Passage 1 (Conversation), Passage 2 (Lecture), Passage 3 (Lecture)

**Total expected: 12 TPOs × 6 segments = 72 segments**

## 📊 Verification & Coverage

The system provides comprehensive verification:

### Parsing Report
- Total URLs found and validated
- Invalid URLs and formatting errors
- Duplicate mappings removed
- Missing segments identified

### Coverage Analysis  
- Complete segments vs expected (out of 72)
- Missing segments by TPO number
- Database vs dictionary consistency

### Safety Features
- Automatic backups before changes
- Dry-run mode for testing
- Rollback capability
- Duplicate detection and removal

## 🔒 Safety Measures

### Before Updates
1. **Automatic Backups**: 
   - `routes.py.backup.YYYYMMDD_HHMMSS`
   - `tpo_audio_backup_YYYYMMDD_HHMMSS.sql`

2. **Dry Run Testing**:
   - Always test with `--dry-run` first
   - Review changes before executing

3. **Validation**:
   - URL format validation
   - Duplicate detection  
   - Coverage verification

## 🚀 Quick Start

### If you have Google Doc content:

1. **Save Google Doc content to file**:
   ```bash
   # Copy content to google_doc.txt
   ```

2. **Test with dry run**:
   ```bash
   python unified_tpo_updater.py --input google_doc.txt --dry-run
   ```

3. **Review the report** and fix any issues

4. **Execute updates**:
   ```bash
   python unified_tpo_updater.py --input google_doc.txt --execute
   ```

### If you want to test the system:

```bash
# Use built-in sample data
python unified_tpo_updater.py --sample --dry-run
```

## 📈 Expected Results

After successful execution:

1. **GOOGLE_DOCS_TPO_URLS** in `routes.py` updated with new mappings
2. **tpo_audio_map** database table populated with missing segments  
3. **Coverage verification** showing 72/72 segments found
4. **Audio playback** working for all TPO35-46 segments

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Run from project root directory
   cd /workspaces/20241220-TOEFL-Practice-Listening
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database status
   python -c "from app import db; print('DB OK')"
   ```

3. **Permission Issues**:
   ```bash
   # Check file permissions
   ls -la routes.py
   ```

### Error Recovery

1. **Restore from backup**:
   ```bash
   # Routes.py
   cp routes.py.backup.YYYYMMDD_HHMMSS routes.py
   
   # Database (run SQL file)
   python -c "from app import app, db; 
   with app.app_context(): 
       with open('tpo_audio_backup_YYYYMMDD_HHMMSS.sql') as f:
           db.session.execute(db.text(f.read()));
       db.session.commit()"
   ```

## 📞 Next Steps

1. **Obtain Google Doc content** with TPO35-46 audio URLs
2. **Save content to text file** (handle any encoding issues)
3. **Run dry-run test** to validate parsing
4. **Review coverage report** to ensure all segments are found
5. **Execute updates** if validation passes
6. **Restart application** to load new mappings
7. **Test audio playback** for TPO35-46

## 🎉 Success Criteria

- ✅ All 72 TPO35-46 segments have valid audio URLs
- ✅ Both dictionary and database are updated consistently
- ✅ No duplicate or invalid URLs
- ✅ Audio playback works for all segments
- ✅ System backup files created successfully
- ✅ Coverage verification shows 72/72 complete

---

*This system addresses the critical issue where most TPO audio files cannot be played by ensuring comprehensive and accurate URL mappings for TPO35-46.*