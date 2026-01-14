# Phase 3.1: TRANSFER Event Normalization Design

## 1. Current State (Heuristic Transfer Detection)

**Location:** `central_transfer_report.py`

**Current Logic:**
```
For each VIN:
  Scan events sequentially
    Find OUT event (status=SHIPPED, has date_out)
    Find next IN event at DIFFERENT site (status=IN_STOCK, has date_in)
    If: out_time < in_time ≤ out_time + max_days
    → Add to transfer_candidates
```

**Limitations:**
- ⚠️ Heuristic only - doesn't mark events as "officially" transferred
- ⚠️ Doesn't handle: intermediate storage, transfers > max_days, complex chains
- ⚠️ Double-counting risk in HQ reports if event is both OUT and later IN

---

## 2. Proposed Solution: TRANSFER Event Normalization

### 2.1 New Event Type: "TRANSFER"

Create a **normalized TRANSFER event** in `central_events` table:

```
event_type: "TRANSFER" (instead of individual OUT/IN)
action: "TRANSFER_DETECTED" or "TRANSFER_CONFIRMED"
record_id: VIN
payload: {
  "vin": "...",
  "from_site": "...",
  "to_site": "...",
  "out_event_uid": "...",       // Reference to original OUT
  "in_event_uid": "...",         // Reference to original IN
  "out_at": "ISO datetime",
  "in_at": "ISO datetime",
  "transfer_duration_days": N,
  "transfer_status": "detected" | "confirmed",
  "notes": "Auto-matched by TRANSFER_DETECTOR"
}
```

### 2.2 Matching Rules

**Rule 1: Basic OUT→IN Matching**
```
OUT event at Site A:
  - action = UPDATE
  - status changes to SHIPPED
  - has date_out

IN event at Site B (B ≠ A):
  - action = CREATE
  - status = IN_STOCK
  - has date_in
  - occurred_at within [out_time, out_time + max_days]

→ Create TRANSFER event (transfer_status = "detected")
```

**Rule 2: Time Window (Configurable)**
```
Default: 7 days (max_days=7)
Reason: Normal transport time for domestic logistics

Override via: --transfer-max-days flag
```

**Rule 3: Conflict Resolution**
```
If single OUT has multiple IN candidates:
  Choose: earliest IN within window
  Reason: Vehicle likely arrived first

If single IN has multiple OUT candidates:
  Choose: latest OUT before IN
  Reason: Last recorded exit before entry
```

**Rule 4: Chain Detection**
```
If VIN goes: A → B → C → ...
Process sequentially:
  - Mark A→B as TRANSFER_DETECTED
  - Mark B→C as TRANSFER_DETECTED
  - Continue until no more matching pairs
```

---

## 3. Implementation Plan

### 3.1 Phase 3.1.1: Design (✅ DONE - This file)

### 3.2 Phase 3.1.2: Test Suite
File: `tests/integration/test_transfer_normalization.py`

**Test Cases:**
1. `test_basic_out_in_match` - Simple A→B transfer
2. `test_time_window_boundary` - At max_days threshold
3. `test_time_window_exceeded` - Beyond max_days (should NOT match)
4. `test_same_site_ignored` - OUT→IN at same site (should NOT match)
5. `test_multiple_in_candidates` - OUT with 2+ IN options (pick earliest)
6. `test_chain_transfer_a_to_c` - A→B→C chain detection
7. `test_conflict_resolve_latest_out` - IN with multiple OUT options
8. `test_no_events` - Empty dataset
9. `test_malformed_events` - Missing date_out/date_in
10. `test_dedup_same_pair` - Don't create duplicate TRANSFER events

### 3.3 Phase 3.1.3: Implement
File: `reporting/transfer_normalizer.py` (new)

```python
class TransferNormalizer:
  """Detect & normalize OUT↔IN events into TRANSFER events"""
  
  def normalize(db_path, period_from, period_to, max_days=7):
    """
    Scan central_events for OUT/IN pairs
    Create TRANSFER events
    Return: list of created TRANSFER events
    """
```

### 3.4 Phase 3.1.4: Validate
- Run test suite
- Validate with sample data (1K vehicles, 7-day window)
- Check for duplicates
- Performance test (should be < 5s for 10K events)

---

## 4. Data Flow

```
Event Bundle (JSON)
    ↓
central_events (table)
    ↓
TransferNormalizer.normalize()
    ↓
central_events (with new TRANSFER rows)
    ↓
central_transfer_report.find_transfer_candidates()
    ↓ (now uses TRANSFER events if available)
HQ Deduplication Report
```

---

## 5. Configuration

```python
# config.py additions
TRANSFER_MAX_DAYS = 7  # Configurable

# CLI flag
--transfer-max-days=7  # Override in tools/generate_transfer_report.py
```

---

## 6. Success Criteria

- ✅ All 10 test cases pass
- ✅ No duplicate TRANSFER events created
- ✅ Performance: < 5s for 10K events
- ✅ Chain transfers (A→B→C) correctly identified
- ✅ Edge cases handled (missing dates, same site, etc.)

---

## 7. Next Steps

1. Create test dataset with various scenarios
2. Implement TransferNormalizer class
3. Add integration to generate_transfer_report.py
4. Phase 3.2: HQ Deduplication Report (uses TRANSFER events)
