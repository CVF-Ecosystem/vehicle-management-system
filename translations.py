# translations.py
# Bilingual Translation File for Tan Thuan Vehicle Management System
# Terminology updated based on industry standards.

translations = {
    # ===================================================================
    # == 1. GENERAL & MAIN WINDOW
    # ===================================================================
    "app_title": {"vi": "Phần mềm Quản lý Xe", "en": "Vehicle Management System"},
    "status_ready": {"vi": "Sẵn sàng", "en": "Ready"},
    "status_loading": {"vi": "Đang tải dữ liệu", "en": "Loading data"},
    "status_exporting": {"vi": "Đang xuất file", "en": "Exporting file"},
    "status_stock_count": {"vi": "Số xe tồn: {count}", "en": "Yard Stock: {count}"},
    "status_search_result": {"vi": "Tìm thấy {count} kết quả.", "en": "Found {count} results."},
    "author_credit": {"vi": "Phát triển bởi: Tiền-Cảng Tân Thuận", "en": "Developed by: Tien-Tan Thuan Port"},
    "confirm_exit_title": {"vi": "Xác nhận thoát", "en": "Confirm Exit"},
    "confirm_exit_msg": {"vi": "Bạn có chắc chắn muốn thoát?", "en": "Are you sure you want to exit?"},

    # ===================================================================
    # == 2. MAIN MENU
    # ===================================================================
    "menu_file": {"vi": "Tệp", "en": "File"},
    "menu_tools": {"vi": "Công cụ", "en": "Tools"},
    "menu_settings": {"vi": "Cài đặt", "en": "Configuration"},
    "menu_exit": {"vi": "Thoát", "en": "Exit"},
    "menu_create_vouchers": {"vi": "Tạo phiếu vận chuyển", "en": "Generate Transfer Slips"},
    "menu_language": {"vi": "Ngôn ngữ", "en": "Language"},
    "menu_theme": {"vi": "Giao diện", "en": "Theme"},
    "menu_archive": {"vi": "Lưu trữ dữ liệu ", "en": "Archive Dispatched Data"},
    "menu_manage_drivers": {"vi": "Quản lý tài xế", "en": "Manage Drivers"},
    "menu_manage_transports": {"vi": "Quản lý xe vận chuyển", "en": "Manage Transport Vehicles"},
    "menu_manage_layout": {"vi": "Quản lý Layout bãi xe", "en": "Manage Yard Layout"},
    "menu_select_voucher_template": {"vi": "Chọn mẫu phiếu vận chuyển", "en": "Select Tranfer Slips Template"},
    "theme_light": {"vi": "Sáng", "en": "Light"},
    "theme_dark": {"vi": "Tối", "en": "Dark"},
    "theme_system": {"vi": "Hệ thống", "en": "System"},
    "lang_vi": {"vi": "Tiếng Việt", "en": "Vietnamese"},
    "lang_en": {"vi": "Tiếng Anh", "en": "English"},

    # ===================================================================
    # == 3. TABS
    # ===================================================================
    "tab_inbound": {"vi": "Nhập bãi", "en": "Inbound Transfer"},
    "tab_dispatch": {"vi": "🚚 Xuất bãi (nhiều)", "en": "🚚 Batch Dispatch"},
    "tab_outbound": {"vi": "Xuất bãi (lẻ)", "en": "Single Dispatch"},
    "tab_stock": {"vi": "Tồn bãi", "en": "Yard Stock"},
    "tab_search": {"vi": "🔍 Tra cứu", "en": "🔍 Search"},
    "tab_dashboard": {"vi": "📊 Báo cáo", "en": "📊 Dashboard"},
    "tab_log": {"vi": "Nhật ký hoạt động", "en": "Activity Log"},

    # ===================================================================
    # == 4. WIDGETS (LABELS, BUTTONS, HEADERS)
    # ===================================================================
    # --- Common ---
    "lbl_vin": {"vi": "Số khung (VIN):", "en": "VIN:"},
    "lbl_owner": {"vi": "Chủ hàng:", "en": "Owner:"},
    "lbl_vehicle_type": {"vi": "Loại xe:", "en": "Vehicle Type:"},
    "lbl_location": {"vi": "Vị trí bãi:", "en": "Yard Location:"},
    "lbl_transport_vehicle": {"vi": "Xe vận chuyển:", "en": "Transport Veh.:"},
    "lbl_driver": {"vi": "Tài xế:", "en": "Driver:"},
    "lbl_notes": {"vi": "Ghi chú", "en": "Notes"},
    "btn_save": {"vi": "Lưu", "en": "Save"},
    "btn_cancel": {"vi": "Hủy", "en": "Cancel"},
    "btn_ok": {"vi": "OK", "en": "OK"},
    "btn_add_new": {"vi": "Thêm mới", "en": "Add New"},
    "btn_import_excel": {"vi": "Import Excel", "en": "Import Excel"},
    "btn_edit": {"vi": "Chỉnh sửa", "en": "Edit"},
    "btn_delete": {"vi": "Xóa", "en": "Delete"},
    "combobox_all": {"vi": "Tất cả", "en": "All"},

    # --- Inbound Tab ---
    "frame_manual_entry": {"vi": "Nhập thủ công (Gate In)", "en": "Manual Entry (Gate In)"},
    "frame_bulk_import": {"vi": "Nhập hàng loạt (Excel)", "en": "Bulk Import (Excel)"},
    "btn_save_vehicle": {"vi": "Lưu", "en": "Save"},
    "btn_find_location": {"vi": "Tự động tìm", "en": "Auto Find"},

    # --- Dispatch Tab ---
    "frame_create_dispatch": {"vi": "Tạo phiếu vận chuyển", "en": "Generate New Transfer Slip"},
    "btn_create_dispatch": {"vi": "Tạo phiếu", "en": "Generate Slip"},
    "frame_current_dispatch_empty": {"vi": "Chưa có phiếu vận chuyển ", "en": "No open transfer slip"},
    "frame_current_dispatch_title": {"vi": "Đang xử lý phiếu #{id} (Tài xế: {driver} - Xe: {vehicle})", "en": "Processing Slip #{id} (Driver: {driver} - Vehicle: {vehicle})"},
    "lbl_add_vehicle_to_dispatch": {"vi": "Quét VIN để thêm xe:", "en": "Scan VIN to add:"},
    "btn_complete_dispatch": {"vi": "Hoàn tất", "en": "Complete"},
    "btn_cancel_dispatch": {"vi": "Hủy phiếu", "en": "Cancel Slip"},

    # --- Outbound Tab ---
    "frame_outbound_info": {"vi": "Xuất bãi (Gate Out)", "en": "Dispatch Processing (Gate Out)"},
    "lbl_scan_qr": {"vi": "Quét/Nhập VIN:", "en": "Scan/Input VIN:"},
    "btn_process_dispatch": {"vi": "Xuất", "en": "Process Dispatch"},

    # --- Stock Tab ---
    "lbl_filter_owner": {"vi": "Lọc theo chủ hàng:", "en": "Filter by Owner:"},
    "lbl_search_vin_owner": {"vi": "Tìm kiếm (VIN/Chủ hàng):", "en": "Search (VIN/Owner):"},
    "btn_refresh": {"vi": "Làm mới", "en": "Refresh"},
    "btn_export_reports": {"vi": "Xuất báo cáo ▼", "en": "Export Reports ▼"},
    "menu_export_stock": {"vi": "Báo cáo tồn (Excel)", "en": "Stock Report (Excel)"},
    "menu_export_summary": {"vi": "Tổng hợp xuất bãi (Excel)", "en": "Dispatch Summary (Excel)"},
    "menu_export_history": {"vi": "Lịch sử xuất bãi (Excel)", "en": "Dispatch History (Excel)"},

    # --- Search Tab ---
    "frame_global_search": {"vi": "Tìm kiếm", "en": "Search"},
    "btn_search": {"vi": "Tìm kiếm", "en": "Search"},

    # --- Dashboard Tab ---
    "btn_update_dashboard": {"vi": "Cập nhật", "en": "Update"},
    "btn_export_png": {"vi": "💾 Xuất ảnh PNG", "en": "💾 Export PNG"},
    "btn_export_pdf": {"vi": "🧾 Xuất báo cáo PDF", "en": "🧾 Export PDF Report"},
    "cbx_auto_refresh": {"vi": "Tự động làm mới sau", "en": "Auto refresh every"},
    "lbl_minutes": {"vi": "phút", "en": "minutes"},

    # --- Treeview Headers ---
    "tree_stt": {"vi": "STT", "en": "No."},
    "tree_vin": {"vi": "SỐ KHUNG", "en": "VIN"},
    "tree_owner": {"vi": "CHỦ HÀNG", "en": "OWNER"},
    "tree_type": {"vi": "LOẠI XE", "en": "VEHICLE TYPE"},
    "tree_location": {"vi": "VỊ TRÍ BÃI", "en": "YARD LOCATION"},
    "tree_status": {"vi": "TRẠNG THÁI", "en": "STATUS"},
    "tree_date_in": {"vi": "NGÀY NHẬP ", "en": "DATE IN "},
    "tree_date_out": {"vi": "NGÀY XUẤT ", "en": "DATE OUT "},
    "tree_transport_vehicle": {"vi": "XE VẬN CHUYỂN", "en": "TRANSPORT VEH."},
    "tree_driver": {"vi": "TÀI XẾ", "en": "DRIVER"},
    "excel_days_in_stock": {"vi": "SỐ NGÀY TỒN", "en": "DAYS IN STOCK"},
    "excel_days_stored": {"vi": "SỐ NGÀY LƯU bãi", "en": "DAYS STORED"},
    
    # ===================================================================
    # == 5. DIALOGS & POP-UPS
    # ===================================================================
    "lbl_from_date": {"vi": "Từ ngày:", "en": "From:"},
    "lbl_to_date": {"vi": "Đến ngày:", "en": "To:"},
    "dialog_manage_drivers_title": {"vi": "Danh sách xài xế", "en": "Driver Management"},
    "dialog_manage_transports_title": {"vi": "Danh sách xe vận chuyển", "en": "Transport Vehicle Management"},
    "dialog_add_driver_title": {"vi": "Thêm tài xế mới", "en": "Add New Driver"},
    "dialog_edit_driver_title": {"vi": "Chỉnh sửa tài xế", "en": "Edit Driver"},
    "dialog_add_transport_title": {"vi": "Thêm xe vận chuyển mới", "en": "Add New Transport Vehicle"},
    "dialog_edit_transport_title": {"vi": "Chỉnh sửa xe vận chuyển", "en": "Edit Transport Vehicle"},
    "lbl_driver_name": {"vi": "Tên tài xế", "en": "Driver Name"},
    "lbl_cccd": {"vi": "Số CCCD", "en": "ID Card Number"},
    "lbl_phone": {"vi": "Số điện thoại", "en": "Phone Number"},
    "lbl_license_plate": {"vi": "Biển số xe", "en": "License Plate"},

    # --- Context Menu ---
    "ctx_menu_edit": {"vi": "Chỉnh sửa thông tin", "en": "Edit Information"},
    "ctx_menu_swap_location": {"vi": "Đảo vị trí", "en": "Swap Location"},
    "ctx_menu_delete": {"vi": "Xóa xe (ẩn)", "en": "Delete Vehicle (hide)"},
    # === BỔ SUNG MỚI ===
    "ctx_menu_cut": {"vi": "Cắt", "en": "Cut"},
    "ctx_menu_copy": {"vi": "Sao chép", "en": "Copy"},
    "ctx_menu_paste": {"vi": "Dán", "en": "Paste"},
    # --- Dialogs & Messages ---
    "dialog_swap_location_title": {"vi": "Đảo vị trí xe", "en": "Swap Vehicle Location"},
    "lbl_current_location": {"vi": "Vị trí hiện tại:", "en": "Current Location:"},
    "lbl_new_location": {"vi": "Chọn vị trí mới:", "en": "Select New Location:"},
    
    # === BỔ SUNG MỚI ===
    "lbl_location_id_info": {"vi": "ID vị trí: {id}", "en": "Location ID: {id}"},
    "dialog_print_tag_title": {"vi": "In QR Code", "en": "Print Vehicle QR Code"},
    "dialog_print_tag_prompt": {"vi": "Đã thêm xe {vin} thành công.\nBạn có muốn in Qr code định danh cho xe này không?", "en": "Vehicle {vin} was added successfully.\nDo you want to print an identification Qr code for this vehicle?"},
    # ===================

    "btn_confirm": {"vi": "Xác nhận", "en": "Confirm"},
    "dialog_conditional_formatting_title": {"vi": "Định dạng có điều kiện", "en": "Conditional Formatting"},
    "dialog_conditional_formatting_prompt": {"vi": "Tô màu những xe tồn kho quá (ngày)?\n(Bỏ trống hoặc nhấn Cancel nếu không muốn)", "en": "Highlight vehicles in stock over (days)?\n(Leave blank or press Cancel for no highlight)"},
    
    # ===================================================================
    # == 6. MESSAGES & TOASTS
    # ===================================================================
    "toast_add_success": {"vi": "Đã nhập xe thành công!", "en": "Vehicle checked in successfully!"},
    "toast_shipped_success": {"vi": "Đã xuất xe {vin}", "en": "Dispatched vehicle {vin}"},
    "toast_export_success": {"vi": "Đã xuất file thành công!", "en": "File exported successfully!"},
    "warn_missing_info": {"vi": "Thiếu thông tin", "en": "Missing Information"},
    "warn_missing_info_msg": {"vi": "Vui lòng nhập đủ Số khung và Chủ hàng.", "en": "Please enter both VIN and Owner."},
    "warn_not_found": {"vi": "Không tìm thấy", "en": "Not Found"},
    "warn_not_found_msg": {"vi": "VIN {vin} không tồn tại trong kho.", "en": "VIN {vin} not found in stock."},
    "info_no_data_in_range": {"vi": "Không có dữ liệu", "en": "No Data"},
    "info_no_data_in_range_msg": {"vi": "Không có dữ liệu trong khoảng thời gian đã chọn.", "en": "No data found in the selected time range."},
    "confirm_delete_title": {"vi": "Xác nhận xóa", "en": "Confirm Deletion"},
    "confirm_delete_msg": {"vi": "Bạn có chắc chắn muốn xóa '{item}'?", "en": "Are you sure you want to delete '{item}'?"},
    "warn_missing_dispatch_info": {"vi": "Thiếu thông tin", "en": "Missing Information"},
    "warn_missing_dispatch_info_msg": {"vi": "Vui lòng chọn Tài xế và Xe vận chuyển.", "en": "Please select a Driver and a Transport Vehicle."},
    "toast_dispatch_created": {"vi": "Đã tạo phiếu Vận chuyển #{id}", "en": "Generated Transfer Slip #{id}"},
    "warn_not_in_stock_or_added": {"vi": "Xe không hợp lệ", "en": "Invalid Vehicle"},
    "warn_not_in_stock_or_added_msg": {"vi": "Xe {vin} không có trong kho hoặc đã được thêm vào phiếu này.", "en": "Vehicle {vin} is not in stock or has already been added to this slip."},
    "toast_vehicle_added_to_shipment": {"vi": "Đã thêm xe {vin} vào phiếu", "en": "Added vehicle {vin} to slip"},
    "confirm_complete_dispatch_title": {"vi": "Xác nhận Hoàn tất", "en": "Confirm Completion"},
    "confirm_complete_dispatch_msg": {"vi": "Bạn có chắc chắn muốn hoàn tất và xuất kho tất cả xe trong phiếu #{id} không?", "en": "Are you sure you want to complete and dispatch all vehicles in Slip #{id}?"},
    "confirm_cancel_dispatch_title": {"vi": "Xác nhận Hủy phiếu", "en": "Confirm Slip Cancellation"},
    "confirm_cancel_dispatch_msg": {"vi": "Bạn có chắc chắn muốn hủy phiếu #{id} không?\nMọi xe đã thêm vào sẽ được trả về trạng thái tồn kho.", "en": "Are you sure you want to cancel Slip #{id}?\nAll added vehicles will be returned to stock status."},
    "prompt_add_new_driver": {"vi": "Tài xế '{name}' chưa có trong danh sách.\nBạn có muốn tự động thêm mới tài xế này không?", "en": "Driver '{name}' is not in the list.\nDo you want to automatically add this new driver?"},
    "prompt_add_new_transport": {"vi": "Xe vận chuyển '{plate}' chưa có trong danh sách.\nBạn có muốn tự động thêm mới xe này không?", "en": "Transport vehicle '{plate}' is not in the list.\nDo you want to automatically add this new vehicle?"},

    # ===================================================================
    # == 7. REPORTS (PDF, EXCEL)
    # ===================================================================
    "report_vehicle_stock": {"vi": "Báo cáo Tồn bãi Xe", "en": "Vehicle Stock Report"},
    "report_dispatch_summary": {"vi": "Báo cáo tổng hợp", "en": "Summary Report"},
    "report_dispatch_history": {"vi": "Báo cáo lịch sử xuất bãi", "en": "Dispatch History Report"},
    "db_main_title": {"vi": "THỐNG KÊ NHẬP - XUẤT", "en": "INBOUND - OUTBOUND STATISTICS"},
    "db_bar_chart_title": {"vi": "Thống kê Nhập-Xuất-Tồn theo Chủ hàng", "en": "In-Out-Stock Statistics by Owner"},
    "db_pie_chart_title": {"vi": "Tỷ lệ Tồn theo Chủ hàng", "en": "Stock Ratio by Owner"},
    "db_bar_label_in": {"vi": "Nhập", "en": "Inbound"},
    "db_bar_label_out": {"vi": "Xuất", "en": "Outbound"},
    "db_bar_label_stock": {"vi": "Tồn", "en": "Stock"},
    "pdf_report_title": {"vi": "BÁO CÁO THỐNG KÊ TỒN KHO", "en": "YARD STOCK STATISTICAL REPORT"},
    "pdf_shift": {"vi": "Ca làm việc: <b>{shift}</b>", "en": "Work Shift: <b>{shift}</b>"},
    "pdf_shift_day": {"vi": "Ca ngày (06:00 - 18:00)", "en": "Day Shift (06:00 - 18:00)"},
    "pdf_shift_night": {"vi": "Ca đêm (18:00 - 06:00)", "en": "Night Shift (18:00 - 06:00)"},
    "pdf_date_range": {"vi": "Thời gian: {start} - {end}", "en": "Period: {start} - {end}"},
    "pdf_report_date": {"vi": "Ngày lập báo cáo: {date}", "en": "Report Date: {date}"},
    "pdf_total_row": {"vi": "TỔNG CỘNG", "en": "TOTAL"},
    "pdf_col_total_in": {"vi": "TỔNG NHẬP", "en": "TOTAL IN"},
    "pdf_col_total_out": {"vi": "TỔNG XUẤT", "en": "TOTAL OUT"},
    "pdf_col_stock": {"vi": "TỒN bãi", "en": "IN STOCK"},


    # --- Cửa sổ Quản lý Layout ---
    "manage_layout_title": {"vi": "Quản lý Layout", "en": "Manage Yard Layout"},
    "frame_manual_layout": {"vi": "Tạo Layout:", "en": "Manual Layout Generate:"},
    "placeholder_block": {"vi": "Tên Lô (ví dụ: A, KHU CFS)", "en": "Block Name (e.g., A, CFS AREA)"},
    "placeholder_row_start": {"vi": "Từ Dãy (số)", "en": "From Row (number)"},
    "placeholder_row_end": {"vi": "Đến Dãy (số)", "en": "To Row (number)"},
    "placeholder_slots": {"vi": "Số Ô/Dãy", "en": "Slots/Row"},
    "btn_generate": {"vi": "Tạo Vị trí", "en": "Generate Locations"},
    "frame_import_layout": {"vi": "Tạo Layout từ File Excel:", "en": "Generate Layout from Excel File:"},
    "btn_import_excel_source": {"vi": "Chọn File Excel", "en": "Select Excel File"},
    "btn_download_template": {"vi": "Tải file mẫu", "en": "Download Template"},
    "info_generate_success": {"vi": "Hoàn tất!\n- Đã tạo mới: {s}\n- Bỏ qua (đã tồn tại): {e}", "en": "Completed!\n- Newly Generated: {s}\n- Skipped (already exist): {e}"},
    "info_import_success": {"vi": "Hoàn tất Import!\n- Tạo mới thành công: {s}\n- Bỏ qua (đã tồn tại): {e}", "en": "Import Complete!\n- Successfully Generated: {s}\n- Skipped (already exist): {e}"},
    "err_invalid_input": {"vi": "Lỗi", "en": "Error"},
    "err_invalid_input_msg": {"vi": "Dữ liệu nhập vào phải là số.", "en": "Input data must be numbers."},
    "err_column_missing": {"vi": "Lỗi Cột", "en": "Column Error"},
    "err_read_file": {"vi": "Lỗi", "en": "Error"},

    # --- Dialogs Quản lý và Chỉnh sửa ---
    "manage_drivers_title": {"vi": "Quản lý Tài xế", "en": "Manage Drivers"},
    "manage_transport_vehicles_title": {"vi": "Quản lý Xe vận chuyển", "en": "Manage Transport Vehicles"},
    "btn_save": {"vi": "Lưu", "en": "Save"},
    "btn_ok": {"vi": "OK", "en": "OK"},
    "btn_cancel": {"vi": "Hủy", "en": "Cancel"},
    "btn_add_new": {"vi": "Thêm mới", "en": "Add New"},
    "btn_edit": {"vi": "Chỉnh sửa", "en": "Edit"},
    "btn_delete": {"vi": "Xóa", "en": "Delete"},
    "warn_no_selection": {"vi": "Chưa chọn mục", "en": "No Item Selected"},
    "warn_no_selection_msg": {"vi": "Vui lòng chọn một mục trong danh sách.", "en": "Please select an item from the list."},
    "warn_field_empty_msg": {"vi": "Trường '{field}' không được để trống.", "en": "The '{field}' field cannot be empty."},
    "add_driver_title": {"vi": "Thêm Tài xế mới", "en": "Add New Driver"},
    "edit_driver_title": {"vi": "Chỉnh sửa thông tin Tài xế", "en": "Edit Driver Information"},
    "add_transport_title": {"vi": "Thêm Xe vận chuyển mới", "en": "Add New Transport Vehicle"},
    "edit_transport_title": {"vi": "Chỉnh sửa thông tin Xe vận chuyển", "en": "Edit Transport Vehicle Information"},
    "field_driver_name": {"vi": "Tên tài xế", "en": "Driver Name"},
    "field_phone": {"vi": "Số điện thoại", "en": "Phone Number"},
    "field_cccd": {"vi": "Số CCCD", "en": "ID Number"},
    "field_notes": {"vi": "Ghi chú", "en": "Notes"},
    "field_license_plate": {"vi": "Biển số xe", "en": "License Plate"},
    "field_vehicle_type_transport": {"vi": "Loại xe (vận chuyển)", "en": "Vehicle Type (Transport)"},
    "confirm_delete_title": {"vi": "Xác nhận Xóa", "en": "Confirm Deletion"},
    "confirm_delete_msg": {"vi": "Bạn có chắc muốn xóa '{item}' không?\nHành động này sẽ ẩn mục này đi.", "en": "Are you sure you want to delete '{item}'?\nThis action will hide the item."},
    "btn_import_from_excel": {"vi": "Import từ Excel", "en": "Import from Excel"},
    "btn_export_to_excel": {"vi": "Export ra Excel", "en": "Export to Excel"},
    "import_summary_title": {"vi": "Kết quả Import", "en": "Import Result"},
    "import_summary_message": {"vi": "Hoàn tất!\n- Thêm mới thành công: {s}\n- Bỏ qua (đã tồn tại): {e}", "en": "Completed!\n- Successfully added: {s}\n- Skipped (already exist): {e}"},
    "err_column_missing_generic": {"vi": "Lỗi Cột", "en": "Column Error"},
    "err_column_missing_msg": {"vi": "File Excel phải chứa cột bắt buộc: {col}", "en": "Excel file must contain the required column: {col}"},
    
    # --- Công cụ Tạo phiếu VC ---
    "dialog_create_vouchers_title": {"vi": "Tạo phiếu", "en": "Generate Transfer Slips"},
    "lbl_excel_file_path": {"vi": "File dữ liệu (Excel):", "en": "Data File (Excel):"},
    "lbl_word_template_path": {"vi": "File mẫu (Word):", "en": "Template File (Word):"},
    "lbl_output_file_path": {"vi": "File xuất ra:", "en": "Output File:"},
    "btn_create_vouchers": {"vi": "Tạo phiếu", "en": "Generate Transfer Slips"},
    "btn_select_file": {"vi": "Chọn File", "en": "Select File"},
    "btn_select_template": {"vi": "Chọn Mẫu", "en": "Select Template"},
    "btn_save_as": {"vi": "Lưu", "en": "Save As"},
    "log_ready": {"vi": "Sẵn sàng.", "en": "Ready."},
    "log_reading_excel": {"vi": "Bắt đầu đọc file Excel", "en": "Starting to read Excel file"},
    "log_read_excel_done": {"vi": "Đã đọc {count} dòng từ file Excel.", "en": "Read {count} rows from Excel file."},
    "log_creating_word": {"vi": "Bắt đầu tạo file Word", "en": "Starting to generate Word file"},
    "log_success": {"vi": "THÀNH CÔNG! Đã tạo file phiếu tại: {path}", "en": "SUCCESS! Transfer slips file generated at: {path}"},
    "log_error": {"vi": "LỖI: {error}", "en": "ERROR: {error}"},
    "log_critical_error": {"vi": "LỖI NGHIÊM TRỌNG: {error}", "en": "CRITICAL ERROR: {error}"},
    "msgbox_fill_all_paths": {"vi": "Vui lòng điền đầy đủ các đường dẫn file.", "en": "Please fill in all file paths."},
    "msgbox_creation_complete_title": {"vi": "Hoàn tất", "en": "Completed"},
    "msgbox_creation_complete_prompt": {"vi": "Tạo phiếu thành công!\nBạn có muốn mở file không?", "en": "Transfer slips generated successfully!\nDo you want to open the file?"},
    # === BỔ SUNG: Key cho Công cụ Quản lý xe đã xóa ===
    "menu_deleted_vehicles": {"vi": "Quản lý xe đã xóa", "en": "Manage Deleted Vehicles"},
    # === BỔ SUNG: Key cho Công cụ Tra cứu Lưu trữ ===
    "menu_archive_explorer": {"vi": "Tra cứu dữ liệu lưu trữ", "en": "Explore Archived Data"},
    "dialog_archive_explorer_title": {"vi": "Tra cứu", "en": "Explorer"},
    "lbl_select_archive_file": {"vi": "Chọn File lưu trữ:", "en": "Select Archive File:"},
    "lbl_time_period": {"vi": "Khoảng thời gian:", "en": "Time Period:"},
    "lbl_not_selected": {"vi": "Chưa chọn", "en": "Not selected"},
    "btn_select_period": {"vi": "Chọn", "en": "Select"},
    "btn_export_archive_to_excel": {"vi": "Xuất ra Excel", "en": "Export to Excel"},
    "msg_no_archive_folder": {"vi": "Không tìm thấy thư mục lưu trữ", "en": "Archive folder not found"},
    "msg_no_archive_files": {"vi": "Không có file lưu trữ nào", "en": "No archive files found"},
    "err_select_valid_archive": {"vi": "Vui lòng chọn một file lưu trữ hợp lệ.", "en": "Please select a valid archive file."},
    "err_select_time_period": {"vi": "Vui lòng chọn khoảng thời gian để tra cứu.", "en": "Please select a time period to search."},
    "err_archive_file_not_exist": {"vi": "File lưu trữ được chọn không tồn tại.", "en": "The selected archive file does not exist."},
    "err_cannot_read_archive": {"vi": "Không thể đọc file lưu trữ:\n{error}", "en": "Could not read archive file:\n{error}"},
    "info_no_data_in_archive": {"vi": "Không tìm thấy dữ liệu nào trong khoảng thời gian đã chọn.", "en": "No data found in the selected time period."},
    "toast_export_archive_success": {"vi": "Xuất file lưu trữ thành công!", "en": "Archive file exported successfully!"},
    # === BỔ SUNG: Key chung cho tiêu đề các hộp thoại lỗi ===
    "dialog_error_title": {"vi": "Lỗi", "en": "Error"},
    "dialog_info_title": {"vi": "Thông báo", "en": "Information"},
    "dialog_warning_title": {"vi": "Cảnh báo", "en": "Warning"},
    # === BỔ SUNG: Key cho Phân trang ===
    "pagination_prev": {"vi": "< Trang trước", "en": "< Previous"},
    "pagination_next": {"vi": "Trang sau >", "en": "Next >"},
    "pagination_page_info": {"vi": "Trang {current} / {total}", "en": "Page {current} / {total}"},

    # === BỔ SUNG: Key cho các hardcoded strings ===
    "warn_no_location_available": {"vi": "Hết chỗ", "en": "No Available Slot"},
    "warn_no_location_available_msg": {"vi": "Không tìm thấy vị trí nào còn trống trong bãi.", "en": "No available parking slots found in the yard."},
    "warn_no_location_selected": {"vi": "Vui lòng chọn vị trí bãi cho xe.", "en": "Please select a yard location for the vehicle."},
    "dialog_save_qr_title": {"vi": "Lưu file QR Code PDF", "en": "Save QR Code PDF File"},
    "toast_qr_created_success": {"vi": "Đã tạo file QR Code thành công.", "en": "QR Code file created successfully."},
    "err_create_qr_title": {"vi": "Lỗi tạo QR Code", "en": "QR Code Generation Error"},
    "err_create_qr_msg": {"vi": "Không thể tạo file PDF:\n{error}", "en": "Could not create PDF file:\n{error}"},
    "import_result_title": {"vi": "Kết quả Import", "en": "Import Result"},
    "import_result_msg": {"vi": "Tổng số dòng xử lý: {total}\nThành công: {success}\nThất bại: {errors}\n\n(Chi tiết lỗi đã được hiển thị trong khung log)", "en": "Total rows processed: {total}\nSuccessful: {success}\nFailed: {errors}\n\n(Error details are shown in the log panel)"},
    "import_summary_log": {"vi": "Import hoàn tất: {success} thành công, {errors} lỗi.", "en": "Import completed: {success} successful, {errors} errors."},
    "confirm_archive_title": {"vi": "Xác nhận Lưu trữ", "en": "Confirm Archive"},
    "confirm_archive_msg": {"vi": "Bạn có chắc chắn muốn lưu trữ và XÓA vĩnh viễn dữ liệu xe đã xuất từ {start} đến {end} khỏi CSDL chính không?\n\nDữ liệu sẽ được chuyển sang một file lưu trữ riêng và không thể hoàn tác.", "en": "Are you sure you want to archive and PERMANENTLY DELETE exported vehicle data from {start} to {end} from the main database?\n\nData will be moved to a separate archive file and cannot be undone."},
    "status_archiving": {"vi": "Đang lưu trữ dữ liệu...", "en": "Archiving data..."},
    "dialog_archive_complete_title": {"vi": "Hoàn tất", "en": "Complete"},
    "err_add_fail": {"vi": "Lỗi thêm xe", "en": "Add Vehicle Error"},
    "err_load_dashboard": {"vi": "Không thể tải dữ liệu thống kê: {error}", "en": "Could not load statistics data: {error}"},
    "status_error": {"vi": "Lỗi", "en": "Error"},
    "warn_no_chart_title": {"vi": "Chưa có biểu đồ", "en": "No Chart Available"},
    "warn_no_chart_msg": {"vi": "Vui lòng cập nhật dashboard trước khi xuất.", "en": "Please update the dashboard before exporting."},
    "warn_invalid_vin_title": {"vi": "VIN không hợp lệ", "en": "Invalid VIN"},
    "warn_invalid_vin_msg": {"vi": "{error}", "en": "{error}"},

}