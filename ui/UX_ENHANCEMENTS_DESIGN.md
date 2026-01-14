# Phase 3.4: UX Enhancements Design

## 1. Overview

Add UI buttons and dialogs to enable users to directly access Phase 3.2 and 3.3 features from the GUI.

**Key Features:**
- Export bundle button (snapshot reports)
- Import bundles button (with file selection)
- Generate report button (HQ dedup report)
- Start auto-monitor button (start folder monitoring)
- Progress dialogs and confirmations

## 2. UI Components to Add

### 2.1 New Buttons in Dashboard

**Location:** dashboard_tab.py (Main tab)

```
[Export Bundle] [Import Bundles] [Generate Report] [Auto Monitor]
```

### 2.2 Export Bundle Dialog

```python
class ExportBundleDialog:
    """Dialog for exporting site bundles."""
    
    - Period selection (date range)
    - Include transfers checkbox
    - Export location selector
    - Progress bar
    - Success/error message
```

### 2.3 Import Bundles Dialog

```python
class ImportBundlesDialog:
    """Dialog for importing bundles."""
    
    - File selection dialog
    - Preview of files to import
    - Progress bar
    - Import results summary
```

### 2.4 Generate Report Dialog

```python
class GenerateReportDialog:
    """Dialog for generating HQ reports."""
    
    - Period selection
    - Report type selector:
      - Vehicle movements
      - Site summary
      - Transfer reconciliation
      - Consolidated
    - Dedup toggle
    - Output format (CSV)
    - Save location
    - Progress
    - Open exported file option
```

### 2.5 Auto Monitor Dialog

```python
class AutoMonitorDialog:
    """Dialog for folder monitoring."""
    
    - Start/Stop button
    - Monitor folder display
    - Status (Running / Stopped)
    - Recent activity log
    - Setup Task Scheduler button
```

## 3. Integration Points

### 3.1 With tools/export_site_bundle.py
- Add `export_with_period()` method
- Return file path on success
- Emit progress signals

### 3.2 With tools/import_bundles.py
- Extend to accept list of files
- Return summary dict
- Support async operation with callbacks

### 3.3 With reporting/central_report_dedup.py
- Wrap generator for async use
- Progress callback support
- CSV export integration

### 3.4 With reporting/hq_automation.py
- Start/stop monitor in separate thread
- Show live status
- Display recent imports

## 4. Dialog Layouts

### ExportBundleDialog

```
Title: Export Site Bundle

Period:
  From: [YYYY-MM-DD]
  To:   [YYYY-MM-DD]

Options:
  ☑ Include transfer events
  ☑ Include dedup info

Output:
  Location: [Browse] /exports/

[Status: Preparing...]
[========>          ] 45%

[ Cancel ]  [ Export ]
```

### ImportBundlesDialog

```
Title: Import Bundles

Select files to import:
  [Browse]

Files to import:
  ☑ site_bundle_2025-01-15.zip (2.3 MB)
  ☑ site_bundle_2025-01-14.zip (1.8 MB)

[Status: Importing...]
[==============>    ] 65%

Import Results:
  Successful: 2 files, 1542 events
  Failed: 0 files

[ Done ]
```

### GenerateReportDialog

```
Title: Generate HQ Report

Period:
  From: [YYYY-MM-DD]
  To:   [YYYY-MM-DD]

Report Type:
  ○ Vehicle Movements
  ○ Site Summary
  ○ Transfer Reconciliation
  ○ Consolidated (all three)

Options:
  ☑ Enable deduplication

Output:
  Location: [Browse] /reports/
  Format: CSV

[Status: Generating...]
[=======>           ] 30%

[ Cancel ]  [ Generate ]
```

### AutoMonitorDialog

```
Title: Auto Monitor

Monitor Status: [Running ●] or [Stopped ○]

Monitor Folder: /data/monitor

Recent Activity:
  14:35:42 - Imported site_bundle_2025-01-15.zip (156 events)
  14:32:10 - Started monitoring
  
  [View full log]

Schedule:
  Task Scheduler Job: [Not set up]
  [Set Up Daily Task]

[Stop Monitor]  [Close]
```

## 5. Implementation Plan

### Phase 3.4.1: Core Dialogs
- ExportBundleDialog class
- ImportBundlesDialog class
- GenerateReportDialog class
- ~250 lines, 5 tests

### Phase 3.4.2: Auto Monitor Dialog
- AutoMonitorDialog class
- Thread management for monitoring
- Status updates
- ~180 lines, 3 tests

### Phase 3.4.3: Dashboard Integration
- Add buttons to dashboard_tab.py
- Wire up button signals
- Add icons/styling
- ~60 lines

### Phase 3.4.4: Integration & Polish
- Error handling dialogs
- Validation
- User confirmations
- Documentation
- ~40 lines

## 6. Code Structure

```
ui/
  export_bundle_dialog.py      # ExportBundleDialog
  import_bundles_dialog.py     # ImportBundlesDialog
  generate_report_dialog.py    # GenerateReportDialog
  auto_monitor_dialog.py       # AutoMonitorDialog
  
tests/unit/
  test_export_bundle_dialog.py
  test_import_bundles_dialog.py
  test_generate_report_dialog.py
  test_auto_monitor_dialog.py
```

## 7. Signal/Slot Integration

Each dialog will emit signals to update UI:
- `progressUpdated(int)` - progress bar
- `statusChanged(str)` - status message
- `completed(dict)` - operation finished
- `errorOccurred(str)` - error handling

## 8. Timeline

- Phase 3.4.1: ~40 mins
- Phase 3.4.2: ~30 mins
- Phase 3.4.3: ~15 mins
- Phase 3.4.4: ~15 mins
- Testing & debugging: ~20 mins
- **Total: ~120 mins**

## 9. Success Criteria

✅ Users can export bundles from GUI
✅ Users can import bundles from GUI
✅ Users can generate reports from GUI
✅ Auto monitor status visible in GUI
✅ All operations show progress
✅ Error messages clear and actionable
✅ No functionality broken
✅ All tests passing (8 tests)
