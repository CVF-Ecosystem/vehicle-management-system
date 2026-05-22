# main.py
import customtkinter as ctk
from tkinter import messagebox, Menu, filedialog
from datetime import datetime
import logging
import os

import utils
from utils import setup_logging, load_config, save_config
from database.base_manager import BaseManager
from database.vehicle_manager import VehicleManager
from database.entity_manager import EntityManager
from database.dispatch_manager import DispatchManager
from database.location_manager import LocationManager
from layout_manager import LayoutManager
from api_client import ApiClient

import excel_importer 

from translations import translations
from config import APP_VERSION, ENTITY_TYPE_DRIVER, ENTITY_TYPE_TRANSPORT

from ui.inbound_tab import InboundTab
from ui.outbound_tab import OutboundTab
from ui.stock_tab import StockTab
from ui.dashboard_tab import DashboardTab
from ui.search_tab import SearchTab
from ui.yard_map_tab import YardMapTab
from ui.log_tab import LogTab
from ui.dispatch_tab import DispatchTab
from ui.components import Toast, DateRangeDialog
from ui.management_dialogs import ManagementDialog
from ui.layout_management_dialog import LayoutManagementDialog
from ui.voucher_creation_dialog import VoucherCreationDialog
from ui.archive_explorer_dialog import ArchiveExplorerDialog # Đảm bảo import này tồn tại
from ui.deleted_vehicles_dialog import DeletedVehiclesDialog
from config import APP_VERSION, APP_NAME, FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_LARGE, FONT_SIZE_SMALL

# Phase 1C: Auth imports
from auth.auth_manager import AuthManager
from auth.permissions import Permission, get_role_display_name
from ui.login_dialog import LoginDialog, ChangePasswordDialog
from ui.user_management_dialog import UserManagementDialog, LoginHistoryDialog

# Phase 2.6: Notification imports
from core.notification_service import NotificationService, get_notification_service
from ui.notification_panel import NotificationPanel, NotificationBell, NotificationSettingsDialog

# 7.1-ARCH-1: Web Dashboard Manager (tách từ main.py)
from ui.web_dashboard_manager import WebDashboardManager

# 7.6-DEPLOY-1: Auto-update checker
from core.update_checker import check_for_updates


class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_logging()

        # SECURITY NOTE (7.3-SEC-1): Cơ chế unlock.txt đã bị xóa vì lý do bảo mật.
        # Cơ chế này cho phép bất kỳ ai có quyền ghi file vào thư mục ứng dụng
        # đều có thể reset mật khẩu admin — đây là backdoor không an toàn.
        # Để reset admin, hãy dùng script tools/reset_admin.py hoặc liên hệ quản trị viên.

        self.config = load_config()
        self.current_lang = ctk.StringVar(value=self.config.get("Settings", "language", fallback="vi"))
        self.current_theme = ctk.StringVar(value=self.config.get("Settings", "theme", fallback="System"))

        ctk.set_appearance_mode(self.current_theme.get())

        self.vehicle_manager = VehicleManager()
        self.entity_manager = EntityManager()
        self.dispatch_manager = DispatchManager()
        self.location_manager = LocationManager()
        self.layout_manager = LayoutManager(self.location_manager)

        self.api_client = ApiClient(self.vehicle_manager, self.entity_manager, self.dispatch_manager)

        # --- BỔ SUNG: Tạo các đối tượng Font tập trung ---
        self.font_normal = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        self.font_bold = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL, weight="bold")
        self.font_large_bold = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_LARGE, weight="bold")
        self.font_small = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL)
        self.font_small_italic = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL, slant="italic")
        # -------------------------------------------------

        # Phase 1C: Initialize Auth Manager
        self.auth_manager = AuthManager.get_instance()

        # Phase 2.6: Initialize Notification Service
        self.notification_service = NotificationService.get_instance()

        # Show login dialog first
        self._show_login_dialog()

    def _show_login_dialog(self):
        """Hiển thị dialog đăng nhập."""
        # Withdraw main window until login
        self.withdraw()
        
        # Wait for window to be ready
        self.after(100, self._open_login)
    
    def _open_login(self):
        """Mở dialog đăng nhập."""
        login_dialog = LoginDialog(self, on_success_callback=self._on_login_success)
        login_dialog.wait_window()
    
    def _on_login_success(self, user: dict):
        """Callback khi đăng nhập thành công."""
        logging.info(f"Đăng nhập thành công: {user['username']} ({user['role']})")
        
        # Show main window
        self.deiconify()
        
        # Build UI
        self._build_ui()
        
        # === PHASE 2.4: Setup global keyboard shortcuts ===
        self._setup_keyboard_shortcuts()
        
        # === PHASE 2.6: Start notification checks ===
        self._setup_notification_checks()
        
        # 7.1-ARCH-1: Initialize Web Dashboard Manager
        self._web_dashboard = WebDashboardManager(self)
        
        # PERF-02: Chuẩn hóa tên chủ hàng trong background (có cache)
        self.status_var.set("Đang chuẩn hóa dữ liệu chủ hàng...")
        self.vehicle_manager.start_background_normalization(
            callback=lambda changed: self.after(0, self._on_normalization_done, changed)
        )
        
        # 7.6-DEPLOY-1: Check for updates in background (after 10 seconds)
        self.after(10000, self._check_for_updates)
        
        logging.info(f"Ứng dụng {APP_VERSION} đã khởi động thành công.")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_normalization_done(self, changed: bool):
        """Callback khi owner normalization hoàn thành."""
        self.status_var.set(self.get_translation("status_ready"))
        if changed:
            logging.info("Owner normalization hoàn thành, làm mới dropdown chủ hàng.")
            if hasattr(self, 'stock_tab'):
                self.stock_tab.update_owner_filter_options()
            if hasattr(self, 'inbound_tab'):
                self.inbound_tab.update_dropdowns()
            if hasattr(self, 'outbound_tab'):
                self.outbound_tab.update_dropdowns()

    def get_translation(self, key):
        lang = self.current_lang.get()
        return translations.get(key, {}).get(lang, key)

    def _build_ui(self):
        """Xây dựng lại toàn bộ giao diện người dùng."""
        for widget in self.winfo_children():
            widget.destroy()

        self.title(f"{self.get_translation('app_title')} - {APP_VERSION}")
        self.geometry("1200x800")
        self.minsize(1024, 768)
        
        if not hasattr(self, '_initial_build_done'):
             self.center_window()
             self._initial_build_done = True

        self._build_menu()
        # ==========================================================

        self._build_tabs()
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent")
        
        # === PHASE 2.6: Build notification panel ===
        self._build_notification_panel()
                
        self._build_status_bar()
        self.after(100, self.inbound_tab.update_dropdowns)
        # ==========================================================
        
        #self.on_data_changed()

        
    def _build_menu(self):
        self.main_menu = Menu(self)
        menu_font = (FONT_FAMILY, FONT_SIZE_SMALL)
        self.file_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.tools_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.settings_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.user_menu = Menu(self.main_menu, tearoff=0, font=menu_font)  # Phase 1C: User menu
        self.lang_menu = Menu(self.settings_menu, tearoff=0, font=menu_font)
        self.theme_menu = Menu(self.settings_menu, tearoff=0, font=menu_font)
        self.configure(menu=self.main_menu)
        self._update_menu_text()

    def _update_menu_text(self):
        self.main_menu.delete(0, "end")
        self.file_menu.delete(0, "end")
        self.tools_menu.delete(0, "end")
        self.settings_menu.delete(0, "end")
        self.user_menu.delete(0, "end")  # Phase 1C
        self.lang_menu.delete(0, "end")
        self.theme_menu.delete(0, "end")

        self.main_menu.add_cascade(label=self.get_translation("menu_file"), menu=self.file_menu)
        self.main_menu.add_cascade(label=self.get_translation("menu_tools"), menu=self.tools_menu)
        self.main_menu.add_cascade(label=self.get_translation("menu_settings"), menu=self.settings_menu)
        
        # Phase 1C: User menu
        current_user = self.auth_manager.get_current_user()
        user_menu_label = f"👤 {current_user['username']}" if current_user else "👤 Tài khoản"
        self.main_menu.add_cascade(label=user_menu_label, menu=self.user_menu)

        self.file_menu.add_command(label=self.get_translation("menu_exit"), command=self.on_close, accelerator="Alt+F4")
        self.tools_menu.add_command(label=self.get_translation("menu_create_vouchers"), command=self.open_voucher_creation_tool)
        # === CẬP NHẬT: Sử dụng key dịch thuật ===
        self.tools_menu.add_command(label=self.get_translation("menu_archive_explorer"), command=self.open_archive_explorer)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label=self.get_translation("menu_deleted_vehicles"), command=self.open_deleted_vehicles)
        self.tools_menu.add_separator()
        # === PHASE 3: PDF Report & Print Templates ===
        self.tools_menu.add_command(label=self.get_translation("menu_pdf_report"), command=self._open_pdf_report)
        self.tools_menu.add_command(label=self.get_translation("menu_print_templates"), command=self._open_print_templates)
        # ===================

        # Phase 1C: User menu items
        self.user_menu.add_command(label=self.get_translation("menu_change_password"), command=self._open_change_password)
        if self.auth_manager.has_permission(Permission.USER_VIEW):
            self.user_menu.add_command(label=self.get_translation("menu_user_management"), command=self._open_user_management)
        if self.auth_manager.has_permission(Permission.AUDIT_VIEW):
            self.user_menu.add_command(label=self.get_translation("menu_login_history"), command=self._open_login_history)
        self.user_menu.add_separator()
        self.user_menu.add_command(label=self.get_translation("menu_logout"), command=self._logout, accelerator="Ctrl+Q")


        self.settings_menu.add_cascade(label=self.get_translation("menu_language"), menu=self.lang_menu)
        self.lang_menu.add_radiobutton(label=self.get_translation("lang_vi"), variable=self.current_lang, value="vi", command=self.change_language)
        self.lang_menu.add_radiobutton(label=self.get_translation("lang_en"), variable=self.current_lang, value="en", command=self.change_language)

        self.settings_menu.add_cascade(label=self.get_translation("menu_theme"), menu=self.theme_menu)
        self.theme_menu.add_radiobutton(label=self.get_translation("theme_light"), variable=self.current_theme, value="Light", command=self.change_theme)
        self.theme_menu.add_radiobutton(label=self.get_translation("theme_dark"), variable=self.current_theme, value="Dark", command=self.change_theme)
        self.theme_menu.add_radiobutton(label=self.get_translation("theme_system"), variable=self.current_theme, value="System", command=self.change_theme)
        
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.get_translation("menu_manage_drivers"), command=self.manage_drivers)
        self.settings_menu.add_command(label=self.get_translation("menu_manage_transports"), command=self.manage_transport_vehicles)
        self.settings_menu.add_command(label=self.get_translation("menu_manage_layout"), command=self.manage_layout)
        self.settings_menu.add_command(label=self.get_translation("menu_select_voucher_template"), command=self.select_voucher_template)
        self.settings_menu.add_separator()
        # Phase 2.6: Notification settings
        self.settings_menu.add_command(label=self.get_translation("menu_notification_settings"), command=self._open_notification_settings)
        self.settings_menu.add_separator()
        # === PHASE 3: Config & Onboarding ===
        self.settings_menu.add_command(label=self.get_translation("menu_config"), command=self._open_config_dialog)
        self.settings_menu.add_command(label=self.get_translation("menu_onboarding"), command=self._open_onboarding)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.get_translation("menu_archive"), command=self.prompt_archive_data)

    def _build_tabs(self):
        # Frame chứa tabs và nút Web Dashboard
        self.tabs_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs_container.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        self.tabs = ctk.CTkTabview(self.tabs_container, command=self.on_tab_change)
        self.tabs.pack(side="left", fill="both", expand=True)

        tab_names = ["tab_inbound", "tab_dispatch", "tab_outbound", "tab_stock", "tab_search", "tab_yard_map", "tab_dashboard", "tab_log"]
        self.tab_map = {name: self.tabs.add(self.get_translation(name)) for name in tab_names}
        
        # === NÚT WEB DASHBOARD - Đặt bên phải, gần tab Nhật ký ===
        self._build_web_dashboard_button()

        # === SỬA LỖI: Khởi tạo tất cả các đối tượng tab trước ===
        self.inbound_tab = InboundTab(self.tab_map["tab_inbound"], self)
        self.dispatch_tab = DispatchTab(self.tab_map["tab_dispatch"], self)
        self.outbound_tab = OutboundTab(self.tab_map["tab_outbound"], self)
        self.stock_tab = StockTab(self.tab_map["tab_stock"], self)
        self.search_tab = SearchTab(self.tab_map["tab_search"], self)
        self.yard_map_tab = YardMapTab(self.tab_map["tab_yard_map"], self)
        self.dashboard_tab = DashboardTab(self.tab_map["tab_dashboard"], self)
        self.log_tab = LogTab(self.tab_map["tab_log"], self)
        
        # Sau khi tất cả các tab đã được tạo, mới gọi update_language
        self.update_all_tabs_language()
        # =====================================================

    def update_all_tabs_language(self):
        """Cập nhật ngôn ngữ cho tất cả các tab."""
        for tab in [self.inbound_tab, self.dispatch_tab, self.outbound_tab, self.stock_tab, self.search_tab, self.yard_map_tab, self.dashboard_tab]:
            if hasattr(tab, 'update_language'):
                tab.update_language()

    def _build_web_dashboard_button(self):
        """Xây dựng nút Web Dashboard bên phải tab bar."""
        # Frame chứa nút, đặt ở góc trên bên phải
        self.web_btn_frame = ctk.CTkFrame(self.tabs_container, fg_color="transparent")
        self.web_btn_frame.pack(side="right", anchor="n", padx=(5, 0), pady=(5, 0))
        
        # Nút Web Dashboard chính
        self.web_dashboard_btn = ctk.CTkButton(
            self.web_btn_frame,
            text="🌐 Web Dashboard",
            command=self._launch_web_dashboard,
            width=140,
            height=32,
            fg_color="#2980b9",
            hover_color="#3498db",
            font=self.font_normal
        )
        self.web_dashboard_btn.pack(pady=(0, 5))
        
        # Nút Stop (ẩn mặc định)
        self.web_stop_btn = ctk.CTkButton(
            self.web_btn_frame,
            text="⏹ Dừng",
            command=self._stop_web_dashboard,
            width=140,
            height=28,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            font=self.font_small
        )
        # Không pack ngay, chỉ hiện khi dashboard đang chạy
        
    def _update_web_dashboard_buttons(self):
        """Cập nhật trạng thái nút Web Dashboard — delegate to WebDashboardManager."""
        if hasattr(self, '_web_dashboard'):
            self._web_dashboard._update_buttons()

    def _build_status_bar(self):
        """Xây dựng thanh trạng thái ở dưới cùng cửa sổ."""
        status_bar_frame = ctk.CTkFrame(self, height=30)
        status_bar_frame.pack(side="bottom", fill="x", padx=0, pady=0) # pack vào self
        self.status_var = ctk.StringVar(value=self.get_translation("status_ready"))
        self.status_label = ctk.CTkLabel(status_bar_frame, textvariable=self.status_var, anchor="w", font=self.font_normal)
        self.status_label.pack(side="left", fill="x", expand=True, padx=10)
        
        # Phase 1C: User info display (without logout button)
        current_user = self.auth_manager.get_current_user()
        if current_user:
            # Use translation for role display
            role_key = {
                'admin': 'role_admin',
                'operator': 'role_operator', 
                'viewer': 'role_viewer'
            }.get(current_user['role'], current_user['role'])
            role_display = self.get_translation(role_key)
            user_text = f"👤 {current_user['username']} ({role_display})"
            self.user_label = ctk.CTkLabel(
                status_bar_frame,
                text=user_text,
                anchor="e",
                font=self.font_normal,
                text_color="#3498db"
            )
            self.user_label.pack(side="right", padx=(0, 10))
        
        self.author_label = ctk.CTkLabel(status_bar_frame, text=self.get_translation("author_credit"), anchor="e", font=self.font_normal)
        self.author_label.pack(side="right", padx=10)

    def change_language(self, *args):
        """Xử lý sự kiện thay đổi ngôn ngữ."""
        new_lang = self.current_lang.get()
        if self.config.get("Settings", "language") != new_lang:
            self.config.set("Settings", "language", new_lang)
            logging.info(f"Ngôn ngữ đã được đổi thành '{new_lang}'. Đang làm mới giao diện.")
            self._build_ui()

    def change_theme(self, *args):
        """Xử lý sự kiện thay đổi theme (Sáng/Tối)."""
        theme = self.current_theme.get()
        ctk.set_appearance_mode(theme)
        self.config.set("Settings", "theme", theme)

    # Phase 1C: Auth methods
    def _logout(self):
        """Đăng xuất khỏi ứng dụng."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
            self.auth_manager.logout()
            logging.info("Người dùng đã đăng xuất")
            
            # Restart app with login
            self.withdraw()
            self._open_login()
    
    def _open_change_password(self):
        """Mở dialog đổi mật khẩu."""
        dialog = ChangePasswordDialog(self)
    
    def _open_user_management(self):
        """Mở dialog quản lý người dùng (Admin only)."""
        if not self.auth_manager.has_permission(Permission.USER_VIEW):
            messagebox.showerror("Lỗi", "Bạn không có quyền truy cập chức năng này!")
            return
        dialog = UserManagementDialog(self)
    
    def _open_login_history(self):
        """Mở dialog xem lịch sử đăng nhập."""
        dialog = LoginHistoryDialog(self)

    def on_tab_change(self):
        """Xử lý sự kiện khi người dùng chuyển tab (Lazy Loading)."""
        # Refresh session khi user tương tác (CQ-5.2)
        if hasattr(self, 'auth_manager'):
            self.auth_manager.refresh_session()
        
        selected_tab_name = self.tabs.get()
        
        # Chỉ tải dữ liệu khi tab được chọn
        if selected_tab_name == self.get_translation("tab_stock"):
            self.stock_tab.refresh_all()
        elif selected_tab_name == self.get_translation("tab_dispatch"):
            self.dispatch_tab.update_dropdowns()
            self.dispatch_tab.load_open_dispatch()
        elif selected_tab_name == self.get_translation("tab_inbound"):
            self.inbound_tab.update_dropdowns()
        elif selected_tab_name == self.get_translation("tab_outbound"):
            self.outbound_tab.update_dropdowns()
        elif selected_tab_name == self.get_translation("tab_dashboard"):
            # Có thể thêm logic tự động cập nhật dashboard ở đây nếu muốn
            pass

    def on_data_changed(self):
        """Hàm điều phối làm mới giao diện khi có thay đổi dữ liệu.
        
        Chỉ refresh tab đang active để tránh lãng phí tài nguyên.
        Các tab khác sẽ được lazy-load khi người dùng chuyển sang.
        """
        logging.info("Phát hiện thay đổi dữ liệu, đang làm mới tab hiện tại.")
        # Refresh session khi user có hoạt động (CQ-5.2)
        if hasattr(self, 'auth_manager'):
            self.auth_manager.refresh_session()
        
        # Luôn cập nhật dropdowns cho inbound/outbound/dispatch (nhẹ, không query nhiều)
        if hasattr(self, 'inbound_tab'):
            self.inbound_tab.update_dropdowns()
        if hasattr(self, 'outbound_tab'):
            self.outbound_tab.update_dropdowns()
        if hasattr(self, 'dispatch_tab'):
            self.dispatch_tab.update_dropdowns()
        
        # Chỉ refresh stock_tab nếu đang active (tránh query nặng khi không cần)
        if hasattr(self, 'tabs') and hasattr(self, 'stock_tab'):
            try:
                active_tab = self.tabs.get()
                if active_tab == self.get_translation("tab_stock"):
                    self.stock_tab.refresh_all()
            except Exception:
                # Fallback: refresh nếu không xác định được tab active
                self.stock_tab.refresh_all()

    def center_window(self):
        """Căn giữa cửa sổ ứng dụng khi khởi động."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        y_pos = y - 40 if y > 40 else 0
        self.geometry(f'{width}x{height}+{x}+{y_pos}')

    # === PHASE 2.6: Notification System ===
    def _build_notification_panel(self):
        """Tạo panel hiển thị thông báo ở góc màn hình."""
        # Create notification panel (positioned at bottom-right)
        self.notification_panel = NotificationPanel(
            self,
            notification_service=self.notification_service,
            position="bottom-right",
        )
        # Only show panel if there are notifications
        if self.notification_panel.service.get_unread():
            self.notification_panel.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-40)
    
    def _check_for_updates(self):
        """Kiểm tra phiên bản mới từ GitHub (7.6-DEPLOY-1)."""
        def on_update_result(info):
            if info and info.get("is_newer"):
                new_version = info.get("version", "")
                url = info.get("url", "")
                msg = f"🆕 Phiên bản mới {new_version} đã có!\nTải về: {url}"
                # Show as notification (non-blocking)
                self.after(0, lambda: self.show_toast(msg))
                logging.info(f"Update available: {new_version} — {url}")

        check_for_updates(APP_VERSION, callback=on_update_result)

    def _setup_notification_checks(self):
        """Thiết lập kiểm tra thông báo định kỳ."""
        # Run initial checks after a short delay
        self.after(5000, self._run_notification_checks)
        
        # Schedule periodic checks (every 30 minutes)
        self._notification_check_job = self.after(30 * 60 * 1000, self._periodic_notification_check)
    
    def _run_notification_checks(self):
        """Chạy các kiểm tra thông báo."""
        try:
            self.notification_service.run_all_checks(
                vehicle_manager=self.vehicle_manager,
                location_manager=self.location_manager
            )
        except Exception as e:
            logging.error(f"Error running notification checks: {e}")
    
    def _periodic_notification_check(self):
        """Kiểm tra thông báo định kỳ."""
        self._run_notification_checks()
        # Reschedule
        self._notification_check_job = self.after(30 * 60 * 1000, self._periodic_notification_check)
    
    def _open_notification_settings(self):
        """Mở dialog cài đặt thông báo."""
        NotificationSettingsDialog(self, self.notification_service)
    # === END PHASE 2.6 ===

    # === PHASE 2.4: Keyboard Shortcuts ===
    def _setup_keyboard_shortcuts(self):
        """Thiết lập các phím tắt toàn cục."""
        # F5 - Refresh current view
        self.bind("<F5>", self._shortcut_refresh)
        
        # Ctrl+N - Go to Inbound tab (new vehicle)
        self.bind("<Control-n>", self._shortcut_new_vehicle)
        self.bind("<Control-N>", self._shortcut_new_vehicle)
        
        # Ctrl+F - Go to Search tab
        self.bind("<Control-f>", self._shortcut_search)
        self.bind("<Control-F>", self._shortcut_search)
        
        # Ctrl+E - Export from current tab
        self.bind("<Control-e>", self._shortcut_export)
        self.bind("<Control-E>", self._shortcut_export)
        
        # Ctrl+D - Go to Dispatch tab
        self.bind("<Control-d>", self._shortcut_dispatch)
        self.bind("<Control-D>", self._shortcut_dispatch)
        
        # Ctrl+M - Go to Yard Map tab
        self.bind("<Control-m>", self._shortcut_yard_map)
        self.bind("<Control-M>", self._shortcut_yard_map)
        
        # Ctrl+B - Go to Dashboard/Reports tab
        self.bind("<Control-b>", self._shortcut_dashboard)
        self.bind("<Control-B>", self._shortcut_dashboard)
        
        # Ctrl+O - Go to Outbound (single) tab
        self.bind("<Control-o>", self._shortcut_outbound)
        self.bind("<Control-O>", self._shortcut_outbound)
        
        # Ctrl+T - Go to Stock tab
        self.bind("<Control-t>", self._shortcut_stock)
        self.bind("<Control-T>", self._shortcut_stock)
        
        # Escape - Clear selection/reset filters
        self.bind("<Escape>", self._shortcut_escape)
        
        # Ctrl+Q - Logout
        self.bind("<Control-q>", self._shortcut_logout)
        self.bind("<Control-Q>", self._shortcut_logout)
        
        # F1 - Help/show shortcuts
        self.bind("<F1>", self._shortcut_help)
        
        logging.info("Keyboard shortcuts initialized")

    def _shortcut_refresh(self, event=None):
        """F5 - Làm mới tab hiện tại."""
        selected_tab = self.tabs.get()
        
        if selected_tab == self.get_translation("tab_stock"):
            self.stock_tab.refresh_all()
        elif selected_tab == self.get_translation("tab_inbound"):
            self.inbound_tab.update_dropdowns()
        elif selected_tab == self.get_translation("tab_dispatch"):
            self.dispatch_tab.update_dropdowns()
            self.dispatch_tab.load_open_dispatch()
        elif selected_tab == self.get_translation("tab_outbound"):
            self.outbound_tab.update_dropdowns()
        elif selected_tab == self.get_translation("tab_search"):
            if hasattr(self.search_tab, 'perform_search'):
                self.search_tab.perform_search()
        elif selected_tab == self.get_translation("tab_yard_map"):
            if hasattr(self.yard_map_tab, 'refresh_data'):
                self.yard_map_tab.refresh_data()
        elif selected_tab == self.get_translation("tab_dashboard"):
            if hasattr(self.dashboard_tab, 'update_dashboard'):
                self.dashboard_tab.update_dashboard()
        
        self.show_toast(self.get_translation("shortcut_refreshed"))
        return "break"  # Prevent default handling

    def _shortcut_new_vehicle(self, event=None):
        """Ctrl+N - Chuyển đến tab Nhập bãi."""
        self.tabs.set(self.get_translation("tab_inbound"))
        self.inbound_tab.update_dropdowns()
        # Focus vào trường VIN
        if hasattr(self.inbound_tab, 'entry_vin'):
            self.after(100, lambda: self.inbound_tab.entry_vin.focus_set())
        return "break"

    def _shortcut_search(self, event=None):
        """Ctrl+F - Chuyển đến tab Tra cứu."""
        self.tabs.set(self.get_translation("tab_search"))
        # Focus vào trường tìm kiếm
        if hasattr(self.search_tab, 'search_entry'):
            self.after(100, lambda: self.search_tab.search_entry.focus_set())
        return "break"

    def _shortcut_export(self, event=None):
        """Ctrl+E - Export từ tab hiện tại."""
        selected_tab = self.tabs.get()
        
        if selected_tab == self.get_translation("tab_stock"):
            if hasattr(self.stock_tab, 'export_stock'):
                self.stock_tab.export_stock()
        elif selected_tab == self.get_translation("tab_dashboard"):
            if hasattr(self.dashboard_tab, 'export_pdf'):
                self.dashboard_tab.export_pdf()
        else:
            self.show_toast(self.get_translation("shortcut_export_not_available"))
        return "break"

    def _shortcut_dispatch(self, event=None):
        """Ctrl+D - Chuyển đến tab Xuất bãi (nhiều xe)."""
        self.tabs.set(self.get_translation("tab_dispatch"))
        self.dispatch_tab.update_dropdowns()
        return "break"

    def _shortcut_yard_map(self, event=None):
        """Ctrl+M - Chuyển đến tab Bản đồ bãi."""
        self.tabs.set(self.get_translation("tab_yard_map"))
        if hasattr(self.yard_map_tab, 'refresh_data'):
            self.yard_map_tab.refresh_data()
        return "break"

    def _shortcut_dashboard(self, event=None):
        """Ctrl+B - Chuyển đến tab Báo cáo."""
        self.tabs.set(self.get_translation("tab_dashboard"))
        return "break"

    def _shortcut_escape(self, event=None):
        """Escape - Xóa selection hoặc reset filters."""
        selected_tab = self.tabs.get()
        
        if selected_tab == self.get_translation("tab_stock"):
            if hasattr(self.stock_tab, 'selected_vins'):
                self.stock_tab.selected_vins.clear()
                self.stock_tab.update_stock_list()
                self.stock_tab._update_selected_count_label()
        elif selected_tab == self.get_translation("tab_search"):
            if hasattr(self.search_tab, 'search_entry'):
                self.search_tab.search_entry.delete(0, "end")
        
        return "break"

    def _shortcut_logout(self, event=None):
        """Ctrl+Q - Đăng xuất."""
        self._logout()
        return "break"
    
    def _shortcut_outbound(self, event=None):
        """Ctrl+O - Chuyển đến tab Xuất lẻ."""
        self.tabs.set(self.get_translation("tab_outbound"))
        self.outbound_tab.update_dropdowns()
        if hasattr(self.outbound_tab, 'scan_entry'):
            self.after(100, lambda: self.outbound_tab.scan_entry.focus_set())
        return "break"
    
    def _shortcut_stock(self, event=None):
        """Ctrl+T - Chuyển đến tab Tồn bãi."""
        self.tabs.set(self.get_translation("tab_stock"))
        return "break"
    
    def _shortcut_help(self, event=None):
        """F1 - Hiển thị danh sách phím tắt."""
        shortcuts_text = self.get_translation("help_shortcuts_text")
        from tkinter import messagebox
        messagebox.showinfo(
            self.get_translation("help_shortcuts_title"),
            shortcuts_text,
            parent=self
        )
        return "break"
    # === END PHASE 2.4 ===

    def show_toast(self, message):
        """Hiển thị một thông báo toast ngắn."""
        Toast(self, message)

    # === HÀM BỊ THIẾU - BỔ SUNG LẠI ===
    def log_to_widget(self, widget, message, tag=None):
        """Ghi một thông điệp log vào một widget Textbox một cách an toàn."""
        try:
            if widget.winfo_exists():
                widget.configure(state="normal")
                timestamp = datetime.now().strftime("[%H:%M:%S]")
                widget.insert("end", f"{timestamp} {message}\n", tag)
                widget.see("end")
                widget.configure(state="disabled")
        except Exception:
            pass # Bỏ qua nếu widget đã bị hủy
    # ===================================
    def manage_drivers(self):
        dialog = ManagementDialog(self, self.get_translation("dialog_manage_drivers_title"), ENTITY_TYPE_DRIVER)
        self.on_data_changed()

    def manage_transport_vehicles(self):
        dialog = ManagementDialog(self, self.get_translation("dialog_manage_transports_title"), ENTITY_TYPE_TRANSPORT)
        self.on_data_changed()

    def manage_layout(self):
        dialog = LayoutManagementDialog(self, self.location_manager)
        self.on_data_changed()

    def select_voucher_template(self):
        path = filedialog.askopenfilename(title="Chọn file Mẫu Phiếu Vận Chuyển", filetypes=[("Word Documents", "*.docx")])
        if path:
            self.config.set("Paths", "voucher_template_path", path)
            save_config(self.config)
            self.show_toast(f"Đã cập nhật mẫu phiếu: {os.path.basename(path)}")
            logging.info(f"Người dùng đã cập nhật mẫu phiếu vận chuyển thành: {path}")

    def open_voucher_creation_tool(self):
        default_filename = f"PHIEU_VC_{datetime.now().strftime('%d%m%Y_%H%M')}.docx"
        dialog = VoucherCreationDialog(self, default_output_filename=default_filename)

    # === HÀM BỊ THIẾU - BỔ SUNG LẠI ===
    def open_archive_explorer(self):
        """Mở công cụ tra cứu dữ liệu đã lưu trữ."""
        dialog = ArchiveExplorerDialog(self)
    # ===================================

    def open_deleted_vehicles(self):
        """Mở công cụ quản lý xe đã xóa."""
        dialog = DeletedVehiclesDialog(
            self,
            vehicle_manager=self.vehicle_manager,
            on_restore_callback=self.on_data_changed
        )

    # === PHASE 3: New Dialog Methods ===
    def _open_pdf_report(self):
        """Mở dialog tạo báo cáo PDF."""
        from ui.pdf_report_dialog import PDFReportDialog
        PDFReportDialog(self)
    
    def _open_print_templates(self):
        """Mở dialog quản lý mẫu in."""
        from ui.print_templates_dialog import PrintTemplatesDialog
        PrintTemplatesDialog(self)
    
    def _open_config_dialog(self):
        """Mở dialog quản lý cấu hình."""
        from ui.config_dialog import ConfigDialog
        ConfigDialog(self)
    
    def _open_onboarding(self):
        """Mở hướng dẫn sử dụng."""
        from ui.onboarding_dialog import OnboardingDialog
        OnboardingDialog(self)
    # === END PHASE 3 ===

    # === WEB DASHBOARD (FLASK) — Delegated to WebDashboardManager (7.1-ARCH-1) ===
    def _launch_web_dashboard(self):
        """Khởi động Web Dashboard — delegate to WebDashboardManager."""
        if hasattr(self, '_web_dashboard'):
            self._web_dashboard.launch()

    def _stop_web_dashboard(self):
        """Dừng Web Dashboard — delegate to WebDashboardManager."""
        if hasattr(self, '_web_dashboard'):
            self._web_dashboard.stop()
    # === END WEB DASHBOARD ===

    def prompt_for_history_export(self):
        dialog = DateRangeDialog(self, title=self.get_translation("menu_export_history"))
        if dialog.result:
            start_date, end_date = dialog.result
            self.stock_tab.export_history(start_date, end_date)

    def prompt_archive_data(self):
        dialog = DateRangeDialog(self, title=self.get_translation("menu_archive"))
        if dialog.result:
            start_date, end_date = dialog.result
            
            confirm_msg = self.get_translation("confirm_archive_msg").format(
                start=start_date.strftime('%d/%m/%Y'), 
                end=end_date.strftime('%d/%m/%Y')
            )
            if messagebox.askyesno(self.get_translation("confirm_archive_title"), confirm_msg, icon='warning'):
                self.status_var.set(self.get_translation("status_archiving"))
                self.update_idletasks()
                
                result = self.vehicle_manager.archive_shipped_vehicles(start_date, end_date)
                
                if result["success"]:
                    messagebox.showinfo(self.get_translation("dialog_archive_complete_title"), result["message"])
                else:
                    messagebox.showerror(self.get_translation("dialog_error_title"), result["message"])
                
                self.status_var.set(self.get_translation("status_ready"))
                self.on_data_changed()

    def on_close(self):
        """Xử lý sự kiện đóng ứng dụng một cách an toàn."""
        if messagebox.askokcancel(self.get_translation("confirm_exit_title"), self.get_translation("confirm_exit_msg")):
            # Stop Web Dashboard if running (delegate to WebDashboardManager)
            if hasattr(self, '_web_dashboard') and self._web_dashboard.is_running:
                self._web_dashboard.stop()
            
            save_config(self.config)
            BaseManager.close_connection()
            self.destroy()

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
    # Đảm bảo đóng kết nối CSDL khi ứng dụng kết thúc
    BaseManager.close_connection()
    # logging.info("Ứng dụng đã đóng.")