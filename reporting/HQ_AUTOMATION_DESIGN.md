# Phase 3.3: HQ Automation Design

## 1. Overview

Enable automated folder monitoring and scheduled report generation for HQ operations.

**Key Features:**
- Automatic folder monitoring for new bundle files
- Auto-import on file detection
- Scheduled batch imports via Task Scheduler
- Logging and error handling

## 2. Architecture

### 2.1 Folder Monitor Component

```python
class FolderMonitor:
    """Monitor folder for new bundle files."""
    
    def __init__(self, monitor_folder, import_folder, log_folder):
        self.monitor_folder = monitor_folder
        self.import_folder = import_folder  
        self.log_folder = log_folder
        self.processed_files = set()
        
    def start(self):
        """Start folder monitoring loop."""
        while True:
            new_files = self._scan_folder()
            for file_path in new_files:
                self._process_bundle(file_path)
            time.sleep(60)  # Check every 60 seconds
    
    def _scan_folder(self) -> List[str]:
        """Scan for new bundle files."""
        # Look for .zip files in monitor folder
        
    def _process_bundle(self, file_path: str):
        """Auto-import bundle file."""
        # Call import_bundles with auto_import=True
```

### 2.2 Scheduled Task Component

```python
class ScheduledImporter:
    """Handle Task Scheduler integration."""
    
    def run_batch_import(self):
        """Run import for all unprocessed bundles."""
        # Import all files in import_folder
        
    def setup_task_scheduler(self):
        """Register Windows Task Scheduler job."""
        # Set task to run daily at specified time
```

## 3. Integration Points

### 3.1 With existing tools/import_bundles.py
- Extend to accept `auto_import=True` flag
- Return summary of processed files
- Handle errors gracefully with logging

### 3.2 With config
- Add config settings:
  - AUTOMATION_ENABLED: bool
  - MONITOR_FOLDER: path (watch for new bundles)
  - IMPORT_FOLDER: path (for scheduled imports)
  - AUTO_IMPORT_INTERVAL: seconds (default 60)
  - TASK_SCHEDULE_TIME: "HH:MM" (default "02:00" for 2 AM)

## 4. Error Handling

- **File Lock**: Handle files still being written
- **Import Errors**: Log and skip, don't stop monitoring
- **Duplicate Detection**: Track processed file hashes
- **Rollback**: If import fails, move file to error folder

## 5. Logging

```
[2025-01-15 14:32:10] [INFO] Folder monitor started - watching /imports/monitor
[2025-01-15 14:33:45] [INFO] Detected new bundle: site_bundle_2025-01-15.zip
[2025-01-15 14:35:20] [INFO] Processing site_bundle_2025-01-15.zip...
[2025-01-15 14:35:42] [INFO] Successfully imported: 156 events from site-a
[2025-01-15 14:35:42] [ERROR] Failed to import: site_bundle_backup.zip (checksum mismatch)
```

## 6. Testing Strategy

**Unit Tests:**
- FolderMonitor._scan_folder() with mock file system
- File hash tracking (no re-imports)
- Error handling scenarios

**Integration Tests:**
- Drop test bundle in monitor folder
- Verify auto-import runs
- Check processed file tracking
- Verify Task Scheduler registration

## 7. Implementation Plan

### Phase 3.3.1: FolderMonitor Class
- Implement file scanning
- Track processed files by hash
- Auto-import on detection
- ~60 lines, 4 tests

### Phase 3.3.2: ScheduledImporter
- Batch import logic
- Task Scheduler integration
- Config settings
- ~80 lines, 3 tests

### Phase 3.3.3: Integration & CLI Tool
- New command: `python -m tools.hq_automation --start`
- Config file updates
- Documentation
- ~40 lines

## 8. Timeline

- Phase 3.3.1: ~30 mins
- Phase 3.3.2: ~25 mins  
- Phase 3.3.3: ~10 mins
- Testing & debugging: ~20 mins
- **Total: ~85 mins**

## 9. Success Criteria

✅ New bundle files automatically detected and imported
✅ No duplicate imports (hash-based tracking)
✅ Graceful error handling with detailed logging
✅ Task Scheduler job created and functioning
✅ All tests passing (7 tests)
✅ Zero data loss or corruption in test scenarios
