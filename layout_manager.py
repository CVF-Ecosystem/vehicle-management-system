# layout_manager.py
import pandas as pd
import logging
from config import EXPECTED_BLOCK_COL, EXPECTED_ROW_COL, EXPECTED_SLOT_COL

class LayoutManager:
    """
    Lớp logic nghiệp vụ để quản lý việc tạo layout bãi xe.
    Lớp này không tương tác trực tiếp với CSDL mà thông qua LocationManager,
    giúp tách biệt rõ ràng giữa logic nghiệp vụ và logic truy cập dữ liệu.
    """
    def __init__(self, location_manager):
        self.location_manager = location_manager

    def generate_from_rules(self, block, row_start, row_end, slots_per_row):
        """
        Tạo ra một danh sách các vị trí dựa trên các quy tắc và yêu cầu ghi vào CSDL.
        
        Returns:
            tuple: (bool success, int added_count, int skipped_count)
        """
        logging.info(f"Bắt đầu tạo layout theo quy tắc: Block={block}, Rows={row_start}-{row_end}, Slots/Row={slots_per_row}")
        locations_data = []
        try:
            # Chuyển đổi đầu vào sang số nguyên để đảm bảo tính toán đúng
            row_start_num = int(row_start)
            row_end_num = int(row_end)
            slots_per_row_num = int(slots_per_row)
            
            if row_start_num > row_end_num:
                logging.error("Lỗi tạo layout: Dãy bắt đầu không thể lớn hơn dãy kết thúc.")
                return False, 0, 0

            for r in range(row_start_num, row_end_num + 1):
                for s in range(1, slots_per_row_num + 1):
                    locations_data.append({
                        'block': block.strip().upper(),
                        'row': str(r).zfill(2), # Định dạng dãy có 2 chữ số, vd: 01, 02
                        'slot': s
                    })
            
            # Gọi LocationManager để thực hiện ghi CSDL
            return self.location_manager.add_locations_batch(locations_data)
        except ValueError:
            logging.error("Lỗi tạo layout: Dữ liệu dãy và ô phải là số.")
            return False, 0, 0
        except Exception as e:
            logging.error(f"Lỗi không xác định khi tạo layout theo quy tắc: {e}")
            return False, 0, 0

    def generate_from_excel(self, file_path):
        """
        Đọc file Excel, chuẩn hóa dữ liệu và yêu cầu ghi vào CSDL.

        Returns:
            tuple: (bool success, str message, int added_count, int skipped_count)
        """
        logging.info(f"Bắt đầu import layout từ file Excel: {file_path}")
        try:
            df = pd.read_excel(file_path, dtype=str)
            # Chuẩn hóa tên cột: xóa khoảng trắng, chuyển thành chữ hoa
            df.columns = [c.strip().upper() for c in df.columns]
            
            required_cols = {EXPECTED_BLOCK_COL, EXPECTED_ROW_COL, EXPECTED_SLOT_COL}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                msg = f"File Excel thiếu các cột bắt buộc: {', '.join(missing)}"
                logging.error(msg)
                return False, msg, 0, 0

            locations_data = []
            for index, row in df.iterrows():
                # Bỏ qua các dòng trống hoặc thiếu dữ liệu
                if pd.isna(row.get(EXPECTED_BLOCK_COL)) or pd.isna(row.get(EXPECTED_ROW_COL)) or pd.isna(row.get(EXPECTED_SLOT_COL)):
                    continue
                
                locations_data.append({
                    'block': str(row[EXPECTED_BLOCK_COL]).strip().upper(),
                    'row': str(row[EXPECTED_ROW_COL]).strip().zfill(2),
                    'slot': int(row[EXPECTED_SLOT_COL])
                })
            
            ok, added, skipped = self.location_manager.add_locations_batch(locations_data)
            if ok:
                return True, "Import thành công!", added, skipped
            else:
                return False, "Đã xảy ra lỗi trong quá trình ghi vào CSDL.", 0, 0
        except ValueError:
            msg = f"Lỗi import layout: Cột '{EXPECTED_SLOT_COL}' phải chứa giá trị số."
            logging.error(msg)
            return False, msg, 0, 0
        except Exception as e:
            logging.error(f"Lỗi không xác định khi import layout từ Excel: {e}")
            return False, str(e), 0, 0