# data_normalizer.py
import json
import logging
import re
import unidecode # Thư viện mạnh mẽ để bỏ dấu tiếng Việt
from difflib import SequenceMatcher
from config import OWNER_MAP_FILE
from exceptions import VINValidationError

# Regex pattern cho VIN theo chuẩn ISO 3779
# VIN phải có 17 ký tự, không chứa I, O, Q (dễ nhầm với 1, 0)
VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')

# Pattern linh hoạt hơn cho các trường hợp VIN không chuẩn (có thể < 17 ký tự)
VIN_PATTERN_FLEXIBLE = re.compile(r'^[A-HJ-NPR-Z0-9]{6,17}$')

# Vietnamese character mapping for common typos/alternatives
VIETNAMESE_CHAR_MAP = {
    # Vowels with accents
    'a': ['à', 'á', 'ả', 'ã', 'ạ', 'ă', 'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ', 'â', 'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ'],
    'e': ['è', 'é', 'ẻ', 'ẽ', 'ẹ', 'ê', 'ề', 'ế', 'ể', 'ễ', 'ệ'],
    'i': ['ì', 'í', 'ỉ', 'ĩ', 'ị'],
    'o': ['ò', 'ó', 'ỏ', 'õ', 'ọ', 'ô', 'ồ', 'ố', 'ổ', 'ỗ', 'ộ', 'ơ', 'ờ', 'ớ', 'ở', 'ỡ', 'ợ'],
    'u': ['ù', 'ú', 'ủ', 'ũ', 'ụ', 'ư', 'ừ', 'ứ', 'ử', 'ữ', 'ự'],
    'y': ['ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ'],
    'd': ['đ'],
}

# Common typo patterns in Vietnamese names
COMMON_TYPOS = {
    'ph': ['f'],  # phương -> fuong
    'ng': ['n'],  # nghĩa -> nia
    'nh': ['n'],  # anh -> an
    'ch': ['c'],  # chính -> cin
    'tr': ['t'],  # trường -> tuong
    'gi': ['d', 'z'],  # giám -> dam/zam
    'kh': ['k'],  # khanh -> kan
    'th': ['t'],  # thành -> tan
    'qu': ['w', 'q'],  # quang -> wang/qang
}


class DataNormalizer:
    """
    Lớp chuyên dụng để xử lý và chuẩn hóa dữ liệu đầu vào không đồng nhất.
    """
    def __init__(self):
        self.owner_map = self._load_json_map(OWNER_MAP_FILE)
        self.owner_map_valid = self._validate_owner_map()  # RELIABILITY FIX Issue #13
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
        except json.JSONDecodeError as e:
            logging.error(f"Lỗi đọc file {file_path}. File không đúng định dạng JSON: {e}")
            return {}
        except Exception as e:
            logging.error(f"Lỗi không xác định khi đọc {file_path}: {e}")
            return {}
    
    def _validate_owner_map(self) -> bool:
        """
        Validate owner_map structure (RELIABILITY FIX Issue #13).
        
        Returns:
            bool: True if map is valid, False otherwise
        """
        if not self.owner_map:
            logging.warning("Owner map is empty - normalization will be disabled")
            return False
        
        if not isinstance(self.owner_map, dict):
            logging.error(f"Owner map is not a dictionary: {type(self.owner_map)}")
            return False
        
        # Validate that all keys and values are strings
        invalid_entries = []
        for key, value in self.owner_map.items():
            if not isinstance(key, str) or not isinstance(value, str):
                invalid_entries.append(f"{key}: {value}")
        
        if invalid_entries:
            logging.error(f"Owner map contains invalid entries (non-string): {invalid_entries[:5]}")
            return False
        
        logging.info(f"Owner map validated successfully: {len(self.owner_map)} entries")
        return True

    def validate_vin(self, vin: str, strict: bool = False) -> dict:
        """
        Kiểm tra tính hợp lệ của VIN (Vehicle Identification Number).
        
        Args:
            vin: Số khung xe cần kiểm tra
            strict: Nếu True, yêu cầu đúng 17 ký tự theo chuẩn ISO 3779 + checksum
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
        
        # SECURITY FIX Issue #12: VIN checksum validation for 17-char VINs
        if strict and len(normalized_vin) == 17:
            checksum_valid, checksum_msg = self._validate_vin_checksum(normalized_vin)
            if not checksum_valid:
                return {
                    "valid": False,
                    "normalized": normalized_vin,
                    "message": f"VIN checksum không hợp lệ: {checksum_msg}"
                }
        
        return {
            "valid": True,
            "normalized": normalized_vin,
            "message": ""
        }
    
    def _validate_vin_checksum(self, vin: str) -> tuple[bool, str]:
        """
        Validate VIN checksum digit (position 9) theo ISO 3779.
        
        Args:
            vin: 17-character VIN string
        
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        if len(vin) != 17:
            return False, "VIN phải có 17 ký tự để kiểm tra checksum"
        
        # VIN transliteration table (ISO 3779)
        transliteration = {
            'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
            'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
            'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9,
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9
        }
        
        # Weight factors for positions
        weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        
        try:
            # Calculate weighted sum
            total = 0
            for i, char in enumerate(vin):
                if char not in transliteration:
                    return False, f"Ký tự không hợp lệ tại vị trí {i+1}: {char}"
                total += transliteration[char] * weights[i]
            
            # Check digit is at position 9 (index 8)
            check_digit = vin[8]
            calculated_check = total % 11
            
            # Check digit can be 0-9 or 'X' (representing 10)
            if calculated_check == 10:
                expected_check = 'X'
            else:
                expected_check = str(calculated_check)
            
            if check_digit != expected_check:
                return False, f"Check digit không đúng. Mong đợi: {expected_check}, thực tế: {check_digit}"
            
            return True, "Checksum hợp lệ"
            
        except Exception as e:
            logging.error(f"Error validating VIN checksum: {e}")
            return False, f"Lỗi kiểm tra checksum: {str(e)}"

    def normalize_vin(self, vin: str) -> str:
        """
        Chuẩn hóa VIN: loại bỏ khoảng trắng, chuyển uppercase, validate checksum ISO 3779.
        
        Raises:
            VINValidationError: Nếu VIN không hợp lệ (length, invalid characters, checksum)
        """
        if not vin:
            raise VINValidationError("VIN không được để trống")
        
        # Clean and uppercase
        normalized = vin.strip().upper().replace(" ", "").replace("-", "")
        
        # Validate length
        if len(normalized) != 17:
            raise VINValidationError(f"VIN phải có đúng 17 ký tự (hiện tại: {len(normalized)})")
        
        # Validate characters (VIN không sử dụng I, O, Q)
        invalid_chars = set('IOQ')
        if any(c in invalid_chars for c in normalized):
            raise VINValidationError("VIN không được chứa ký tự I, O hoặc Q")
        
        # Validate checksum (position 9 is check digit)
        check_digit = normalized[8]
        
        # Transliteration table (ISO 3779)
        transliteration = {
            'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
            'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
            'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9
        }
        
        # Weight factors
        weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        
        # Calculate checksum
        checksum_sum = 0
        for i, char in enumerate(normalized):
            if i == 8:  # Skip check digit position
                continue
            
            # Get numeric value
            if char.isdigit():
                value = int(char)
            else:
                value = transliteration.get(char, 0)
            
            checksum_sum += value * weights[i]
        
        # Calculate check digit
        calculated_check = checksum_sum % 11
        expected_check_char = 'X' if calculated_check == 10 else str(calculated_check)
        
        # Validate
        if check_digit != expected_check_char:
            raise VINValidationError(
                f"VIN checksum không hợp lệ. "
                f"Mong đợi: {expected_check_char}, thực tế: {check_digit}"
            )
        
        return normalized

    def normalize_owner(self, owner_name: str) -> str:
        """
        Chuẩn hóa tên chủ hàng một cách thông minh với fuzzy matching.
        
        Quy trình:
        1. Exact match: Tìm trực tiếp trong map
        2. ASCII match: Bỏ dấu rồi tìm
        3. No-space match: Bỏ khoảng trắng rồi tìm
        4. Fuzzy match: So sánh tương tự (similarity >= 0.8)
        5. Phonetic match: So sánh phát âm tương tự
        6. Default: Trả về giá trị gốc đã uppercase
        """
        if not owner_name:
            return ""
        
        # Validation check
        if not self.owner_map_valid:
            return owner_name.strip().upper()
        
        # Chuẩn hóa input
        cleaned = owner_name.strip()
        key_lower = cleaned.lower()
        key_ascii = unidecode.unidecode(key_lower)
        key_no_space = key_lower.replace(" ", "")
        key_ascii_no_space = key_ascii.replace(" ", "")
        
        # 1. Exact match (giữ dấu)
        if key_lower in self.owner_map:
            return self.owner_map[key_lower]
        
        # 2. ASCII match (bỏ dấu)
        if key_ascii in self.owner_map:
            return self.owner_map[key_ascii]
        
        # 3. No-space match (bỏ khoảng trắng)
        if key_no_space in self.owner_map:
            return self.owner_map[key_no_space]
        
        if key_ascii_no_space in self.owner_map:
            return self.owner_map[key_ascii_no_space]
        
        # 4. Search in map values (reverse lookup)
        for map_key, canonical in self.owner_map.items():
            canonical_lower = canonical.lower()
            canonical_ascii = unidecode.unidecode(canonical_lower)
            
            # Check if input matches canonical name
            if key_lower == canonical_lower or key_ascii == canonical_ascii:
                return canonical
            
            # Check no-space variants
            if key_no_space == canonical_lower.replace(" ", ""):
                return canonical
            if key_ascii_no_space == canonical_ascii.replace(" ", ""):
                return canonical
        
        # 5. Fuzzy match - find best similar match
        best_match = self._fuzzy_match_owner(key_ascii_no_space)
        if best_match:
            return best_match
        
        # 6. Default: uppercase original
        return cleaned.upper()
    
    def _fuzzy_match_owner(self, input_key: str, threshold: float = 0.75) -> str | None:
        """
        Tìm kiếm fuzzy trong owner_map với ngưỡng similarity.
        
        Args:
            input_key: Key đã chuẩn hóa (lowercase, no accent, no space)
            threshold: Ngưỡng similarity tối thiểu (0.0 - 1.0)
        
        Returns:
            Canonical owner name nếu tìm thấy, None nếu không
        """
        best_score = 0.0
        best_match = None
        
        for map_key, canonical in self.owner_map.items():
            # Chuẩn hóa map_key để so sánh
            map_key_normalized = unidecode.unidecode(map_key.lower()).replace(" ", "")
            canonical_normalized = unidecode.unidecode(canonical.lower()).replace(" ", "")
            
            # So sánh với cả key và canonical value
            score_key = SequenceMatcher(None, input_key, map_key_normalized).ratio()
            score_canonical = SequenceMatcher(None, input_key, canonical_normalized).ratio()
            
            max_score = max(score_key, score_canonical)
            
            if max_score > best_score and max_score >= threshold:
                best_score = max_score
                best_match = canonical
        
        if best_match:
            logging.debug(f"Fuzzy match: '{input_key}' -> '{best_match}' (score: {best_score:.2f})")
        
        return best_match
    
    def suggest_owner_matches(self, input_name: str, top_n: int = 5) -> list[dict]:
        """
        Gợi ý các chủ hàng tương tự dựa trên input.
        Hữu ích cho autocomplete hoặc "Did you mean?" feature.
        
        Args:
            input_name: Tên chủ hàng người dùng nhập
            top_n: Số lượng gợi ý tối đa
        
        Returns:
            List of dicts: [{'name': 'PHƯƠNG ANH', 'score': 0.85}, ...]
        """
        if not input_name or not self.owner_map_valid:
            return []
        
        input_normalized = unidecode.unidecode(input_name.strip().lower()).replace(" ", "")
        
        # Collect unique canonical names
        canonical_names = set(self.owner_map.values())
        
        matches = []
        for canonical in canonical_names:
            canonical_normalized = unidecode.unidecode(canonical.lower()).replace(" ", "")
            score = SequenceMatcher(None, input_normalized, canonical_normalized).ratio()
            
            if score > 0.3:  # Minimum threshold for suggestions
                matches.append({
                    'name': canonical,
                    'score': round(score, 2)
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:top_n]
    
    def add_owner_alias(self, alias: str, canonical_name: str) -> bool:
        """
        Thêm alias mới vào owner_map và lưu file.
        
        Args:
            alias: Tên viết tắt/sai chính tả
            canonical_name: Tên chuẩn
        
        Returns:
            bool: True nếu thành công
        """
        try:
            alias_key = alias.strip().lower()
            
            # Thêm vào map
            self.owner_map[alias_key] = canonical_name.strip().upper()
            
            # Lưu file
            with open(OWNER_MAP_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.owner_map, f, ensure_ascii=False, indent=4)
            
            logging.info(f"Added owner alias: '{alias}' -> '{canonical_name}'")
            return True
            
        except Exception as e:
            logging.error(f"Failed to add owner alias: {e}")
            return False
    
    def get_all_canonical_owners(self) -> list[str]:
        """
        Lấy danh sách tất cả tên chủ hàng chuẩn (unique).
        
        Returns:
            List of canonical owner names
        """
        return sorted(set(self.owner_map.values())) if self.owner_map_valid else []

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


# =============================================================================
# MODULE-LEVEL WRAPPER FUNCTIONS
# =============================================================================
# Các hàm này wrap methods của DataNormalizer để dễ import và sử dụng

def validate_vin(vin: str, strict: bool = False) -> dict:
    """
    Kiểm tra tính hợp lệ của VIN (Vehicle Identification Number).
    
    Wrapper function cho DataNormalizer.validate_vin()
    
    Args:
        vin: Số khung xe cần kiểm tra
        strict: Nếu True, yêu cầu đúng 17 ký tự theo chuẩn ISO 3779
               Nếu False, chấp nhận VIN từ 6-17 ký tự
    
    Returns:
        dict với keys:
            - valid (bool): VIN có hợp lệ hay không
            - normalized (str): VIN đã được chuẩn hóa
            - message (str): Thông báo lỗi nếu không hợp lệ
    """
    return normalizer.validate_vin(vin, strict)


def normalize_vin(vin: str) -> str:
    """
    Chuẩn hóa VIN: loại bỏ khoảng trắng, chuyển uppercase.
    
    Wrapper function cho DataNormalizer.normalize_vin()
    
    Args:
        vin: Số khung xe cần chuẩn hóa
    
    Returns:
        str: VIN đã được chuẩn hóa
    """
    return normalizer.normalize_vin(vin)


def normalize_owner(owner_name: str) -> str:
    """
    Chuẩn hóa tên chủ hàng một cách thông minh.
    
    Wrapper function cho DataNormalizer.normalize_owner()
    
    Args:
        owner_name: Tên chủ hàng cần chuẩn hóa
    
    Returns:
        str: Tên chủ hàng đã được chuẩn hóa
    
    Note:
        RELIABILITY FIX Issue #13: Returns input if owner_map is invalid/corrupted
        
    Returns:
        str: Tên chủ hàng đã được chuẩn hóa
    """
    if not normalizer.owner_map_valid:
        # Fallback: return cleaned input without mapping
        logging.debug(f"Owner map invalid - returning cleaned input for: {owner_name}")
        return owner_name.strip().upper() if owner_name else ""
    
    return normalizer.normalize_owner(owner_name)


def normalize_vehicle_type(type_name: str) -> str:
    """
    Chuẩn hóa loại xe.
    
    Wrapper function cho DataNormalizer.normalize_vehicle_type()
    
    Args:
        type_name: Loại xe cần chuẩn hóa
    
    Returns:
        str: Loại xe đã được chuẩn hóa
    """
    return normalizer.normalize_vehicle_type(type_name)