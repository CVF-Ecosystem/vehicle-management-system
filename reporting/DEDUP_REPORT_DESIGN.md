# Phase 3.2: HQ Deduplication Report

## Goal
Create HQ report with deduplication logic to avoid double-counting vehicles in transfers, while maintaining backward compatibility with existing snapshot reports.

## Problem
Current snapshot report counts:
- Vehicle OUT at site A on day 1
- Vehicle IN at site B on day 3
→ Both count in their respective site's "exported" and "imported"
→ **Double-count risk** if not handled carefully

## Solution
When deduplication is **enabled**:
1. Identify TRANSFER events (OUT→IN at different sites)
2. For each transfer:
   - Credit OUT site with full export
   - Credit IN site with full import (normal)
   - **But don't count as double in consolidated HQ view**
3. Generate separate "Transfer Report" showing inter-site movements

## Report Structure

### Report A: Snapshot Report (existing, backward-compatible)
```
Each Site Summary:
- Imported (Nhập)
- Exported (Xuất)  
- Ending Stock (Tồn)

By Owner/Transport (unchanged)
```

### Report B: With Deduplication Flag (NEW)
```
If dedup_enabled=True:
  Adjust site totals:
    For each TRANSFER:
      - OUT site: keep the export record, but mark as "internal transfer"
      - IN site: mark import as "from internal transfer"
      - HQ view: don't double-count toward consolidated balance
```

### Report C: Transfer Reconciliation (NEW)
```
Transfer Summary:
- VIN: xxx
- From Site: A
- To Site: B
- Out Date: 2025-01-10
- In Date: 2025-01-11
- Status: "Reconciled" | "Pending"
```

## Configuration

```python
# config.py additions
TRANSFER_DEDUP_ENABLED = True  # Enable/disable deduplication
TRANSFER_MAX_DAYS = 7           # Time window for matching
```

## Implementation Notes

1. **Backward Compatibility**: Existing snapshot report works unchanged
2. **Configurable**: Dedup can be toggled via config or CLI flag
3. **Audit Trail**: TRANSFER events logged, all original events preserved
4. **Reporting**:
   - New column: "Transfer Status" in vehicle movement report
   - New section: "Inter-site Transfers Summary"
   - New file: transfers_reconciled_{from}_{to}.csv

## Test Strategy

1. Create scenario: 10 vehicles, 3 sites, 5 transfers
2. Compare reports:
   - Without dedup: high totals (double-count)
   - With dedup: accurate consolidated count
3. Validate TRANSFER events match OUT↔IN pairs
