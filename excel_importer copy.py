# excel_importer.py
import pandas as pd
from datetime import datetime
import logging
import re
from thefuzz import fuzz
import unidecode
from config import DEFAULT_DATE_FORMAT 


from config import (
    EXPECTED_VIN_COL, EXPECTED_OWNER_COL, EXPECTED_TYPE_COL
)

def _normalize_string(s):
    """Chuẩn hóa một chuỗi: bỏ dấu, chuyển thành chữ thường, xóa khoảng trắng."""
    return unidecode.unidecode(str(s)).lower().replace(" ", "")

def _find_best_match(dirty_column, clean_options, threshold=80):
    """Tìm tên cột chuẩn phù hợp nhất cho một tên cột 'bẩn'."""
    normalized_dirty = _normalize_string(dirty_column)
    best_score = 0
    best_match = None
    for clean_key, clean_value in clean_options.items():
        score = fuzz.ratio(normalized_dirty, _normalize_string(clean_value))
        if score > best_score:
            best_score = score
            best_match = clean_key
    return best_match if best_score >= threshold else None

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


def import_vehicles_from_excel(path, vehicle_manager, entity_manager, normalize_owner_func):
    try:
        df = pd.read_excel(path, dtype=str, keep_default_na=False)
        
        expected_cols = {
            'vin': EXPECTED_VIN_COL, 'owner': EXPECTED_OWNER_COL, 'vehicle_type': EXPECTED_TYPE_COL,
            'so_cont': 'SO CONT', 'ngay_cb': 'NGAY CB', 'tau': 'TAU',
            'chuyen': 'CHUYEN', 'so_kg': 'SO KG'
        }
        
        rename_map = {}
        for col in df.columns:
            best_match_key = _find_best_match(col, expected_cols)
            if best_match_key: rename_map[col] = best_match_key
        
        df = df.rename(columns=rename_map)

        # --- SỬA LỖI: Kiểm tra sự tồn tại của cột trước khi xử lý ---
        if 'ngay_cb' in df.columns:
            df['ngay_cb_dt'] = infer_and_convert_dates(df['ngay_cb'])
            # Chỉ thực hiện định dạng nếu cột 'ngay_cb_dt' thực sự là kiểu datetime
            if pd.api.types.is_datetime64_any_dtype(df['ngay_cb_dt']):
                df['ngay_cb'] = df['ngay_cb_dt'].dt.strftime('%d/%m/%Y').fillna('')
            else:
                # Nếu không, giữ lại giá trị gốc đã được làm sạch
                df['ngay_cb'] = df['ngay_cb'].fillna('')
        # ---------------------------------------------------------
        
        if "vin" not in df.columns or "owner" not in df.columns:
            raise ValueError(f"Không thể tự động nhận diện các cột bắt buộc '{EXPECTED_VIN_COL}' và '{EXPECTED_OWNER_COL}'.")

        df['vin'] = df['vin'].str.strip().str.upper()
        duplicates = df[df.duplicated(subset=['vin'], keep=False)]
        
        if not duplicates.empty:
            duplicates = duplicates.sort_values(by='vin')
            error_message = "Phát hiện số VIN bị trùng lặp trong file Excel. Toàn bộ quá trình import đã bị hủy.\nVui lòng kiểm tra lại:\n\n"
            for vin, group in duplicates.groupby('vin'):
                line_numbers = [str(i + 2) for i in group.index]
                error_message += f"- VIN: {vin} (xuất hiện ở các dòng: {', '.join(line_numbers)})\n"
            return {"success": 0, "errors": len(df), "total": len(df), "error_details": [error_message], "imported_data": []}

    except Exception as e:
        logging.error(f"Lỗi đọc hoặc xử lý file Excel: {e}")
        return {"success": 0, "errors": 0, "total": 0, "error_details": [str(e)], "imported_data": []}

    total = len(df)
    result = {"success": 0, "errors": 0, "total": total, "error_details": [], "imported_data": []}
    
    # --- SỬA LỖI: Gọi hàm transaction từ đối tượng driver (db) ---
    vehicle_manager.db.begin_transaction()
    try:
        for i, row in df.iterrows():
            # ... (toàn bộ logic xử lý từng dòng giữ nguyên)
            vin = row.get("vin")
            owner = normalize_owner_func(str(row.get("owner", "")))
            
            if not vin or not owner:
                result["errors"] += 1
                result["error_details"].append(f"Dòng {i+2}: Lỗi - Thiếu thông tin VIN hoặc Chủ hàng.")
                continue

            location = entity_manager.get_next_available_location()
            if not location:
                result["errors"] += 1
                result["error_details"].append(f"Dòng {i+2} (VIN: {vin}): Lỗi - Hết vị trí trống trong bãi.")
                continue
            
            location_id = location['id']
            
            vehicle_type = str(row.get("vehicle_type", "")).strip()
            add_result = vehicle_manager.add_vehicle(vin, owner, vehicle_type, datetime.now(), location_id)
            
            if add_result["success"]:
                entity_manager.set_location_occupied(location_id, True)
                result["success"] += 1
                
                imported_row = row.to_dict()
                imported_row.update({'vin': vin, 'owner': owner, 'vehicle_type': vehicle_type, 'location_name': location['name']})
                result["imported_data"].append(imported_row)
            else:
                result["errors"] += 1
                result["error_details"].append(f"Dòng {i+2}: {add_result['message']}")
                entity_manager.set_location_occupied(location_id, False)
        
        if result["errors"] > 0:
            # --- SỬA LỖI ---
            vehicle_manager.db.rollback_transaction()
            result["success"] = 0
            result["imported_data"] = []
            result["error_details"].insert(0, f"Phát hiện {result['errors']} lỗi. Toàn bộ quá trình import đã được hủy bỏ để đảm bảo an toàn dữ liệu.")
        else:
            # --- SỬA LỖI ---
            vehicle_manager.db.commit_transaction()

    except Exception as e:
        # --- SỬA LỖI ---
        vehicle_manager.db.rollback_transaction()
        result["success"] = 0; result["errors"] = total; result["imported_data"] = []
        result["error_details"] = [f"Đã xảy ra lỗi nghiêm trọng: {e}. Toàn bộ quá trình import đã được hủy bỏ."]
        logging.exception("Lỗi nghiêm trọng trong quá trình import Excel.")

    return result