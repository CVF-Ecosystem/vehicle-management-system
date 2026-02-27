# excel_importer.py
import pandas as pd
from datetime import datetime
import logging
from thefuzz import fuzz
import unidecode
from config import (
    EXPECTED_VIN_COL, EXPECTED_OWNER_COL, EXPECTED_TYPE_COL
)
from database.audit_repository import log_audit, AuditAction

def _normalize_string(s):
    """Chuẩn hóa một chuỗi: bỏ dấu, chuyển thành chữ thường, xóa khoảng trắng."""
    return unidecode.unidecode(str(s)).lower().replace(" ", "")

def _find_best_match(dirty_column, clean_options, threshold=80):
    """Tìm tên cột chuẩn phù hợp nhất cho một tên cột 'bẩn'."""
    normalized_dirty = _normalize_string(dirty_column)
    best_score = 0
    best_match = None

    for clean_key, clean_value in clean_options.items():
        normalized_clean = _normalize_string(clean_value)
        score = fuzz.ratio(normalized_dirty, normalized_clean)
        if score > best_score:
            best_score = score
            best_match = clean_key
    
    if best_score >= threshold:
        return best_match
    return None

def infer_and_convert_dates(date_series, default_format="DD/MM/YYYY"):
    """
    Làm sạch và suy luận định dạng ngày mạnh hơn:
    - Hỗ trợ nhiều pattern nhập liệu khác nhau
    - Phân biệt ngày/tháng thông minh
    """
    def clean(s):
        if not isinstance(s, str): return s
        s = s.strip().replace("’", "'")
        if s.startswith("'"): s = s[1:]
        return s

    cleaned = date_series.apply(clean)

    known_formats = [
        "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%Y", "%m-%d-%Y",
        "%d.%m.%Y", "%Y-%m-%d",
        "%Y/%m/%d"
    ]

    def try_parse(value):
        if not isinstance(value, str): return value
        for fmt in known_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None  # không parse được

    parsed = cleaned.apply(try_parse)

    # trường hợp ambiguous: chọn theo default_format
    ambiguous = parsed.isna() & cleaned.str.contains("/", na=False)
    if ambiguous.any():
        if default_format == "DD/MM/YYYY":
            parsed[ambiguous] = pd.to_datetime(cleaned[ambiguous], dayfirst=True, errors="coerce")
        else:
            parsed[ambiguous] = pd.to_datetime(cleaned[ambiguous], dayfirst=False, errors="coerce")

    return parsed


def import_vehicles_from_excel(path, vehicle_manager, location_manager, normalize_owner_func, progress_callback=None):
    """
    Import hàng loạt xe từ file Excel với khả năng nhận diện cột linh hoạt
    và kiểm tra trùng lặp dữ liệu ngay trong file.
    
    Args:
        path: Đường dẫn file Excel
        vehicle_manager: Quản lý xe
        location_manager: Quản lý vị trí
        normalize_owner_func: Hàm chuẩn hóa tên chủ hàng
        progress_callback: Callback function(current, total, message) để cập nhật tiến độ
    """
    def report_progress(current, total, message=""):
        """Helper to safely call progress callback."""
        if progress_callback:
            try:
                progress_callback(current, total, message)
            except Exception:
                pass
    
    try:
        report_progress(0, 100, "Đang đọc file Excel...")
        df = pd.read_excel(path, dtype=str, keep_default_na=False)
        
        expected_cols = {
            'vin': EXPECTED_VIN_COL, 
            'owner': EXPECTED_OWNER_COL, 
            'vehicle_type': EXPECTED_TYPE_COL,
            'so_cont': 'SO CONT', 
            'ngay_cb': 'NGAY CB', 
            'tau': 'TAU',
            'chuyen': 'CHUYEN', 
            'so_kg': 'SO KG'
        }
        
        rename_map = {}
        for col in df.columns:
            best_match_key = _find_best_match(col, expected_cols)
            if best_match_key:
                rename_map[col] = best_match_key
        
        df = df.rename(columns=rename_map)

        if "vin" not in df.columns or "owner" not in df.columns:
            raise ValueError(f"Không thể tự động nhận diện các cột bắt buộc '{EXPECTED_VIN_COL}' và '{EXPECTED_OWNER_COL}' trong file Excel.")

        df['vin'] = df['vin'].str.strip().str.upper()
        
        duplicates = df[df.duplicated(subset=['vin'], keep=False)]
        
        if not duplicates.empty:
            duplicates = duplicates.sort_values(by='vin')
            error_message = "Phát hiện số VIN bị trùng lặp trong file Excel. Vui lòng kiểm tra lại:\n\n"
            for vin, group in duplicates.groupby('vin'):
                line_numbers = [str(i + 2) for i in group.index]
                error_message += f"- VIN: {vin} (xuất hiện ở các dòng: {', '.join(line_numbers)})\n"
            
            return {"success": 0, "errors": len(df), "total": len(df), "error_details": [error_message], "imported_data": []}

    except Exception as e:
        logging.error(f"Lỗi đọc hoặc xử lý file Excel: {e}")

        try:
            log_audit(
                action=AuditAction.IMPORT,
                details={
                    "source": "excel_importer.import_vehicles_from_excel",
                    "file": path,
                    "success": 0,
                    "errors": 0,
                    "total": 0,
                    "fatal_error": str(e),
                    "phase": "read_or_parse",
                },
            )
        except Exception:
            pass
        return {"success": 0, "errors": 0, "total": 0, "error_details": [str(e)], "imported_data": []}

    total = len(df)
    result = {"success": 0, "errors": 0, "total": total, "error_details": [], "imported_data": []}
    
    report_progress(0, total, f"Đang xử lý 0/{total} xe...")
    
    # === LOGIC MỚI: Bỏ qua lỗi và tiếp tục ===
    vehicle_manager.begin_transaction()
    try:
        for i, row in df.iterrows():
            # Update progress for each row
            report_progress(i, total, f"Đang xử lý {i}/{total} xe...")
            
            vin = row["vin"]
            owner = normalize_owner_func(str(row.get("owner", "")))
            
            if not vin or not owner:
                result["errors"] += 1
                result["error_details"].append(f"Dòng {i+2}: Lỗi - Thiếu thông tin VIN hoặc Chủ hàng.")
                continue

            location = location_manager.get_next_available_location()
            if not location:
                result["errors"] += 1
                result["error_details"].append(f"Dòng {i+2} (VIN: {vin}): Lỗi - Hết vị trí trống trong bãi.")
                continue # Bỏ qua dòng này và tiếp tục
            
            location_id = location['id']
            
            vehicle_type = str(row.get("vehicle_type", "")).strip()
            add_result = vehicle_manager.add_vehicle(vin, owner, vehicle_type, datetime.now(), location_id)
            
            if add_result["success"]:
                location_manager.set_location_occupied(location_id, True)
                result["success"] += 1
                
                imported_row = row.to_dict()
                imported_row.update({'vin': vin, 'owner': owner, 'vehicle_type': vehicle_type})
                result["imported_data"].append(imported_row)
            else:
                result["errors"] += 1
                result["error_details"].append(f"Dòng {i+2}: {add_result['message']}")
                # Giải phóng lại vị trí đã lấy vì không thêm xe thành công
                location_manager.set_location_occupied(location_id, False)
        
        # Sau khi lặp xong, commit tất cả các thay đổi thành công
        vehicle_manager.commit_transaction()
        report_progress(total, total, f"Hoàn tất! {result['success']}/{total} xe")

    except Exception as e:
        # Lỗi này chỉ xảy ra nếu có vấn đề nghiêm trọng (ví dụ: CSDL bị khóa)
        vehicle_manager.rollback_transaction()
        # Ghi đè lại kết quả để phản ánh lỗi nghiêm trọng
        result["success"] = 0
        result["errors"] = total
        result["error_details"] = [f"Đã xảy ra lỗi nghiêm trọng: {e}. Toàn bộ quá trình import đã được hủy bỏ."]
        result["imported_data"] = []
        logging.exception("Lỗi nghiêm trọng trong quá trình import Excel.")

    # Audit import summary (best-effort)
    try:
        log_audit(
            action=AuditAction.IMPORT,
            details={
                "source": "excel_importer.import_vehicles_from_excel",
                "file": path,
                "total": result.get("total"),
                "success": result.get("success"),
                "errors": result.get("errors"),
            },
        )
    except Exception:
        pass

    return result