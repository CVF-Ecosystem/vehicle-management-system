# data_normalizer.py
import json
import logging
import re
import unidecode # Thư viện mạnh mẽ để bỏ dấu tiếng Việt
from config import OWNER_MAP_FILE

# Regex pattern cho VIN theo chuẩn ISO 3779
# VIN phải có 17 ký tự, không chứa I, O, Q (dễ nhầm với 1, 0)
VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')

# Pattern linh hoạt hơn cho các trường hợp VIN không chuẩn (có thể < 17 ký tự)
VIN_PATTERN_FLEXIBLE = re.compile(r'^[A-HJ-NPR-Z0-9]{6,17}$')

class DataNormalizer:
    """
    Lớp chuyên dụng để xử lý và chuẩn hóa dữ liệu đầu vào không đồng nhất.
    """
    def __init__(self):
        self.owner_map = self._load_json_map(OWNER_MAP_FILE)
        # Trong tương lai, bạn có thể thêm các map khác ở đây, ví dụ:
        # self.type_map = self._load_json_map(TYPE_MAP_FILE)

    def _load_json_map(self, file_path):
        """Tải một file map JSON một cách an toàn."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Không tìm thấy file map: {file_path}. Chức năng chuẩn hóa có thể bị hạn chế.")
            return {}
        except json.JSONDecodeError:
            logging.error(f"Lỗi đọc file {file_path}. File không đúng định dạng JSON.")
            return {}

    def validate_vin(self, vin: str, strict: bool = False) -> dict:
        """
        Kiểm tra tính hợp lệ của VIN (Vehicle Identification Number).
        
        Args:
            vin: Số khung xe cần kiểm tra
            strict: Nếu True, yêu cầu đúng 17 ký tự theo chuẩn ISO 3779
                   Nếu False, chấp nhận VIN từ 6-17 ký tự
        
        Returns:
            dict với keys:
                - valid (bool): VIN có hợp lệ hay không
                - normalized (str): VIN đã được chuẩn hóa (uppercase, stripped)
                - message (str): Thông báo lỗi nếu không hợp lệ
        """
        if not vin:
            return {
                "valid": False,
                "normalized": "",
                "message": "VIN không được để trống"
            }
        
        # Chuẩn hóa: xóa khoảng trắng, chuyển uppercase
        normalized_vin = vin.strip().upper().replace(" ", "").replace("-", "")
        
        # Kiểm tra ký tự không hợp lệ (I, O, Q không được phép trong VIN)
        invalid_chars = set(re.findall(r'[IOQ]', normalized_vin))
        if invalid_chars:
            return {
                "valid": False,
                "normalized": normalized_vin,
                "message": f"VIN chứa ký tự không hợp lệ: {', '.join(invalid_chars)} (I, O, Q không được phép)"
            }
        
        # Kiểm tra ký tự đặc biệt
        if not re.match(r'^[A-Z0-9]+$', normalized_vin):
            return {
                "valid": False,
                "normalized": normalized_vin,
                "message": "VIN chỉ được chứa chữ cái và số"
            }
        
        # Chọn pattern dựa trên chế độ strict
        pattern = VIN_PATTERN if strict else VIN_PATTERN_FLEXIBLE
        
        if not pattern.match(normalized_vin):
            if strict:
                return {
                    "valid": False,
                    "normalized": normalized_vin,
                    "message": f"VIN phải có đúng 17 ký tự (hiện tại: {len(normalized_vin)} ký tự)"
                }
            else:
                return {
                    "valid": False,
                    "normalized": normalized_vin,
                    "message": f"VIN phải có từ 6-17 ký tự (hiện tại: {len(normalized_vin)} ký tự)"
                }
        
        return {
            "valid": True,
            "normalized": normalized_vin,
            "message": ""
        }

    def normalize_vin(self, vin: str) -> str:
        """
        Chuẩn hóa VIN: loại bỏ khoảng trắng, chuyển uppercase.
        Không validate, chỉ normalize.
        """
        if not vin:
            return ""
        return vin.strip().upper().replace(" ", "").replace("-", "")

    def normalize_owner(self, owner_name: str) -> str:
        """
        Chuẩn hóa tên chủ hàng một cách thông minh.
        Quy trình:
        1. Chuyển thành chữ thường, xóa khoảng trắng thừa.
        2. Tìm kiếm trong map với key gốc (còn dấu).
        3. Nếu không thấy, thử bỏ dấu của key rồi tìm lại.
        4. Nếu vẫn không thấy, trả về giá trị gốc đã được viết hoa.
        """
        if not owner_name:
            return ""
        
        # 1. Tạo key gốc (giữ dấu)
        key_original = owner_name.strip().lower()
        if key_original in self.owner_map:
            return self.owner_map[key_original]
            
        # 2. Tạo key không dấu để tìm kiếm linh hoạt hơn
        key_unidecoded = unidecode.unidecode(key_original)
        if key_unidecoded in self.owner_map:
            return self.owner_map[key_unidecoded]
            
        # 3. Mặc định: Nếu không tìm thấy trong map, trả về giá trị gốc đã được viết hoa
        return owner_name.strip().upper()

    def normalize_vehicle_type(self, type_name: str) -> str:
        """
        Chuẩn hóa loại xe. Hiện tại chỉ làm sạch và viết hoa.
        Có thể mở rộng để sử dụng map trong tương lai.
        """
        if not type_name:
            return ""
        return type_name.strip().upper()

# Tạo một instance duy nhất (Singleton pattern) để toàn bộ ứng dụng có thể
# import và sử dụng mà không cần khởi tạo lại.
normalizer = DataNormalizer()