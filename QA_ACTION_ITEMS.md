# 📌 QA QUICK REFERENCE & ACTION ITEMS

**Quick Summary for Development Team**

---

## 🔴 CRITICAL ISSUES (FIX FIRST!)

### Issue #1: Password Hashing - Mixed SHA256 + Bcrypt
**File:** `database/user_repository.py`
**Severity:** CRITICAL 🔴
**Risk:** Admin credentials can be cracked

**Current Code:**
```python
def _hash_password_legacy(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()
```

**What's Wrong:**
- SHA256 not designed for passwords
- No key stretching (bcrypt has 2^12 iterations)
- Legacy hashes vulnerable to rainbow tables

**Fix (2 hours):**
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt only."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password (bcrypt only, reject legacy)."""
    try:
        if not stored_hash.startswith('$2'):
            logger.error("Legacy hash detected - rejecting")
            return False
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False
```

---

### Issue #2: Audit Logging Silently Fails
**File:** All `database/*_manager.py` files
**Severity:** CRITICAL 🔴
**Risk:** Audit system failures invisible, data integrity issues hidden

**Current Anti-Pattern:**
```python
try:
    log_audit(...)  # If this fails, nobody knows!
except Exception:
    pass  # SILENT FAILURE!
```

**Fix (3 hours):**
```python
try:
    log_audit(...)
except Exception as e:
    # At minimum, log the error
    logger.warning(f"⚠️ AUDIT LOG FAILED: {e}", exc_info=True)
    
    # For critical operations, consider re-raising:
    # if is_critical_operation:
    #     raise AuditFailureError(...) from e
```

---

### Issue #3: Thread-Unsafe Singleton Connection
**File:** `database/base_manager.py`
**Severity:** CRITICAL 🔴
**Risk:** Race conditions, data corruption in concurrent access

**Current Code:**
```python
class BaseManager:
    _conn = None
    
    def __init__(self):
        if BaseManager._conn is None:
            BaseManager._conn = sqlite3.connect(DB_FILE)
```

**Problems:**
1. Two threads can both see `_conn is None`
2. SQLite not thread-safe by default
3. Shared connection can cause deadlocks

**Fix (2 hours):**
```python
import threading

class BaseManager:
    _conn = None
    _lock = threading.Lock()
    
    def __init__(self):
        if BaseManager._conn is None:
            with BaseManager._lock:
                # Double-check pattern
                if BaseManager._conn is None:
                    BaseManager._conn = sqlite3.connect(
                        DB_FILE,
                        check_same_thread=False,
                        timeout=30.0
                    )
                    logger.info("Database connection created")
```

---

### Issue #4: No Date Validation - Future Dates Allowed
**File:** `database/vehicle_manager.py:_validate_vehicle_data()`
**Severity:** CRITICAL 🔴
**Risk:** Invalid business logic (vehicles dated year 2099)

**Current Code:**
```python
# No check for future dates!
if date_in is not None:
    if not isinstance(date_in, datetime):
        raise DateValidationError(...)
    # That's it - no validation of actual date!
```

**Fix (2 hours):**
```python
def _validate_vehicle_data(self, vin: str, owner: str, date_in: datetime = None):
    """..."""
    
    # Add: Validate date_in is not in future
    if date_in is not None:
        if not isinstance(date_in, datetime):
            raise DateValidationError(...)
        
        now = datetime.now().replace(tzinfo=date_in.tzinfo)
        if date_in > now:
            raise DateValidationError(
                field_name="date_in",
                value=date_in.isoformat(),
                message="Ngày nhập không được nằm trong tương lai"
            )
```

---

### Issue #5: Session Never Expires
**File:** `auth/auth_manager.py`
**Severity:** CRITICAL 🔴
**Risk:** Session hijacking, unauthorized access after logout

**Current Code:**
```python
def login(self, username: str, password: str):
    result = self._user_repository.authenticate(username, password)
    if result['success']:
        self._current_user = result['user']
    return result

# No logout timeout tracking!
```

**Fix (1 hour):**
```python
from datetime import datetime, timedelta

class AuthManager:
    _current_user = None
    _login_time = None
    SESSION_TIMEOUT_MINUTES = 30
    
    def login(self, username: str, password: str):
        result = self._user_repository.authenticate(username, password)
        if result['success']:
            self._current_user = result['user']
            self._login_time = datetime.now()
        return result
    
    def check_session_valid(self) -> bool:
        """Check if current session is still valid."""
        if self._current_user is None:
            return False
        
        elapsed = (datetime.now() - self._login_time).total_seconds()
        timeout_seconds = self.SESSION_TIMEOUT_MINUTES * 60
        
        if elapsed > timeout_seconds:
            self.logout()  # Force logout
            return False
        
        return True
    
    def get_current_user(self):
        """Get current user only if session valid."""
        if not self.check_session_valid():
            return None
        return self._current_user
```

---

## 🟠 HIGH PRIORITY ISSUES (FIX THIS SPRINT)

### Issue #6: SQL Injection Risk in Search
**File:** `database/vehicle_manager.py:get_in_stock()`
**Severity:** HIGH 🟠

**Current Code:**
```python
def get_in_stock(self, owner_filter=None, search_term=None, ...):
    query = "SELECT ... WHERE status=?"
    params = [STATUS_IN_STOCK]
    
    if search_term:
        query += " AND (v.vin LIKE ? OR v.owner LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    cur.execute(query, params)  # ✅ Good! Parameterized
```

**Good News:** Code is already using parameterized queries! ✅

**But verify in all queries:**
```bash
# Check all .py files for raw SQL string concatenation
grep -r "query.*+" database/
grep -r "f\"SELECT" database/  # f-string SQL (DANGER)
```

---

### Issue #7: No Permission Enforcement at DB Layer
**File:** All `database/*_manager.py`
**Severity:** HIGH 🟠
**Risk:** Permission checks only in UI, can be bypassed

**Current State:**
- Permissions defined in `auth/permissions.py` ✅
- Permissions checked in UI ✅
- **Database doesn't enforce permissions** ❌

**Example Vulnerability:**
```python
# Someone with direct SQLite access can:
sqlite3 vehicles.db
> DELETE FROM users;  # Requires permission but no check!
```

**Fix (5 hours):**
```python
# Add permission check to all DB operations
class VehicleManager:
    def add_vehicle(self, vin, owner, ...):
        # Check permission
        current_user = AuthManager.get_instance().get_current_user()
        if current_user:
            if not has_permission(
                current_user['role'],
                Permission.VEHICLE_CREATE
            ):
                raise PermissionError(
                    f"User {current_user['username']} "
                    f"cannot create vehicles"
                )
        
        # Then proceed with add
        self.conn.execute(...)
```

---

### Issue #8: Backup Not Encrypted
**File:** `core/backup_service.py`
**Severity:** HIGH 🟠
**Risk:** Backup file stolen = full database leaked

**Current Code:**
```python
def create_backup(self, backup_type):
    # Copies database file plaintext
    shutil.copy(self.db_path, backup_file_path)
    # That's it - no encryption!
```

**Fix (4 hours):**
```python
import cryptography.fernet

class BackupService:
    def __init__(self, ...):
        # Load encryption key from environment
        key = os.getenv("BACKUP_ENCRYPTION_KEY")
        if not key:
            # Generate and save
            key = Fernet.generate_key()
            self.save_key_securely(key)
        self.cipher = Fernet(key)
    
    def create_backup(self, backup_type):
        # Create unencrypted backup first
        plain_backup = self._create_plain_backup(backup_type)
        
        # Encrypt it
        with open(plain_backup, 'rb') as f:
            encrypted = self.cipher.encrypt(f.read())
        
        # Save encrypted version
        encrypted_path = str(plain_backup) + '.encrypted'
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted)
        
        # Delete plaintext
        os.remove(plain_backup)
        
        return encrypted_path
```

---

### Issue #9: Missing Database Indexes
**File:** Database schema initialization
**Severity:** HIGH 🟠
**Impact:** Queries 10x slower on large datasets

**Current Issue:**
```python
# No index on frequently queried columns
# get_in_stock() does full table scan if no index on 'status'
```

**Fix (1 hour):**
```sql
-- Add to database initialization
CREATE INDEX IF NOT EXISTS idx_vehicles_status 
    ON vehicles(status);

CREATE INDEX IF NOT EXISTS idx_vehicles_date_out 
    ON vehicles(date_out);

CREATE INDEX IF NOT EXISTS idx_vehicles_date_in 
    ON vehicles(date_in);

CREATE INDEX IF NOT EXISTS idx_vehicles_owner_status 
    ON vehicles(owner, status);

CREATE INDEX IF NOT EXISTS idx_vehicles_dispatch_id 
    ON vehicles(dispatch_id);

CREATE INDEX IF NOT EXISTS idx_dispatches_status 
    ON dispatches(status);

-- Authentication indexes
CREATE INDEX IF NOT EXISTS idx_users_username 
    ON users(username);

CREATE INDEX IF NOT EXISTS idx_login_history_user_id 
    ON login_history(user_id);
```

---

### Issue #10: Dispatch Close Not Atomic
**File:** `database/dispatch_manager.py:close_dispatch()`
**Severity:** HIGH 🟠
**Risk:** Partial updates if failure occurs

**Current Code:**
```python
def close_dispatch(self, dispatch_id):
    vehicles = self.get_dispatch_vehicles(dispatch_id)
    for vehicle in vehicles:
        # Update one by one
        self.update_to_out(vehicle['vin'], ...)
        # If fails at #5, first 4 already committed!
```

**Fix (2 hours):**
```python
def close_dispatch(self, dispatch_id):
    """Close dispatch with atomic transaction."""
    try:
        with self.conn:  # Use context manager for transaction
            vehicles = self.get_dispatch_vehicles(dispatch_id)
            
            # Collect updates (don't execute yet)
            updates = []
            for vehicle in vehicles:
                updates.append({
                    'vin': vehicle['vin'],
                    'date_out': datetime.now(),
                    'status': STATUS_SHIPPED
                })
            
            # All updates in one transaction
            for update in updates:
                cursor.execute(
                    "UPDATE vehicles SET status=?, date_out=? WHERE vin=?",
                    (update['status'], update['date_out'], update['vin'])
                )
            
            # Update dispatch status
            cursor.execute(
                "UPDATE dispatches SET status=? WHERE id=?",
                (STATUS_SHIPMENT_COMPLETED, dispatch_id)
            )
            
            # Commit all at once
            # If any fails, entire transaction rolls back
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Close dispatch atomic transaction failed: {e}")
        # All changes rolled back automatically
        return {"success": False, "message": str(e)}
```

---

## 🟡 MEDIUM PRIORITY (NEXT SPRINT)

| # | Issue | Time | Impact |
|---|-------|------|--------|
| 11 | Timezone handling (naive vs aware) | 2h | Off-by-one days errors |
| 12 | VIN checksum validation | 2h | Invalid VINs accepted |
| 13 | Backup location configurable | 1h | Flexibility |
| 14 | Owner map validation | 1h | Data consistency |
| 15 | Pagination for large datasets | 3h | Memory/Performance |

---

## ✅ IMPLEMENTATION CHECKLIST

### Week 1 - Critical Fixes
- [ ] Issue #1: Password hashing (bcrypt only)
- [ ] Issue #2: Audit logging (no silent failures)
- [ ] Issue #3: Thread-safe connection
- [ ] Issue #4: Date validation (no future dates)
- [ ] Issue #5: Session timeout

### Week 2 - High Priority Security
- [ ] Issue #6: SQL injection (verify all queries)
- [ ] Issue #7: Permission enforcement at DB
- [ ] Issue #8: Backup encryption
- [ ] Issue #9: Database indexes
- [ ] Issue #10: Atomic transactions

### Week 3 - Testing
- [ ] Write unit tests (vehicle CRUD)
- [ ] Write integration tests (workflows)
- [ ] Write security tests (auth, permissions)
- [ ] Add performance benchmarks

### Week 4 - Code Review
- [ ] Security audit
- [ ] Performance profiling
- [ ] Code quality check (coverage > 70%)
- [ ] Documentation review

---

## 📊 METRICS TO TRACK

### Code Quality
- Test Coverage: **Current: 20% → Target: 70%**
- Code Duplication: Monitor with radon/pylint
- Cyclomatic Complexity: Keep < 10 per function

### Security
- ✅ Bcrypt passwords: 100%
- ✅ Session timeout: Enforced
- ✅ SQL injection: 0 vulnerabilities
- ✅ Permission checks: All DB operations

### Performance
- Query response time: < 1s (100K records)
- Report generation: < 5s
- UI responsiveness: < 500ms for all operations
- Memory usage: < 500MB for 100K vehicles

---

## 🚀 RELEASE CHECKLIST

Before releasing v5.2.0:
- [ ] All 5 critical issues fixed and tested
- [ ] All 5 high-priority issues addressed
- [ ] Test coverage ≥ 70%
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Changelog written
- [ ] Release notes prepared

---

## 📞 ESCALATION CONTACTS

**Issue Categories:**
- 🔴 **Critical (P0):** Contact CTO immediately
- 🟠 **High (P1):** Assign to senior developer within 24h
- 🟡 **Medium (P2):** Plan for next sprint
- 🟢 **Low (P3):** Backlog for future release

**Report Issues:** Create GitHub issue with:
- Issue title and severity level
- File path and line number
- Reproduction steps
- Expected vs. actual behavior
- Suggested fix

---

**Generated:** January 14, 2026  
**Status:** Ready for implementation  
**Estimated Effort:** 4-5 weeks (5 devs)
