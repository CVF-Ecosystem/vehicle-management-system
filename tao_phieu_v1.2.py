# Đặt tên file là: tao_phieu_v1.2.py
import pandas as pd
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import os
import sys
import datetime
import qrcode
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, Menu
import configparser
import threading
import logging
import shutil
import re # Thêm thư viện re để xử lý SO KG
from tkinter import ttk # Explicitly import ttk for Style

# --- Cấu hình Logging (Không đổi) ---
log_filename = 'app_log.txt'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_filename, encoding='utf-8')])
logging.info("--- Khởi động ứng dụng ---")

# --- Cấu hình mặc định (Không đổi) ---
CONFIG_FILE = 'config_phieuvc_v1.1.ini' # Đổi tên file config
DEFAULT_QR_SIZE = 35
ARCHIVE_FOLDER_NAME = "Archive"
DEFAULT_LANGUAGE = 'vi'
ERROR_REPORT_FILENAME = "ErrorReport_{timestamp}.xlsx"

# --- TỪ ĐIỂN CHUẨN HÓA CHỦ HÀNG ---
# Dùng để chuẩn hóa tên chủ hàng từ các biến thể về một định dạng duy nhất (IN HOA)
# Key: Biến thể tên (viết thường, không dấu hoặc có dấu)
# Value: Tên chuẩn (theo định dạng mong muốn - IN HOA)
OWNER_NORMALIZATION_MAP = {
    "minh đức": "MINH ĐỨC",
    "minh duc": "MINH ĐỨC",
    "minh đưc": "MINH ĐỨC", # Thêm trường hợp sai chính tả
    "phương anh": "PHƯƠNG ANH",
    "phuong anh": "PHƯƠNG ANH",
    "phuonganh": "PHƯƠNG ANH",
    "tín nghĩa": "TÍN NGHĨA",
    "Tín Nghĩa": "TÍN NGHĨA",
    "tín Nghĩa": "TÍN NGHĨA",
    "tin nghia": "TÍN NGHĨA",
    "tin ngia": "TÍN NGHĨA",
    "truong nam": "TRƯỜNG NAM",
    "phú sơn": "PHÚ SƠN",
    "phu son": "PHÚ SƠN",
    "phú linh": "PHÚ LINH",
    "phu linh": "PHÚ LINH",
    # --- Thêm các biến thể khác nếu bạn phát hiện ---
}
# ------------------------------------------

# --- Dữ liệu đa ngôn ngữ (Không đổi) ---
translations = {
    "app_title": {"vi": "Tạo phiếu vận chuyển tự động", "en": "Automated Transfer Slip Generator"},
    "file_frame_title": {"vi": "Dữ liệu Nhập/Xuất", "en": "Data Input/Output"},
    "label_excel_path": {"vi": "File/Thư mục nhập(Excel):", "en": "File/Folder Input(Excel):"},
    "button_select_file": {"vi": "Chọn File", "en": "Select File"},
    "button_select_dir": {"vi": "Chọn Thư mục", "en": "Select Folder"},
    "label_template_path": {"vi": "File mẫu(Word):", "en": "Template File(Word):"},
    "button_select": {"vi": "Chọn...", "en": "Select..."},
    "label_output_dir": {"vi": "Thư mục xuất:", "en": "Output Folder:"},
    "label_output_file": {"vi": "File xuất:", "en": "Output File:"},
    "button_save_as": {"vi": "Lưu", "en": "Save As"},
    "button_settings": {"vi": "Cài đặt", "en": "Settings"},
    "button_generate": {"vi": "Tạo phiếu", "en": "Generate"},
    "check_ignore_errors": {"vi": "Bỏ qua lỗi dữ liệu", "en": "Ignore data errors"},
    "check_archive": {"vi": "Lưu file Excel đã xử lý", "en": "Archive processed Excel files"},
    "log_frame_title": {"vi": "Log", "en": "Log"},
    "status_ready": {"vi": "Sẵn sàng.", "en": "Ready."},
    "status_processing_file": {"vi": "Đang xử lý file {current}/{total}: {filename}", "en": "Processing file {current}/{total}: {filename}"},
    "status_processing_single_file": {"vi": "Đang xử lý file: {filename}", "en": "Processing file: {filename}"},
    "status_processed_files": {"vi": "Đã xử lý {processed}/{total} file.", "en": "Processed {processed}/{total} files."},
    "status_processed_single_success": {"vi": "Đã xử lý thành công file: {filename}", "en": "Successfully processed file: {filename}"},
    "status_processed_single_error": {"vi": "Xử lý file {filename} có lỗi.", "en": "Processed file {filename} with errors."},
    "status_author": {"vi": "Phát triển bởi: Tiền-Cảng Tân Thuận", "en": "Developed by: Tien-Tan Thuan Port"},
    "menu_language": {"vi": "Ngôn ngữ", "en": "Language"},
    "menu_vietnamese": {"vi": "Tiếng Việt", "en": "Vietnamese"},
    "menu_english": {"vi": "Tiếng Anh", "en": "English"},
    "settings_window_title": {"vi": "Cài đặt", "en": "Settings"},
    "label_qr_size": {"vi": "Kích thước mã QR (mm):", "en": "QR Code Size (mm):"},
    "button_save": {"vi": "Lưu", "en": "Save"},
    "button_cancel": {"vi": "Hủy", "en": "Cancel"},
    "msg_error_title": {"vi": "Lỗi", "en": "Error"},
    "msg_info_title": {"vi": "Thông tin", "en": "Information"},
    "msg_warning_title": {"vi": "Cảnh báo", "en": "Warning"},
    "msg_question_title": {"vi": "Xác nhận", "en": "Confirmation"},
    "msg_select_all_paths": {"vi": "Vui lòng chọn đầy đủ:\n- File/Thư mục Excel\n- File Template\n- Thư mục Output (nếu chọn thư mục Excel)\n- File Output (nếu chọn file Excel)", "en": "Please select all required paths:\n- Excel File/Folder\n- Template File\n- Output Folder (if Excel folder selected)\n- Output File (if Excel file selected)"},
    "msg_path_not_exist": {"vi": "Đường dẫn không tồn tại:\n{path}", "en": "Path does not exist:\n{path}"},
    "msg_template_invalid": {"vi": "File Template không hợp lệ:\n{path}", "en": "Invalid Template File:\n{path}"},
    "msg_output_dir_invalid": {"vi": "Thư mục Output không hợp lệ:\n{path}", "en": "Invalid Output Folder:\n{path}"},
    "msg_output_file_invalid": {"vi": "Đường dẫn File Output không hợp lệ hoặc chưa chọn:\n{path}", "en": "Invalid or unselected Output File path:\n{path}"},
    "msg_excel_must_be_xlsx": {"vi": "File Excel được chọn phải có định dạng .xlsx", "en": "Selected Excel file must be in .xlsx format"},
    "msg_no_xlsx_found": {"vi": "Không tìm thấy file .xlsx nào trong thư mục:\n{path}", "en": "No .xlsx files found in the folder:\n{path}"},
    "msg_cannot_read_excel_dir": {"vi": "Không thể đọc nội dung thư mục Excel:\n{error}", "en": "Cannot read Excel folder content:\n{error}"},
    "msg_settings_saved": {"vi": "Đã lưu cài đặt.", "en": "Settings saved."},
    "msg_invalid_value": {"vi": "Giá trị không hợp lệ: '{value}'.\nVui lòng nhập một số nguyên dương.\n({error})", "en": "Invalid value: '{value}'.\nPlease enter a positive integer.\n({error})"},
    "msg_qr_updated": {"vi": "Đã cập nhật kích thước QR thành: {value}mm", "en": "QR size updated to: {value}mm"},
    "msg_batch_complete_success": {"vi": "Đã xử lý thành công {processed}/{total} file Excel.", "en": "Successfully processed {processed}/{total} Excel files."},
    "msg_single_complete_success": {"vi": "Đã tạo thành công file:\n{path}", "en": "Successfully created file:\n{path}"},
    "msg_single_complete_error": {"vi": "Xử lý file thất bại. Bạn có muốn xuất báo cáo lỗi chi tiết không?", "en": "File processing failed. Do you want to export a detailed error report?"},
    "msg_batch_complete_error_summary": {"vi": "Đã xử lý {processed}/{total} file.\n\nCó lỗi xảy ra. Bạn có muốn xuất báo cáo lỗi chi tiết ra file Excel không?", "en": "Processed {processed}/{total} files.\n\nErrors occurred. Do you want to export a detailed error report to an Excel file?"},
    "msg_batch_error_file_details": {"vi": "\n- {filename} ({count} lỗi/cảnh báo):\n", "en": "\n- {filename} ({count} errors/warnings):\n"},
    "msg_batch_error_limit_display": {"vi": "      ...\n", "en": "      ...\n"},
    "msg_batch_error_check_log": {"vi": "\nVui lòng kiểm tra Log hoặc file app_log.txt để biết chi tiết.", "en": "\nPlease check the Log or app_log.txt file for details."},
    "msg_error_report_success": {"vi": "Đã xuất báo cáo lỗi thành công:\n{path}", "en": "Successfully exported error report:\n{path}"},
    "msg_error_report_failed": {"vi": "Xuất báo cáo lỗi thất bại:\n{error}", "en": "Failed to export error report:\n{error}"},
    "log_excel_selected": {"vi": "Đã chọn file Excel: {path}", "en": "Selected Excel file: {path}"},
    "log_excel_dir_selected": {"vi": "Đã chọn thư mục Excel: {path}", "en": "Selected Excel folder: {path}"},
    "log_template_selected": {"vi": "Đã chọn file mẫu: {path}", "en": "Selected template file: {path}"},
    "log_output_dir_selected": {"vi": "Đã chọn thư mục Output: {path}", "en": "Selected Output folder: {path}"},
    "log_output_file_selected": {"vi": "Đã chọn file Output: {path}", "en": "Selected Output file: {path}"},
    "log_preparing_files": {"vi": "Chuẩn bị xử lý {count} file Excel...", "en": "Preparing to process {count} Excel files..."},
    "log_preparing_single_file": {"vi": "Chuẩn bị xử lý file Excel: {filename}", "en": "Preparing to process Excel file: {filename}"},
    "log_starting_process": {"vi": "Bắt đầu xử lý {count} file từ: {path}", "en": "Starting processing {count} files from: {path}"},
    "log_starting_single_process": {"vi": "Bắt đầu xử lý file: {path}", "en": "Starting processing file: {path}"},
    "log_processing_file_start": {"vi": "--- Bắt đầu xử lý file: {filename} ---", "en": "--- Starting processing file: {filename} ---"},
    "log_reading_excel": {"vi": "Đang đọc file Excel: {path}", "en": "Reading Excel file: {path}"},
    "log_read_rows": {"vi": "Đã đọc {count} dòng.", "en": "Read {count} rows."},
    "log_excel_empty": {"vi": "Lỗi: File Excel rỗng.", "en": "Error: Excel file is empty."},
    "log_missing_columns": {"vi": "Lỗi: File thiếu cột: {columns}", "en": "Error: File missing columns: {columns}"},
    "log_loading_template": {"vi": "Đang nạp template: {filename}", "en": "Loading template: {filename}"},
    "log_checking_rows": {"vi": "Kiểm tra dữ liệu từng dòng...", "en": "Checking data row by row..."},
    "log_critical_error": {"vi": "    Lỗi Nghiêm Trọng: {message}", "en": "    Critical Error: {message}"},
    "log_error": {"vi": "    Lỗi: {message}", "en": "    Error: {message}"},
    "log_warning": {"vi": "    Cảnh báo: {message}", "en": "    Warning: {message}"},
    "log_warning_invalid_qr_size": {"vi": "Cảnh báo: Giá trị qr_size_mm không hợp lệ. Sử dụng mặc định: {default}mm", "en": "Warning: Invalid qr_size_mm value. Using default: {default}mm"},
    "log_stop_processing_critical": {"vi": "\nLỗi nghiêm trọng ở dòng {row}. Dừng xử lý file này.", "en": "\nCritical error at row {row}. Stopping processing this file."},
    "log_no_context": {"vi": "Lỗi: Không tạo được context nào (có thể do lỗi nghiêm trọng hoặc không có dữ liệu hợp lệ).", "en": "Error: No context could be created (possibly due to critical errors or no valid data)."}, # Sửa lại thông báo lỗi
    "log_prepared_contexts": {"vi": "Đã chuẩn bị {count} context(s).", "en": "Prepared {count} context(s)."},
    "log_data_warnings_header": {"vi": "--- Cảnh báo/Lỗi dữ liệu đã phát hiện ---", "en": "--- Data Warnings/Errors Detected ---"},
    "log_rendering_word": {"vi": "Render tài liệu Word...", "en": "Rendering Word document..."},
    "log_saving_word": {"vi": "Lưu file Word: {filename}", "en": "Saving Word file: {filename}"},
    "log_word_success": {"vi": "-> Đã tạo file Word thành công.", "en": "-> Successfully created Word file."},
    "log_system_error_header": {"vi": "\n--- LỖI HỆ THỐNG KHI XỬ LÝ FILE {filename} ---", "en": "\n--- SYSTEM ERROR WHILE PROCESSING FILE {filename} ---"},
    "log_moving_archive": {"vi": "  -> Đang di chuyển file đã xử lý vào: {path}", "en": "  -> Moving processed file to: {path}"},
    "log_move_success": {"vi": "  -> Di chuyển thành công.", "en": "  -> Move successful."},
    "log_move_error": {"vi": "    Lỗi: Lỗi khi di chuyển file {filename} vào {folder}: {error}", "en": "    Error: Error moving file {filename} to {folder}: {error}"},
    "log_batch_complete_all_success": {"vi": "\n--- HOÀN THÀNH TẤT CẢ (BATCH) ---", "en": "\n--- ALL COMPLETED SUCCESSFULLY (BATCH) ---"},
    "log_single_complete_success": {"vi": "\n--- HOÀN THÀNH (FILE ĐƠN) ---", "en": "\n--- COMPLETED (SINGLE FILE) ---"},
    "log_batch_complete_with_errors": {"vi": "\n--- HOÀN THÀNH VỚI LỖI/CẢNH BÁO (BATCH) ---", "en": "\n--- COMPLETED WITH ERRORS/WARNINGS (BATCH) ---"},
    "log_single_complete_with_errors": {"vi": "\n--- HOÀN THÀNH VỚI LỖI/CẢNH BÁO (FILE ĐƠN) ---", "en": "\n--- COMPLETED WITH ERRORS/WARNINGS (SINGLE FILE) ---"},
    "log_missing_lib_error": {"vi": "\nLỗi: Thiếu thư viện '{name}'. Không thể chạy ứng dụng.", "en": "\nError: Missing library '{name}'. Cannot run the application."},
    "log_install_libs": {"vi": "Vui lòng chạy lệnh sau trong Command Prompt/Terminal:", "en": "Please run the following command in Command Prompt/Terminal:"},
    "log_press_enter": {"vi": "Nhấn Enter để thoát.", "en": "Press Enter to exit."},
    "log_app_closed": {"vi": "--- Đóng ứng dụng ---", "en": "--- Closing application ---"},
    "log_config_saved": {"vi": "Đã lưu cấu hình vào: {path}", "en": "Configuration saved to: {path}"},
    "log_error_saving_config": {"vi": "Lỗi lưu file cấu hình {path}: {error}", "en": "Error saving config file {path}: {error}"},
    "log_config_loaded": {"vi": "Đã đọc cấu hình từ: {path}", "en": "Configuration loaded from: {path}"},
    "log_error_loading_config": {"vi": "Lỗi đọc file cấu hình {path}: {error}. Sử dụng cấu hình mặc định.", "en": "Error reading config file {path}: {error}. Using default configuration."},
    "log_config_not_found": {"vi": "Không tìm thấy file cấu hình {path}. Tạo file mới...", "en": "Config file {path} not found. Creating new file..."},
    "log_qr_updated_log": {"vi": "Kích thước QR được cập nhật thành {value}mm", "en": "QR size updated to {value}mm"},
    "log_gui_ready": {"vi": "Giao diện ứng dụng đã sẵn sàng.", "en": "Application GUI ready."},
    "error_report_sheet_name": {"vi": "Chi tiết lỗi", "en": "Error Details"},
    "error_report_col_file": {"vi": "File Excel nguồn", "en": "Source Excel File"},
    "error_report_col_row": {"vi": "Dòng trong Excel", "en": "Excel Row"},
    "error_report_col_column": {"vi": "Cột bị ảnh hưởng", "en": "Affected Column"},
    "error_report_col_value": {"vi": "Giá trị gốc (nếu có)", "en": "Original Value (if any)"},
    "error_report_col_type": {"vi": "Loại lỗi", "en": "Error Type"},
    "error_report_col_message": {"vi": "Thông báo lỗi", "en": "Error Message"},
    "error_type_missing_column": {"vi": "Thiếu cột", "en": "Missing Column"},
    "error_type_missing_value": {"vi": "Thiếu giá trị", "en": "Missing Value"},
    "error_type_duplicate_value": {"vi": "Trùng giá trị", "en": "Duplicate Value"},
    "error_type_invalid_format": {"vi": "Sai định dạng", "en": "Invalid Format"},
    "error_type_system": {"vi": "Lỗi hệ thống", "en": "System Error"},
    "error_type_archive": {"vi": "Lỗi lưu trữ", "en": "Archive Error"},
    "error_type_qr": {"vi": "Lỗi tạo QR", "en": "QR Generation Error"},
    "error_type_image": {"vi": "Lỗi chèn ảnh QR", "en": "QR Image Insertion Error"},
    "error_type_empty_file": {"vi": "File rỗng", "en": "Empty File"},
    "error_type_no_context": {"vi": "Không có dữ liệu hợp lệ", "en": "No Valid Data"},
}

# --- Hàm đọc/ghi cấu hình (Không đổi) ---
def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile: config.write(configfile)
        logging.info(f"Đã lưu cấu hình vào: {CONFIG_FILE}")
    except Exception as e: logging.error(f"Lỗi lưu file cấu hình {CONFIG_FILE}: {e}")
def load_config():
    config = configparser.ConfigParser();
    if os.path.exists(CONFIG_FILE):
        try: config.read(CONFIG_FILE, encoding='utf-8'); logging.info(f"Đã đọc cấu hình từ: {CONFIG_FILE}")
        except Exception as e: logging.error(f"Lỗi đọc file cấu hình {CONFIG_FILE}: {e}. Sử dụng cấu hình mặc định."); config = configparser.ConfigParser()
    if 'Paths' not in config: config.add_section('Paths')
    if 'Settings' not in config: config.add_section('Settings')
    if 'last_excel_file' not in config['Paths']: config['Paths']['last_excel_file'] = ''
    if 'last_excel_dir' not in config['Paths']: config['Paths']['last_excel_dir'] = ''
    if 'last_template' not in config['Paths']: config['Paths']['last_template'] = ''
    if 'last_output_dir' not in config['Paths']: config['Paths']['last_output_dir'] = ''
    if 'last_output_file' not in config['Paths']: config['Paths']['last_output_file'] = ''
    if 'qr_size_mm' not in config['Settings']: config['Settings']['qr_size_mm'] = str(DEFAULT_QR_SIZE)
    if 'archive_processed' not in config['Settings']: config['Settings']['archive_processed'] = 'False'
    if 'language' not in config['Settings']: config['Settings']['language'] = DEFAULT_LANGUAGE
    if 'ignore_errors' not in config['Settings']: config['Settings']['ignore_errors'] = 'False'
    if config['Settings']['language'] not in ['vi', 'en']: config['Settings']['language'] = DEFAULT_LANGUAGE
    return config

# --- Hàm chọn file/thư mục (Không đổi) ---
def select_file_or_dir(is_dir=False, title="Chọn...", filetypes=None, initial_dir_or_file=""):
    root = tk.Tk(); root.withdraw(); initialdir = None; initialfile = None
    if initial_dir_or_file and os.path.exists(initial_dir_or_file):
        if os.path.isdir(initial_dir_or_file): initialdir = initial_dir_or_file
        elif os.path.isfile(initial_dir_or_file):
            initialdir = os.path.dirname(initial_dir_or_file)
            if not is_dir: initialfile = os.path.basename(initial_dir_or_file)
    if is_dir: path = filedialog.askdirectory(title=title, initialdir=initialdir)
    else: path = filedialog.askopenfilename(title=title, filetypes=filetypes, initialdir=initialdir, initialfile=initialfile)
    root.destroy(); return path

# --- Hàm xử lý chính (generate_word_from_excel_jinja - ĐÃ CẬP NHẬT) ---
def generate_word_from_excel_jinja(excel_path, template_path, output_path, config, ignore_row_errors, log_callback, progress_callback):
    """
    Hàm chính để đọc file Excel, xử lý dữ liệu, tạo mã QR và điền vào template Word.

    Args:
        excel_path (str): Đường dẫn đến file Excel đầu vào.
        template_path (str): Đường dẫn đến file template Word (.docx).
        output_path (str): Đường dẫn để lưu file Word đầu ra.
        config (ConfigParser): Đối tượng cấu hình ứng dụng.
        ignore_row_errors (bool): True nếu bỏ qua các lỗi không nghiêm trọng ở từng dòng.
        log_callback (function): Hàm để gửi thông điệp log về GUI.
        progress_callback (function): Hàm để cập nhật thanh tiến trình GUI.

    Returns:
        tuple: (bool, list) - (True nếu thành công, danh sách lỗi chi tiết)
                               (False nếu thất bại, danh sách lỗi chi tiết)
    """
    current_lang = config.get('Settings', 'language', fallback=DEFAULT_LANGUAGE)
    excel_basename = os.path.basename(excel_path)

    # --- Hàm tiện ích nội bộ ---
    def get_translation_local(key, **kwargs):
        """Lấy bản dịch cho ngôn ngữ hiện tại."""
        try: return translations[key][current_lang].format(**kwargs)
        except KeyError: return key

    def add_error(error_list, row, col, value, err_type_key, msg):
        """Thêm lỗi vào danh sách và ghi log."""
        error_list.append({
            'file': excel_basename,
            'row': row,
            'column': col,
            'value': value,
            'type': err_type_key, # Key của loại lỗi (để dịch sau)
            'message': msg
        })
        # Xác định mức độ log dựa trên loại lỗi
        log_level = logging.ERROR if err_type_key == "error_type_critical" else logging.WARNING
        log_prefix_key = "log_critical_error" if err_type_key == "error_type_critical" else ("log_error" if err_type_key.startswith("error_type_") and err_type_key != "error_type_warning" else "log_warning")
        log_prefix = get_translation_local(log_prefix_key).split(':')[0] # Lấy phần đầu (Lỗi/Cảnh báo)
        log_callback(f"{log_prefix}: Dòng {row}: {msg}") # Gửi log về GUI
        logging.log(log_level, f"File: {excel_basename}, Dòng: {row}, Cột: {col}, Lỗi: {msg}, Giá trị: {value}")

    # --- Khởi tạo ---
    detailed_errors = [] # Danh sách lưu trữ tất cả lỗi/cảnh báo chi tiết
    if not output_path:
        err_msg = "Đường dẫn file output không được cung cấp hoặc không hợp lệ."
        add_error(detailed_errors, None, None, None, "error_type_system", err_msg)
        return False, detailed_errors

    try:
        qr_code_size_mm = int(config.get('Settings', 'qr_size_mm', fallback=DEFAULT_QR_SIZE))
        if qr_code_size_mm <= 0: raise ValueError("QR size must be positive")
    except ValueError:
        log_callback(get_translation_local("log_warning_invalid_qr_size", default=DEFAULT_QR_SIZE))
        qr_code_size_mm = DEFAULT_QR_SIZE

    # Các cột bắt buộc phải có trong file Excel
    required_columns = ['STT', 'LOAI XE', 'SO KHUNG', 'SO CONT', 'NGAY CB', 'TAU', 'CHUYEN', 'CHU HANG', 'SO KG']
    critical_error_occurred = False # Cờ đánh dấu lỗi nghiêm trọng
    processed_so_khung = {} # Dictionary để kiểm tra trùng SO KHUNG

    try:
        # --- Đọc File Excel ---
        log_callback(get_translation_local("log_processing_file_start", filename=excel_basename))
        logging.info(f"Đang đọc file Excel: {excel_path}")
        # Đọc Excel, đảm bảo NGAY CB đọc dạng text, SO KHUNG/CONT dạng text để giữ số 0 đứng đầu (nếu có)
        df = pd.read_excel(excel_path, dtype={'NGAY CB': str, 'SO KHUNG': str, 'SO CONT': str})
        total_rows = len(df)
        log_callback(get_translation_local("log_read_rows", count=total_rows))
        progress_callback(0) # Bắt đầu tiến trình

        # Kiểm tra file rỗng
        if df.empty:
            err_msg = get_translation_local("log_excel_empty")
            add_error(detailed_errors, None, None, None, "error_type_empty_file", err_msg)
            return False, detailed_errors

        # Kiểm tra thiếu cột bắt buộc
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            err_msg = get_translation_local("log_missing_columns", columns=', '.join(missing_cols))
            # Đây là lỗi nghiêm trọng, không thể tiếp tục
            add_error(detailed_errors, None, ', '.join(missing_cols), None, "error_type_critical", err_msg)
            return False, detailed_errors

        # --- Nạp Template Word ---
        all_page_contexts = [] # Danh sách chứa context cho mỗi dòng/phiếu
        log_callback(get_translation_local("log_loading_template", filename=os.path.basename(template_path)))
        logging.info(f"Nạp template: {template_path}")
        try:
            tpl = DocxTemplate(template_path)
        except Exception as template_err:
            err_msg = f"Lỗi khi nạp template: {template_err}"
            add_error(detailed_errors, None, None, template_path, "error_type_critical", err_msg)
            return False, detailed_errors

        # --- Xử lý từng dòng Excel ---
        log_callback(get_translation_local("log_checking_rows"))
        for index, row in df.iterrows():
            current_row_idx = index + 2 # Số dòng thực tế trong file Excel (bắt đầu từ 1, cộng 1 dòng header)
            row_data = row.to_dict()
            is_critical_error_this_row = False # Cờ lỗi nghiêm trọng cho dòng hiện tại
            page_context = {} # Context cho dòng/phiếu này

            # --- Xử lý SO KHUNG (Quan trọng - Critical) ---
            so_khung_str = str(row_data.get('SO KHUNG', '')).strip()
            if not so_khung_str:
                error_msg = "Thiếu 'SO KHUNG'."
                add_error(detailed_errors, current_row_idx, 'SO KHUNG', so_khung_str, "error_type_critical", error_msg) # Thiếu là nghiêm trọng
                so_khung_str = "[KHUNG LỖI]"
                is_critical_error_this_row = True
            elif so_khung_str in processed_so_khung:
                error_msg = f"Trùng 'SO KHUNG' với dòng {processed_so_khung[so_khung_str]}."
                add_error(detailed_errors, current_row_idx, 'SO KHUNG', so_khung_str, "error_type_critical", error_msg) # Trùng là nghiêm trọng
                is_critical_error_this_row = True
            else:
                processed_so_khung[so_khung_str] = current_row_idx # Lưu lại để kiểm tra trùng

            # --- Xử lý NGAY CB ---
            ngay_cb_val = row_data.get('NGAY CB')
            ngay_cb_str = '' # Giá trị mặc định nếu trống hoặc lỗi
            if pd.notna(ngay_cb_val) and str(ngay_cb_val).strip():
                try:
                    # Thử đọc trực tiếp nếu là datetime object
                    if isinstance(ngay_cb_val, (datetime.datetime, pd.Timestamp)):
                        dt_obj = pd.to_datetime(ngay_cb_val) # Chuẩn hóa về Timestamp
                    # Nếu là số (Excel date number), chuyển đổi
                    elif isinstance(ngay_cb_val, (int, float)):
                         dt_obj = pd.to_datetime(ngay_cb_val, unit='D', origin='1899-12-30') # Common Excel origin
                    # Nếu là chuỗi, thử các định dạng phổ biến
                    elif isinstance(ngay_cb_val, str):
                        ngay_cb_val_str = str(ngay_cb_val).strip()
                        try:
                            # Ưu tiên định dạng ngày/tháng/năm
                            dt_obj = pd.to_datetime(ngay_cb_val_str, format='%d/%m/%Y', errors='raise')
                        except ValueError:
                            try:
                                # Thử định dạng tháng/ngày/năm
                                dt_obj = pd.to_datetime(ngay_cb_val_str, format='%m/%d/%Y', errors='raise')
                            except ValueError:
                                # Thử định dạng chuẩn ISO hoặc các định dạng khác pandas hỗ trợ
                                dt_obj = pd.to_datetime(ngay_cb_val_str, errors='raise')
                    else:
                         # Trường hợp kiểu dữ liệu không xác định
                         dt_obj = pd.to_datetime(str(ngay_cb_val), errors='raise')

                    # Định dạng lại thành dd/MM/yyyy
                    ngay_cb_str = dt_obj.strftime('%d/%m/%Y')
                except Exception as date_err:
                    error_msg = f"Định dạng 'NGAY CB' ('{ngay_cb_val}') không hợp lệ hoặc không thể chuyển đổi."
                    add_error(detailed_errors, current_row_idx, 'NGAY CB', ngay_cb_val, "error_type_invalid_format", error_msg)
                    ngay_cb_str = "[NGÀY LỖI]" # Đánh dấu lỗi

                        # --- Xử lý SO KG (Cải thiện và Chuẩn hóa Output kiểu VN) ---
            so_kg_raw = str(row_data.get('SO KG', '')).strip()
            so_kg_for_output = "" # Giá trị mặc định là chuỗi rỗng
            if so_kg_raw:
                # 1. Làm sạch: Loại bỏ "kg" (không phân biệt hoa thường), khoảng trắng,
                #    và cả dấu chấm/phẩy để lấy chuỗi số thuần túy.
                so_kg_numeric_str = re.sub(r'\s*kg\s*$', '', so_kg_raw, flags=re.IGNORECASE).strip()
                so_kg_numeric_str = so_kg_numeric_str.replace('.', '').replace(',', '')

                if so_kg_numeric_str: # Nếu sau khi làm sạch vẫn còn ký tự số
                    try:
                        # 2. Chuyển đổi sang số nguyên
                        int_value = int(so_kg_numeric_str)

                        # 3. Định dạng đầu ra kiểu Việt Nam (dấu chấm hàng nghìn)
                        # Định dạng với dấu phẩy hàng nghìn (chuẩn US)
                        formatted_str = "{:,}".format(int_value)
                        # Thay dấu phẩy bằng dấu chấm
                        so_kg_for_output = formatted_str.replace(',', '.') # Ví dụ: 1350 -> "1,350" -> "1.350"

                    except ValueError:
                        # Nếu không chuyển được thành số nguyên -> lỗi định dạng
                        error_msg = f"Giá trị 'SO KG' ('{so_kg_raw}') không phải số nguyên hợp lệ sau khi làm sạch."
                        add_error(detailed_errors, current_row_idx, 'SO KG', so_kg_raw, "error_type_invalid_format", error_msg)
                        so_kg_for_output = "[KG LỖI]"
                else:
                    # Nếu sau khi làm sạch không còn gì (ví dụ: chỉ có "kg", ".", ",")
                    if so_kg_raw: # Chỉ báo lỗi nếu giá trị gốc không rỗng
                        error_msg = f"Giá trị 'SO KG' ('{so_kg_raw}') không chứa số hợp lệ."
                        add_error(detailed_errors, current_row_idx, 'SO KG', so_kg_raw, "error_type_invalid_format", error_msg)
                        so_kg_for_output = "[KG LỖI]"
                    # Nếu giá trị gốc đã rỗng thì so_kg_for_output vẫn là ""
            # --- Kết thúc xử lý SO KG ---

            # --- Xử lý CHU HANG (Áp dụng chuẩn hóa) ---
            chu_hang_raw = str(row_data.get('CHU HANG', '')).strip()
            chu_hang_lower = chu_hang_raw.lower() # Chuyển về chữ thường để tìm trong map
            # Lấy giá trị chuẩn hóa từ map, nếu không có thì dùng giá trị gốc viết IN HOA
            chu_hang_normalized = OWNER_NORMALIZATION_MAP.get(chu_hang_lower, chu_hang_raw.upper())

            # --- Dừng nếu có lỗi nghiêm trọng và không bỏ qua lỗi ---
            if is_critical_error_this_row and not ignore_row_errors:
                log_callback(get_translation_local("log_stop_processing_critical", row=current_row_idx))
                logging.error(f"Dừng xử lý file {excel_basename} do lỗi nghiêm trọng ở dòng {current_row_idx} và không bỏ qua lỗi.")
                critical_error_occurred = True # Đặt cờ lỗi nghiêm trọng tổng thể
                break # Thoát khỏi vòng lặp xử lý dòng

            # --- Tạo mã QR ---
            qr_data = so_khung_str # Dữ liệu cho QR là SO KHUNG đã xử lý
            img_byte_arr = None
            qr_code_obj = None # Đối tượng InlineImage cho template
            if qr_data and qr_data != "[KHUNG LỖI]": # Chỉ tạo QR nếu SO KHUNG hợp lệ
                try:
                    qr_img = qrcode.make(qr_data)
                    img_byte_arr = io.BytesIO() # Tạo bộ đệm byte trong bộ nhớ
                    qr_img.save(img_byte_arr, format='PNG') # Lưu ảnh QR vào bộ đệm
                    img_byte_arr.seek(0) # Đưa con trỏ về đầu bộ đệm
                    try:
                        # Tạo đối tượng InlineImage để chèn vào Word
                        qr_code_obj = InlineImage(tpl, img_byte_arr, width=Mm(qr_code_size_mm))
                    except Exception as img_err:
                        error_msg = f"Lỗi chèn ảnh QR vào Word: {img_err}"
                        add_error(detailed_errors, current_row_idx, 'SO KHUNG', qr_data, "error_type_image", error_msg)
                        qr_code_obj = "[QR Img Error]" # Đánh dấu lỗi chèn ảnh
                except Exception as qr_err:
                    error_msg = f"Lỗi tạo mã QR: {qr_err}"
                    add_error(detailed_errors, current_row_idx, 'SO KHUNG', qr_data, "error_type_qr", error_msg)
                    qr_code_obj = "[QR Gen Error]" # Đánh dấu lỗi tạo QR

            # --- Tạo Context cho trang/phiếu hiện tại ---
            # Sử dụng các giá trị đã được xử lý và chuẩn hóa
            page_context = {
                'phieu_so': str(row_data.get('STT', index + 1)), # Lấy STT hoặc dùng index+1
                'loai_xe': str(row_data.get('LOAI XE', '')).strip(),
                'so_khung': so_khung_str, # Đã kiểm tra lỗi
                'so_cont': str(row_data.get('SO CONT', '')).strip(),
                'ngay_cb': ngay_cb_str, # Đã xử lý định dạng/lỗi
                'ten_tau': str(row_data.get('TAU', '')).strip(),
                'chuyen': str(row_data.get('CHUYEN', '')).strip(),
                'chu_hang': chu_hang_normalized, # ĐÃ CHUẨN HÓA
                'so_kg': so_kg_for_output, # Đã làm sạch và xác thực
                'qr_code': qr_code_obj if qr_code_obj else "" # QR code object hoặc chuỗi rỗng/lỗi
            }
            all_page_contexts.append(page_context) # Thêm context của dòng này vào danh sách chung

            # Cập nhật tiến trình (tính toán % hoàn thành dựa trên số dòng đã xử lý)
            progress_callback(int(((index + 1) / total_rows) * 90)) # Giả sử xử lý dòng chiếm 90% công việc

        # --- Kiểm tra sau vòng lặp ---
        if critical_error_occurred:
             # Nếu có lỗi nghiêm trọng và không bỏ qua, thì không tạo file Word
            return False, detailed_errors

        # Kiểm tra nếu không có context nào được tạo (có thể do lỗi hoặc file chỉ có header)
        if not all_page_contexts:
            err_msg = get_translation_local("log_no_context")
            add_error(detailed_errors, None, None, None, "error_type_no_context", err_msg)
            return False, detailed_errors

        log_callback(get_translation_local("log_prepared_contexts", count=len(all_page_contexts)))

        # Hiển thị tiêu đề nếu có lỗi/cảnh báo dữ liệu
        if detailed_errors:
            log_callback(get_translation_local("log_data_warnings_header"))

        # --- Render và Lưu File Word ---
        # Cấu trúc context cuối cùng mà docxtpl mong đợi cho vòng lặp {{#items}}...{{/items}}
        final_context = { 'items': all_page_contexts }

        log_callback(get_translation_local("log_rendering_word"))
        logging.info(f"Bắt đầu render Word cho file {excel_basename}")
        tpl.render(final_context)
        progress_callback(95) # Cập nhật tiến trình sau khi render

        log_callback(get_translation_local("log_saving_word", filename=os.path.basename(output_path)))
        logging.info(f"Lưu file Word vào: {output_path}")
        tpl.save(output_path) # Lưu file Word
        log_callback(get_translation_local("log_word_success"))
        logging.info(f"Đã tạo thành công file Word: {output_path}")
        progress_callback(100) # Hoàn thành

        # Trả về True (thành công) và danh sách lỗi (có thể có cảnh báo)
        return True, detailed_errors

    # --- Xử lý các Exception tổng quát ---
    except FileNotFoundError as e:
        err_msg = f"Không tìm thấy file: {e.filename}"
        add_error(detailed_errors, None, None, e.filename, "error_type_system", err_msg)
        logging.exception(f"Lỗi FileNotFoundError khi xử lý {excel_path}:")
        progress_callback(0)
        return False, detailed_errors
    except pd.errors.EmptyDataError:
        # Lỗi này thường xảy ra nếu file Excel tồn tại nhưng hoàn toàn trống
        err_msg = get_translation_local("log_excel_empty")
        add_error(detailed_errors, None, None, excel_path, "error_type_empty_file", err_msg)
        logging.warning(f"File Excel rỗng hoặc không có dữ liệu: {excel_path}")
        progress_callback(0)
        return False, detailed_errors
    except Exception as e:
        # Bắt các lỗi không mong muốn khác
        err_msg = f"Lỗi hệ thống không xác định: {e}"
        add_error(detailed_errors, None, None, None, "error_type_system", err_msg)
        import traceback
        log_callback(f"Lỗi hệ thống:\n{traceback.format_exc()}") # Ghi traceback vào log GUI
        logging.exception(f"Lỗi hệ thống khi xử lý file {excel_path}:") # Ghi traceback vào file log
        progress_callback(0)
        return False, detailed_errors


# --- Lớp ứng dụng GUI (Đã đổi tên biến template_p, output_file_p) ---
class App:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.current_language = self.config.get('Settings', 'language', fallback=DEFAULT_LANGUAGE)
        self.is_input_single_file = False # Cờ xác định đang chọn file đơn hay thư mục

        self.style = ttk.Style(self.root)
        # Cố gắng sử dụng theme 'clam' hoặc 'alt' nếu có, nếu không dùng theme mặc định
        available_themes = self.style.theme_names()
        theme_to_use = 'default'
        if 'clam' in available_themes:
            theme_to_use = 'clam'
        elif 'alt' in available_themes:
            theme_to_use = 'alt'
        try:
            self.style.theme_use(theme_to_use)
            # Thêm style cho nút Generate để nổi bật hơn
            self.style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), foreground='white', background='#0078D7') # Màu xanh dương
            self.style.map('Accent.TButton', background=[('active', '#005A9E')]) # Màu đậm hơn khi hover/active
        except tk.TclError:
            logging.warning(f"Không thể đặt theme '{theme_to_use}'. Sử dụng theme mặc định.")

        self.root.geometry("850x720") # Kích thước cửa sổ

        # --- Variables ---
        # Các biến Tkinter để liên kết với các widget trên GUI
        self.excel_path_var = tk.StringVar(value=self.config.get('Paths', 'last_excel_dir', fallback=''))
        self.template_path_var = tk.StringVar(value=self.config.get('Paths', 'last_template', fallback=''))
        self.output_dir_var = tk.StringVar(value=self.config.get('Paths', 'last_output_dir', fallback=''))
        self.output_file_var = tk.StringVar(value=self.config.get('Paths', 'last_output_file', fallback=''))
        self.ignore_errors_var = tk.BooleanVar(value=self.config.getboolean('Settings', 'ignore_errors', fallback=False))
        self.archive_var = tk.BooleanVar(value=self.config.getboolean('Settings', 'archive_processed', fallback=False))
        self.progress_var = tk.IntVar() # Biến cho thanh tiến trình
        self.progress_label_var = tk.StringVar(value="") # Biến cho nhãn trạng thái tiến trình
        self.language_var = tk.StringVar(value=self.current_language) # Biến cho ngôn ngữ đang chọn

        # --- Menu Bar ---
        self.menu_bar = Menu(root)
        root.config(menu=self.menu_bar)
        # Menu Ngôn ngữ
        self.language_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.get_translation("menu_language"), menu=self.language_menu)
        self.language_menu.add_radiobutton(label=self.get_translation("menu_vietnamese"), variable=self.language_var, value='vi', command=self.change_language)
        self.language_menu.add_radiobutton(label=self.get_translation("menu_english"), variable=self.language_var, value='en', command=self.change_language)

        # --- Main Frame ---
        # Khung chính chứa tất cả các thành phần khác
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Top Frame (Chứa Frame File và nút Settings) ---
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        # Khung con cho việc chọn file/thư mục
        self.file_frame = ttk.LabelFrame(top_frame, padding="10")
        self.file_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # --- Input/Output Widgets (Trong file_frame) ---
        # Đường dẫn Excel
        self.excel_label = ttk.Label(self.file_frame)
        self.excel_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        excel_entry = ttk.Entry(self.file_frame, textvariable=self.excel_path_var, width=55, state='readonly')
        excel_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=3)
        self.excel_file_button = ttk.Button(self.file_frame, command=self.select_excel_file) # Nút chọn file
        self.excel_file_button.grid(row=0, column=2, padx=(5, 2), pady=3)
        self.excel_dir_button = ttk.Button(self.file_frame, command=self.select_excel_dir) # Nút chọn thư mục
        self.excel_dir_button.grid(row=0, column=3, padx=(2, 5), pady=3)

        # Đường dẫn Template
        self.template_label = ttk.Label(self.file_frame)
        self.template_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        self.template_entry = ttk.Entry(self.file_frame, textvariable=self.template_path_var, width=55, state='readonly')
        self.template_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=3)
        self.template_button = ttk.Button(self.file_frame, command=self.select_template)
        self.template_button.grid(row=1, column=2, columnspan=2, padx=5, pady=3, sticky=tk.E)

        # Đường dẫn Thư mục Output (cho chế độ batch)
        self.output_dir_label = ttk.Label(self.file_frame)
        self.output_dir_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        self.output_dir_entry = ttk.Entry(self.file_frame, textvariable=self.output_dir_var, width=55, state='readonly')
        self.output_dir_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=3)
        self.output_dir_button = ttk.Button(self.file_frame, command=self.select_output_dir)
        self.output_dir_button.grid(row=2, column=2, columnspan=2, padx=5, pady=3, sticky=tk.E)

        # Đường dẫn File Output (cho chế độ file đơn)
        self.output_file_label = ttk.Label(self.file_frame)
        self.output_file_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
        self.output_file_entry = ttk.Entry(self.file_frame, textvariable=self.output_file_var, width=55, state='readonly')
        self.output_file_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=3)
        self.output_file_button = ttk.Button(self.file_frame, command=self.select_output_file)
        self.output_file_button.grid(row=3, column=2, columnspan=2, padx=5, pady=3, sticky=tk.E)

        # Cấu hình cột thứ 2 (chứa Entry) co giãn theo chiều ngang
        self.file_frame.columnconfigure(1, weight=1)

        # Nút Settings (nằm bên phải file_frame)
        self.settings_button = ttk.Button(top_frame, command=self.open_settings_window)
        self.settings_button.pack(side=tk.RIGHT, anchor=tk.N, pady=3)

        # --- Control Frame (Chứa nút Generate và Checkbox) ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        # Nút Generate chính
        self.generate_button = ttk.Button(control_frame, command=self.start_generation_thread, style='Accent.TButton') # Sử dụng style đã định nghĩa
        self.generate_button.pack(side=tk.LEFT, padx=(0, 15))
        # Checkbox Bỏ qua lỗi
        self.ignore_errors_checkbox = ttk.Checkbutton(control_frame, variable=self.ignore_errors_var, command=self.save_checkbox_states)
        self.ignore_errors_checkbox.pack(side=tk.LEFT, padx=10)
        # Checkbox Lưu trữ file đã xử lý
        self.archive_checkbox = ttk.Checkbutton(control_frame, variable=self.archive_var, command=self.save_checkbox_states)
        self.archive_checkbox.pack(side=tk.LEFT, padx=10)

        # --- Progress Bar & Label ---
        # Nhãn hiển thị trạng thái chi tiết (vd: Đang xử lý file X/Y)
        self.progress_status_label = ttk.Label(main_frame, textvariable=self.progress_label_var, anchor=tk.W)
        self.progress_status_label.pack(fill=tk.X, pady=(5, 0))
        # Thanh tiến trình
        self.progress_bar = ttk.Progressbar(main_frame, orient="horizontal", length=400, mode="determinate", variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # --- Log Frame ---
        # Khung chứa ô hiển thị log
        self.log_frame = ttk.LabelFrame(main_frame, padding="10")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        # Ô văn bản có thanh cuộn để hiển thị log
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=15, state='disabled', font=("Consolas", 9)) # Dùng font Consolas cho dễ đọc log
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        # Thanh trạng thái ở dưới cùng cửa sổ
        self.status_bar_frame = ttk.Frame(root, relief=tk.SUNKEN, padding=(5, 2))
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # Nhãn trạng thái chung (vd: Sẵn sàng, Đã hoàn thành)
        self.status_label = ttk.Label(self.status_bar_frame, text="", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Nhãn thông tin tác giả
        self.author_label = ttk.Label(self.status_bar_frame, anchor=tk.E)
        self.author_label.pack(side=tk.RIGHT)

        # --- Initial UI Update & Log ---
        self.update_output_mode_ui() # Cập nhật trạng thái ban đầu của các nút Output
        self.update_ui_language() # Cập nhật ngôn ngữ cho các widget
        self.log_message(self.get_translation("status_ready")) # Ghi log trạng thái sẵn sàng
        logging.info(self.get_translation("log_gui_ready")) # Ghi log vào file

    # --- Language Handling ---
    def get_translation(self, key, **kwargs):
        """Lấy chuỗi dịch theo key và ngôn ngữ hiện tại."""
        try:
            return translations[key][self.current_language].format(**kwargs)
        except KeyError:
            logging.warning(f"Missing translation for key '{key}' in language '{self.current_language}'")
            return key # Trả về key nếu không tìm thấy bản dịch
        except Exception as e:
             logging.error(f"Error formatting translation for key '{key}': {e}")
             return key

    def change_language(self):
        """Thay đổi ngôn ngữ và cập nhật giao diện."""
        new_lang = self.language_var.get()
        if new_lang != self.current_language:
            self.current_language = new_lang
            self.config.set('Settings', 'language', self.current_language) # Lưu ngôn ngữ mới vào config
            self.update_ui_language() # Cập nhật lại text trên GUI
            self.log_message(f"Ngôn ngữ đã đổi thành: {'Tiếng Việt' if new_lang == 'vi' else 'English'}")
            logging.info(f"Language changed to: {self.current_language}")

    def update_ui_language(self):
        """Cập nhật tất cả các chuỗi văn bản trên GUI theo ngôn ngữ hiện tại."""
        self.root.title(self.get_translation("app_title"))
        # Menu
        self.menu_bar.entryconfig(1, label=self.get_translation("menu_language")) # Index 1 là menu Ngôn ngữ
        self.language_menu.entryconfig(0, label=self.get_translation("menu_vietnamese"))
        self.language_menu.entryconfig(1, label=self.get_translation("menu_english"))
        # File Frame
        self.file_frame.config(text=self.get_translation("file_frame_title"))
        self.excel_label.config(text=self.get_translation("label_excel_path"))
        self.excel_file_button.config(text=self.get_translation("button_select_file"))
        self.excel_dir_button.config(text=self.get_translation("button_select_dir"))
        self.template_label.config(text=self.get_translation("label_template_path"))
        self.template_button.config(text=self.get_translation("button_select"))
        self.output_dir_label.config(text=self.get_translation("label_output_dir"))
        self.output_dir_button.config(text=self.get_translation("button_select"))
        self.output_file_label.config(text=self.get_translation("label_output_file"))
        self.output_file_button.config(text=self.get_translation("button_save_as"))
        # Buttons & Checkboxes
        self.settings_button.config(text=self.get_translation("button_settings"))
        self.generate_button.config(text=self.get_translation("button_generate"))
        self.ignore_errors_checkbox.config(text=self.get_translation("check_ignore_errors"))
        self.archive_checkbox.config(text=self.get_translation("check_archive"))
        # Log Frame & Status Bar
        self.log_frame.config(text=self.get_translation("log_frame_title"))
        self.status_label.config(text=self.get_translation("status_ready")) # Cập nhật status bar
        self.author_label.config(text=self.get_translation("status_author"))

    # --- UI State Update ---
    def update_output_mode_ui(self):
        """Bật/tắt các widget chọn đường dẫn Output dựa trên chế độ file đơn/thư mục."""
        if self.is_input_single_file:
            # Chế độ file đơn: Bật chọn File Output, Tắt chọn Thư mục Output, Tắt Archive
            self.output_file_label.config(state='normal')
            self.output_file_entry.config(state='readonly')
            self.output_file_button.config(state='normal')
            self.output_dir_label.config(state='disabled')
            self.output_dir_entry.config(state='disabled')
            self.output_dir_button.config(state='disabled')
            self.archive_checkbox.config(state='disabled')
            self.archive_var.set(False) # Tự động bỏ chọn Archive
        else:
            # Chế độ thư mục: Tắt chọn File Output, Bật chọn Thư mục Output, Bật Archive
            self.output_file_label.config(state='disabled')
            self.output_file_entry.config(state='disabled')
            self.output_file_button.config(state='disabled')
            self.output_dir_label.config(state='normal')
            self.output_dir_entry.config(state='readonly')
            self.output_dir_button.config(state='normal')
            self.archive_checkbox.config(state='normal')
            # Khôi phục trạng thái archive từ config nếu cần
            self.archive_var.set(self.config.getboolean('Settings', 'archive_processed', fallback=False))


    # --- Event Handlers ---
    def select_excel_file(self):
        """Mở hộp thoại chọn một file Excel."""
        title = self.get_translation("button_select_file")
        # Lấy đường dẫn thư mục của file/thư mục đã chọn trước đó làm thư mục mở mặc định
        initial_dir = os.path.dirname(self.excel_path_var.get()) if os.path.exists(self.excel_path_var.get()) else None
        path = select_file_or_dir(is_dir=False, title=title, filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")), initial_dir_or_file=initial_dir)
        if path:
            if not path.lower().endswith(".xlsx"):
                messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_excel_must_be_xlsx"))
                return
            self.excel_path_var.set(path)
            self.config.set('Paths', 'last_excel_file', path) # Lưu file cuối cùng
            self.config.set('Paths', 'last_excel_dir', os.path.dirname(path)) # Lưu thư mục chứa file đó
            self.log_message(self.get_translation("log_excel_selected", path=path))
            self.is_input_single_file = True # Đặt cờ là file đơn
            self.update_output_mode_ui() # Cập nhật GUI
            self.output_dir_var.set("") # Xóa đường dẫn thư mục output (nếu có)

    def select_excel_dir(self):
        """Mở hộp thoại chọn một thư mục chứa các file Excel."""
        title = self.get_translation("button_select_dir")
        # Lấy đường dẫn thư mục đã chọn trước đó làm thư mục mở mặc định
        initial_dir = self.excel_path_var.get() if os.path.isdir(self.excel_path_var.get()) else None
        path = select_file_or_dir(is_dir=True, title=title, initial_dir_or_file=initial_dir)
        if path:
            self.excel_path_var.set(path)
            self.config.set('Paths', 'last_excel_dir', path) # Lưu thư mục cuối cùng
            self.config.set('Paths', 'last_excel_file', '') # Xóa đường dẫn file đơn
            self.log_message(self.get_translation("log_excel_dir_selected", path=path))
            self.is_input_single_file = False # Đặt cờ là thư mục
            self.update_output_mode_ui() # Cập nhật GUI
            self.output_file_var.set("") # Xóa đường dẫn file output (nếu có)

    def select_template(self):
        """Mở hộp thoại chọn file template Word (.docx)."""
        title = self.get_translation("label_template_path")
        initial_dir = os.path.dirname(self.template_path_var.get()) if os.path.exists(self.template_path_var.get()) else None
        path = select_file_or_dir(is_dir=False, title=title, filetypes=(("Word files", "*.docx"), ("All files", "*.*")), initial_dir_or_file=initial_dir)
        if path:
            if not path.lower().endswith(".docx"):
                 messagebox.showerror(self.get_translation("msg_error_title"), "File mẫu phải là file .docx")
                 return
            self.template_path_var.set(path)
            self.config.set('Paths', 'last_template', path)
            self.log_message(self.get_translation("log_template_selected", path=path))

    def select_output_dir(self):
        """Mở hộp thoại chọn thư mục lưu trữ output (chế độ batch)."""
        title = self.get_translation("label_output_dir")
        initial_dir = self.output_dir_var.get() if os.path.isdir(self.output_dir_var.get()) else None
        path = select_file_or_dir(is_dir=True, title=title, initial_dir_or_file=initial_dir)
        if path:
            self.output_dir_var.set(path)
            self.config.set('Paths', 'last_output_dir', path)
            self.log_message(self.get_translation("log_output_dir_selected", path=path))

    def select_output_file(self):
        """Mở hộp thoại 'Lưu thành' để chọn nơi lưu file Word output (chế độ file đơn)."""
        title = self.get_translation("button_save_as")
        excel_path = self.excel_path_var.get()
        # Tạo tên file gợi ý dựa trên tên file Excel đầu vào
        initial_filename = "PhieuVanChuyen_Output.docx" # Tên mặc định
        if excel_path and os.path.isfile(excel_path):
            base = os.path.splitext(os.path.basename(excel_path))[0]
            # Loại bỏ các ký tự không hợp lệ trong tên file (ví dụ)
            safe_base = re.sub(r'[\\/*?:"<>|]', "", base)
            initial_filename = f"PhieuVanChuyen_{safe_base}.docx"

        # Lấy thư mục output đã lưu trước đó làm thư mục mở mặc định
        initial_dir = self.config.get('Paths', 'last_output_dir', fallback=None)
        # Mở hộp thoại asksaveasfilename
        path = filedialog.asksaveasfilename(
            title=title,
            initialdir=initial_dir,
            initialfile=initial_filename,
            defaultextension=".docx",
            filetypes=(("Word files", "*.docx"), ("All files", "*.*"))
        )
        if path:
            self.output_file_var.set(path)
            self.config.set('Paths', 'last_output_file', path) # Lưu đường dẫn file output
            # Cũng cập nhật thư mục output cuối cùng dựa trên lựa chọn này
            self.config.set('Paths', 'last_output_dir', os.path.dirname(path))
            self.log_message(self.get_translation("log_output_file_selected", path=path))

    def open_settings_window(self):
        """Mở cửa sổ cài đặt kích thước QR."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title(self.get_translation("settings_window_title"))
        settings_window.geometry("350x150")
        settings_window.resizable(False, False)
        settings_window.transient(self.root) # Đặt làm cửa sổ con của root
        settings_window.grab_set() # Chặn tương tác với cửa sổ chính

        frame = ttk.Frame(settings_window, padding="10")
        frame.pack(expand=True, fill=tk.BOTH)

        qr_label = ttk.Label(frame, text=self.get_translation("label_qr_size"))
        qr_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        qr_size_var = tk.StringVar(value=self.config.get('Settings', 'qr_size_mm', fallback=str(DEFAULT_QR_SIZE)))
        qr_size_entry = ttk.Entry(frame, textvariable=qr_size_var, width=10)
        qr_size_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=15)

        save_button = ttk.Button(button_frame, text=self.get_translation("button_save"), command=lambda: self.save_settings(qr_size_var, settings_window))
        save_button.pack(side=tk.LEFT, padx=10)
        cancel_button = ttk.Button(button_frame, text=self.get_translation("button_cancel"), command=settings_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)

        qr_size_entry.focus_set() # Đặt focus vào ô nhập liệu
        # Cho phép nhấn Enter để lưu
        settings_window.bind('<Return>', lambda event: self.save_settings(qr_size_var, settings_window))

    def save_settings(self, entry_var, settings_window):
        """Lưu cài đặt từ cửa sổ Settings."""
        new_value_str = entry_var.get().strip()
        try:
            new_value_int = int(new_value_str)
            if new_value_int <= 0:
                 # Ném lỗi cụ thể hơn để bắt trong except
                 raise ValueError("Kích thước phải là số nguyên dương.")

            # Lưu giá trị hợp lệ vào config
            self.config.set('Settings', 'qr_size_mm', str(new_value_int))
            self.log_message(self.get_translation("msg_qr_updated", value=new_value_int))
            logging.info(self.get_translation("log_qr_updated_log", value=new_value_int))
            messagebox.showinfo(self.get_translation("msg_info_title"),
                                self.get_translation("msg_settings_saved"),
                                parent=settings_window) # Hiển thị thông báo trên cửa sổ con
            settings_window.destroy() # Đóng cửa sổ cài đặt
        except ValueError as e:
            # Hiển thị lỗi nếu giá trị nhập không hợp lệ
            messagebox.showerror(self.get_translation("msg_error_title"),
                                 self.get_translation("msg_invalid_value", value=new_value_str, error=e),
                                 parent=settings_window) # Hiển thị lỗi trên cửa sổ con

    def save_checkbox_states(self):
        """Lưu trạng thái của các checkbox vào file config."""
        self.config.set('Settings', 'ignore_errors', str(self.ignore_errors_var.get()))
        # Chỉ lưu trạng thái archive nếu không ở chế độ file đơn (vì nó bị disable)
        if not self.is_input_single_file:
            self.config.set('Settings', 'archive_processed', str(self.archive_var.get()))
        # Không cần gọi save_config(self.config) ở đây, sẽ lưu khi đóng app hoặc hoàn thành tác vụ

    # --- Generation Process ---
    def start_generation_thread(self):
        """Bắt đầu quá trình tạo phiếu trong một luồng riêng biệt."""
        # --- Lấy giá trị từ GUI ---
        excel_input_path = self.excel_path_var.get()
        template_path = self.template_path_var.get() # Đổi tên biến
        output_dir = self.output_dir_var.get()
        output_filepath = self.output_file_var.get() # Đổi tên biến
        ignore_errors = self.ignore_errors_var.get()
        # Archive chỉ hoạt động khi chọn thư mục và checkbox được chọn
        archive_files = self.archive_var.get() and not self.is_input_single_file

        # --- Kiểm tra đầu vào cơ bản ---
        if not excel_input_path or not template_path:
            messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_select_all_paths"))
            return
        if not os.path.exists(excel_input_path):
             messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_path_not_exist", path=excel_input_path))
             return
        if not os.path.isfile(template_path):
             messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_template_invalid", path=template_path))
             return

        # --- Kiểm tra đường dẫn Output dựa trên chế độ ---
        if self.is_input_single_file:
            # Chế độ file đơn: Cần có đường dẫn file output hợp lệ
            if not output_filepath:
                messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_output_file_invalid", path=output_filepath))
                return
            # Kiểm tra thư mục chứa file output có tồn tại không
            output_file_dir = os.path.dirname(output_filepath)
            if not os.path.isdir(output_file_dir):
                 messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_output_dir_invalid", path=output_file_dir))
                 return
        else:
            # Chế độ thư mục: Cần có đường dẫn thư mục output hợp lệ
            if not output_dir:
                messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_output_dir_invalid", path=output_dir))
                return
            if not os.path.isdir(output_dir):
                 messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_output_dir_invalid", path=output_dir))
                 return

        # --- Vô hiệu hóa GUI trong khi xử lý ---
        self.disable_ui()

        # --- Xóa log cũ và reset tiến trình ---
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        self.progress_var.set(0)
        self.progress_label_var.set("")
        self.status_label.config(text=self.get_translation("status_processing_single_file", filename="...")[:-4]) # Trạng thái ban đầu
        self.root.update_idletasks() # Cập nhật giao diện ngay lập tức

        # --- Tạo và bắt đầu luồng xử lý ---
        if self.is_input_single_file:
            # Xử lý file đơn
            self.log_message(self.get_translation("log_preparing_single_file", filename=os.path.basename(excel_input_path)))
            logging.info(self.get_translation("log_starting_single_process", path=excel_input_path))
            thread = threading.Thread(target=self.run_single_generation, args=(excel_input_path, template_path, output_filepath, ignore_errors))
        else:
            # Xử lý thư mục (batch)
            try:
                # Lấy danh sách file .xlsx trong thư mục đầu vào
                files_to_process = [
                    os.path.join(excel_input_path, f)
                    for f in os.listdir(excel_input_path)
                    if f.lower().endswith(".xlsx") and not f.startswith('~') # Bỏ qua file tạm của Excel
                ]
                if not files_to_process:
                    messagebox.showwarning(self.get_translation("msg_warning_title"), self.get_translation("msg_no_xlsx_found", path=excel_input_path))
                    self.enable_ui() # Kích hoạt lại UI nếu không có file
                    return
            except Exception as e:
                messagebox.showerror(self.get_translation("msg_error_title"), self.get_translation("msg_cannot_read_excel_dir", error=e))
                logging.error(f"Lỗi đọc thư mục Excel {excel_input_path}: {e}")
                self.enable_ui() # Kích hoạt lại UI nếu lỗi đọc thư mục
                return

            file_count = len(files_to_process)
            self.log_message(self.get_translation("log_preparing_files", count=file_count))
            logging.info(self.get_translation("log_starting_process", count=file_count, path=excel_input_path))
            thread = threading.Thread(target=self.run_batch_generation, args=(files_to_process, template_path, output_dir, ignore_errors, archive_files))

        thread.daemon = True # Để luồng tự thoát khi chương trình chính đóng
        thread.start() # Bắt đầu chạy luồng

    def disable_ui(self):
        """Vô hiệu hóa các thành phần GUI khi đang xử lý."""
        self.generate_button.config(state='disabled')
        self.ignore_errors_checkbox.config(state='disabled')
        self.archive_checkbox.config(state='disabled')
        self.settings_button.config(state='disabled')
        self.menu_bar.entryconfig(1, state='disabled') # Vô hiệu hóa menu Ngôn ngữ
        # Vô hiệu hóa các nút chọn đường dẫn
        self.excel_file_button.config(state='disabled')
        self.excel_dir_button.config(state='disabled')
        self.template_button.config(state='disabled')
        self.output_dir_button.config(state='disabled')
        self.output_file_button.config(state='disabled')

    def enable_ui(self):
        """Kích hoạt lại các thành phần GUI sau khi xử lý xong."""
        self.generate_button.config(state='normal')
        self.ignore_errors_checkbox.config(state='normal')
        # Archive checkbox chỉ bật lại nếu không ở chế độ file đơn
        self.archive_checkbox.config(state='normal' if not self.is_input_single_file else 'disabled')
        self.settings_button.config(state='normal')
        self.menu_bar.entryconfig(1, state='normal') # Kích hoạt lại menu Ngôn ngữ
        # Kích hoạt lại các nút chọn đường dẫn
        self.excel_file_button.config(state='normal')
        self.excel_dir_button.config(state='normal')
        self.template_button.config(state='normal')
        # Kích hoạt lại các nút output dựa trên chế độ hiện tại
        self.update_output_mode_ui()

    def run_single_generation(self, excel_file, template_path, output_filepath, ignore_errors):
        """Chạy hàm xử lý chính cho một file đơn."""
        # Cập nhật trạng thái ban đầu cho file này
        self.root.after(0, self.update_progress_label, self.get_translation("status_processing_single_file", filename=os.path.basename(excel_file)))
        self.root.after(0, self.update_progress, 0)

        # Gọi hàm xử lý chính
        success, file_errors = generate_word_from_excel_jinja(
            excel_file, template_path, output_filepath, self.config, ignore_errors,
            self.log_message_threadsafe, self.update_progress_threadsafe
        )

        # Gọi hàm xử lý kết quả trên luồng chính của GUI
        self.root.after(0, self.single_generation_complete, success, excel_file, output_filepath, file_errors)

    def run_batch_generation(self, excel_files, template_path, output_dir, ignore_errors, archive_files):
        """Chạy hàm xử lý chính cho nhiều file trong thư mục."""
        overall_success = True # Cờ theo dõi thành công tổng thể
        all_detailed_errors = [] # Thu thập lỗi từ tất cả các file
        processed_files = 0
        total_files = len(excel_files)

        # Tạo thư mục Archive nếu cần và được chọn
        archive_dir_path = None
        if archive_files and excel_files:
            # Giả định tất cả file excel nằm cùng thư mục, lấy thư mục của file đầu tiên
            excel_file_dir = os.path.dirname(excel_files[0])
            archive_dir_path = os.path.join(excel_file_dir, ARCHIVE_FOLDER_NAME)
            try:
                os.makedirs(archive_dir_path, exist_ok=True) # Tạo thư mục, bỏ qua nếu đã tồn tại
            except Exception as mkdir_err:
                # Nếu không tạo được thư mục Archive, báo lỗi và dừng archive
                err_msg = f"Lỗi tạo thư mục lưu trữ '{archive_dir_path}': {mkdir_err}. File sẽ không được di chuyển."
                self.log_message_threadsafe(err_msg)
                logging.error(err_msg)
                archive_files = False # Tắt chức năng archive nếu không tạo được thư mục
                archive_dir_path = None

        # Lặp qua từng file Excel để xử lý
        for i, excel_file in enumerate(excel_files):
            # Cập nhật trạng thái xử lý file hiện tại
            progress_text = self.get_translation("status_processing_file", current=i + 1, total=total_files, filename=os.path.basename(excel_file))
            self.root.after(0, self.update_progress_label, progress_text)
            self.root.after(0, self.update_progress, 0) # Reset progress cho file mới

            # Tạo tên file output duy nhất cho mỗi file input
            excel_filename_no_ext = os.path.splitext(os.path.basename(excel_file))[0]
            safe_filename_no_ext = re.sub(r'[\\/*?:"<>|]', "", excel_filename_no_ext) # Làm sạch tên file
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"PhieuVanChuyen_{safe_filename_no_ext}_{timestamp}.docx"
            output_filepath = os.path.join(output_dir, output_filename)

            # Gọi hàm xử lý chính cho file này
            success, file_errors = generate_word_from_excel_jinja(
                excel_file, template_path, output_filepath, self.config, ignore_errors,
                self.log_message_threadsafe, self.update_progress_threadsafe
            )

            # Cập nhật trạng thái tổng thể và danh sách lỗi
            if not success:
                overall_success = False
            if file_errors:
                all_detailed_errors.extend(file_errors) # Thêm lỗi của file này vào danh sách chung

            # Di chuyển file Excel đã xử lý thành công vào thư mục Archive (nếu được chọn và thành công)
            if success and archive_files and archive_dir_path:
                try:
                    archive_target_path = os.path.join(archive_dir_path, os.path.basename(excel_file))
                    # Kiểm tra nếu file đích đã tồn tại (trường hợp hiếm)
                    if os.path.exists(archive_target_path):
                        base, ext = os.path.splitext(os.path.basename(excel_file))
                        archive_target_path = os.path.join(archive_dir_path, f"{base}_{timestamp}{ext}")

                    self.log_message_threadsafe(self.get_translation("log_moving_archive", path=archive_target_path))
                    logging.info(f"Di chuyển file {excel_file} vào {archive_target_path}")
                    shutil.move(excel_file, archive_target_path) # Di chuyển file
                    self.log_message_threadsafe(self.get_translation("log_move_success"))
                except Exception as move_err:
                    # Nếu lỗi di chuyển, ghi log và thêm vào danh sách lỗi
                    err_msg = self.get_translation("log_move_error", filename=os.path.basename(excel_file), folder=ARCHIVE_FOLDER_NAME, error=move_err)
                    self.log_message_threadsafe(f"    Lỗi: {err_msg}") # Thêm thụt lề cho dễ nhìn
                    logging.error(f"Lỗi di chuyển file {excel_file}: {move_err}")
                    all_detailed_errors.append({
                        'file': os.path.basename(excel_file),
                        'row': None, 'column': None, 'value': None,
                        'type': "error_type_archive", # Loại lỗi lưu trữ
                        'message': str(move_err)
                    })
                    overall_success = False # Đánh dấu có lỗi xảy ra

            processed_files += 1 # Tăng bộ đếm file đã xử lý

        # Gọi hàm xử lý kết quả batch trên luồng chính của GUI
        self.root.after(0, self.batch_generation_complete, overall_success, processed_files, total_files, all_detailed_errors)

    def single_generation_complete(self, success, excel_file, output_file, errors):
        """Xử lý kết quả sau khi hoàn thành xử lý file đơn."""
        self.enable_ui() # Kích hoạt lại giao diện
        save_config(self.config) # Lưu cấu hình (đường dẫn cuối, cài đặt)

        if success:
            # Thành công
            final_status = self.get_translation("status_processed_single_success", filename=os.path.basename(excel_file))
            self.progress_label_var.set(final_status)
            self.status_label.config(text=final_status)
            self.progress_var.set(100) # Đặt tiến trình 100%
            self.log_message(self.get_translation("log_single_complete_success"))
            logging.info(f"Hoàn thành xử lý file đơn {excel_file} thành công.")
            # Hiển thị thông báo thành công
            messagebox.showinfo(self.get_translation("msg_info_title"), self.get_translation("msg_single_complete_success", path=output_file))
        else:
            # Thất bại hoặc có lỗi
            final_status = self.get_translation("status_processed_single_error", filename=os.path.basename(excel_file))
            self.progress_label_var.set(final_status)
            self.status_label.config(text=final_status)
            self.progress_var.set(0) # Đặt tiến trình về 0
            self.log_message(self.get_translation("log_single_complete_with_errors"))
            logging.warning(f"Hoàn thành xử lý file đơn {excel_file} với {len(errors)} lỗi/cảnh báo chi tiết.")

            # Hỏi người dùng có muốn xuất báo cáo lỗi không
            export_report = messagebox.askyesno(
                self.get_translation("msg_warning_title"),
                self.get_translation("msg_single_complete_error"),
                parent=self.root # Đặt parent để messagebox hiện trên cửa sổ chính
            )
            if export_report and errors:
                self.export_error_report(errors) # Gọi hàm xuất báo cáo
            elif errors:
                 # Nếu không xuất báo cáo, ghi tóm tắt lỗi vào log
                 error_summary = f"{self.get_translation('msg_error_title')}: {len(errors)} " + self.get_translation("error_report_col_message").lower() + "."
                 error_summary += self.get_translation("msg_batch_error_check_log")
                 self.log_message(error_summary)

    def batch_generation_complete(self, overall_success, processed_count, total_count, all_detailed_errors):
        """Xử lý kết quả sau khi hoàn thành xử lý batch."""
        self.enable_ui() # Kích hoạt lại giao diện
        final_status = self.get_translation("status_processed_files", processed=processed_count, total=total_count)
        self.progress_label_var.set(final_status)
        self.status_label.config(text=final_status)
        self.progress_var.set(100 if total_count > 0 else 0) # Đặt 100% nếu có file xử lý
        save_config(self.config) # Lưu cấu hình

        if not all_detailed_errors:
            # Hoàn thành tất cả không có lỗi/cảnh báo nào
            self.log_message(self.get_translation("log_batch_complete_all_success"))
            logging.info(f"Hoàn thành xử lý batch {processed_count}/{total_count} file thành công.")
            messagebox.showinfo(self.get_translation("msg_info_title"), self.get_translation("msg_batch_complete_success", processed=processed_count, total=total_count))
        else:
             # Hoàn thành nhưng có lỗi/cảnh báo
             self.log_message(self.get_translation("log_batch_complete_with_errors"))
             logging.warning(f"Hoàn thành xử lý batch với {len(all_detailed_errors)} lỗi/cảnh báo chi tiết.")
             # Hỏi có muốn xuất báo cáo lỗi không
             export_report = messagebox.askyesno(
                 self.get_translation("msg_warning_title"),
                 self.get_translation("msg_batch_complete_error_summary", processed=processed_count, total=total_count),
                 parent=self.root
             )
             if export_report:
                 self.export_error_report(all_detailed_errors) # Xuất báo cáo
             else:
                 # Nếu không xuất, ghi tóm tắt vào log
                 error_summary = self.get_translation("msg_batch_complete_error_summary", processed=processed_count, total=total_count).split('\n\n')[0] # Lấy phần tóm tắt
                 files_with_errors = set(e['file'] for e in all_detailed_errors if e.get('file')) # Đếm số file có lỗi
                 error_summary += f"\n{self.get_translation('msg_error_title')}: {len(files_with_errors)} file(s)."
                 error_summary += self.get_translation("msg_batch_error_check_log")
                 self.log_message(error_summary)

    def export_error_report(self, error_list):
        """Xuất danh sách lỗi chi tiết ra file Excel."""
        if not error_list:
            self.log_message("Không có lỗi nào để xuất báo cáo.")
            return
        try:
            # Tạo DataFrame từ danh sách lỗi
            df = pd.DataFrame(error_list)

            # Đổi tên cột sang ngôn ngữ hiện tại
            column_mapping = {
                'file': self.get_translation("error_report_col_file"),
                'row': self.get_translation("error_report_col_row"),
                'column': self.get_translation("error_report_col_column"),
                'value': self.get_translation("error_report_col_value"),
                'type': self.get_translation("error_report_col_type"),
                'message': self.get_translation("error_report_col_message"),
            }
            df.rename(columns=column_mapping, inplace=True)

            # Dịch giá trị trong cột "Loại lỗi"
            error_type_col_name = self.get_translation("error_report_col_type")
            if error_type_col_name in df.columns:
                df[error_type_col_name] = df[error_type_col_name].apply(
                    lambda x: self.get_translation(x) if isinstance(x, str) and x.startswith("error_type_") else x
                )

            # Sắp xếp lại thứ tự cột mong muốn
            cols_order = [
                self.get_translation("error_report_col_file"),
                self.get_translation("error_report_col_row"),
                self.get_translation("error_report_col_column"),
                self.get_translation("error_report_col_value"),
                self.get_translation("error_report_col_type"),
                self.get_translation("error_report_col_message"),
            ]
            # Lọc ra các cột thực sự tồn tại trong DataFrame để tránh lỗi
            existing_cols_order = [col for col in cols_order if col in df.columns]
            df = df[existing_cols_order]

            # Tạo tên file báo cáo lỗi duy nhất
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = ERROR_REPORT_FILENAME.format(timestamp=timestamp)

            # Xác định thư mục lưu báo cáo lỗi
            output_location = None
            if not self.is_input_single_file and self.output_dir_var.get() and os.path.isdir(self.output_dir_var.get()):
                output_location = self.output_dir_var.get()
            elif self.is_input_single_file and self.output_file_var.get():
                 output_file_dir = os.path.dirname(self.output_file_var.get())
                 if os.path.isdir(output_file_dir):
                     output_location = output_file_dir
            # Nếu không xác định được thư mục output, lưu cùng chỗ với file config
            if not output_location:
                 config_dir = os.path.dirname(CONFIG_FILE)
                 output_location = config_dir if config_dir and os.path.isdir(config_dir) else '.' # Mặc định là thư mục hiện tại

            report_filepath = os.path.join(output_location, report_filename)

            # Xuất ra file Excel
            sheet_name = self.get_translation("error_report_sheet_name")
            df.to_excel(report_filepath, index=False, sheet_name=sheet_name)

            # Thông báo thành công
            success_msg = self.get_translation("msg_error_report_success", path=report_filepath)
            self.log_message(success_msg)
            messagebox.showinfo(self.get_translation("msg_info_title"), success_msg)
            logging.info(f"Đã xuất báo cáo lỗi: {report_filepath}")

        except Exception as e:
            # Thông báo thất bại
            err_msg = self.get_translation("msg_error_report_failed", error=e)
            self.log_message(err_msg)
            messagebox.showerror(self.get_translation("msg_error_title"), err_msg)
            logging.error(f"Xuất báo cáo lỗi thất bại: {e}")

    # --- Log & Progress Update Methods ---
    def log_message(self, message):
        """Ghi thông điệp vào ô log trên GUI."""
        # Chỉ thực hiện nếu widget log_text còn tồn tại
        if self.log_text.winfo_exists():
            self.log_text.config(state='normal') # Cho phép sửa đổi
            self.log_text.insert(tk.END, message + "\n") # Thêm tin nhắn và xuống dòng
            self.log_text.see(tk.END) # Tự động cuộn xuống dòng cuối
            self.log_text.config(state='disabled') # Chặn sửa đổi từ người dùng
            self.root.update_idletasks() # Cập nhật giao diện

    def log_message_threadsafe(self, message):
        """Gửi yêu cầu ghi log từ luồng phụ về luồng chính GUI."""
        self.root.after(0, self.log_message, message)

    def update_progress(self, value):
        """Cập nhật giá trị thanh tiến trình."""
        if self.progress_bar.winfo_exists():
            self.progress_var.set(value)
            self.root.update_idletasks()

    def update_progress_threadsafe(self, value):
        """Gửi yêu cầu cập nhật tiến trình từ luồng phụ về luồng chính GUI."""
        self.root.after(0, self.update_progress, value)

    def update_progress_label(self, text):
        """Cập nhật nhãn trạng thái tiến trình và thanh status bar."""
        if self.progress_status_label.winfo_exists():
            self.progress_label_var.set(text)
        if self.status_label.winfo_exists():
            self.status_label.config(text=text) # Cập nhật cả status bar
        self.root.update_idletasks()

# --- Entry Point ---
if __name__ == "__main__":
    # --- Kiểm tra thư viện cần thiết ---
    missing_libs = []
    lib_map = {
        "qrcode[pil]": ["qrcode", "PIL"],
        "pandas openpyxl": ["pandas", "openpyxl"],
        "docxtpl python-docx": ["docxtpl", "docx"]
    }
    install_commands = []

    try: import qrcode; import PIL
    except ImportError: missing_libs.extend(lib_map["qrcode[pil]"]); install_commands.append("qrcode[pil]")
    try: import pandas; import openpyxl
    except ImportError: missing_libs.extend(lib_map["pandas openpyxl"]); install_commands.append("pandas openpyxl")
    try: import docxtpl; import docx
    except ImportError: missing_libs.extend(lib_map["docxtpl python-docx"]); install_commands.append("docxtpl python-docx")

    # Nếu thiếu thư viện, hiển thị thông báo và thoát
    if missing_libs:
        # Cố gắng lấy bản dịch tiếng Việt nếu có thể
        lang = DEFAULT_LANGUAGE
        try:
            # Tải nhanh config chỉ để lấy ngôn ngữ nếu có
            temp_config = load_config()
            lang = temp_config.get('Settings', 'language', fallback=DEFAULT_LANGUAGE)
        except Exception:
            pass # Bỏ qua nếu không đọc được config

        error_msg = translations["log_missing_lib_error"][lang].format(name=', '.join(missing_libs))
        install_msg = translations["log_install_libs"][lang]
        command_msg = f"pip install {' '.join(install_commands)}\n"
        exit_msg = translations["log_press_enter"][lang]

        # In ra console vì GUI chưa khởi tạo
        print(error_msg)
        print(install_msg)
        print(command_msg)
        input(exit_msg)
        sys.exit(1) # Thoát với mã lỗi

    # --- Khởi tạo và chạy ứng dụng Tkinter ---
    root = tk.Tk()
    app = App(root)

    # --- Xử lý sự kiện đóng cửa sổ ---
    def on_closing():
        """Lưu cấu hình trước khi đóng ứng dụng."""
        try:
            save_config(app.config) # Lưu trạng thái cuối cùng
            logging.info(app.get_translation("log_app_closed")) # Ghi log đóng ứng dụng
        except Exception as e:
             logging.error(f"Lỗi khi lưu config lúc đóng ứng dụng: {e}")
        finally:
            root.destroy() # Đóng cửa sổ

    root.protocol("WM_DELETE_WINDOW", on_closing) # Gán hàm on_closing cho sự kiện đóng
    root.mainloop() # Bắt đầu vòng lặp sự kiện chính của Tkinter