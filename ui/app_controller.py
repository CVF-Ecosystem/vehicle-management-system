# ui/app_controller.py
"""
InventoryApp — main application window.

Được tách từ main.py (CQ-05). main.py chỉ còn là entry point.
Tab management được delegate sang TabManager.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from tkinter import Menu, filedialog, messagebox

import customtkinter as ctk

from utils import load_config, save_config
from database.base_manager import BaseManager
from database.vehicle_manager import VehicleManager
from database.entity_manager import EntityManager
from database.dispatch_manager import DispatchManager
from database.location_manager import LocationManager
from layout_manager import LayoutManager
from api_client import ApiClient
from translations import translations
from config import (
    APP_NAME, APP_VERSION,
    ENTITY_TYPE_DRIVER, ENTITY_TYPE_TRANSPORT,
    FONT_FAMILY, FONT_SIZE_LARGE, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
)

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
from ui.archive_explorer_dialog import ArchiveExplorerDialog
from ui.deleted_vehicles_dialog import DeletedVehiclesDialog
from ui.tab_manager import TabManager
from ui.web_dashboard_manager import WebDashboardManager

from auth.auth_manager import AuthManager
from auth.permissions import Permission, get_role_display_name
from ui.login_dialog import LoginDialog, ChangePasswordDialog
from ui.user_management_dialog import UserManagementDialog, LoginHistoryDialog

from core.notification_service import NotificationService
from ui.notification_panel import NotificationPanel, NotificationSettingsDialog
from core.update_checker import check_for_updates


class InventoryApp(ctk.CTk):
    """Cửa sổ chính của ứng dụng Quản lý Xe."""

    def __init__(self) -> None:
        super().__init__()
        self.withdraw()  # hide immediately so the empty window never shows as "Not Responding"

        self.config = load_config()
        self.current_lang = ctk.StringVar(
            value=self.config.get("Settings", "language", fallback="vi")
        )
        self.current_theme = ctk.StringVar(
            value=self.config.get("Settings", "theme", fallback="System")
        )
        ctk.set_appearance_mode(self.current_theme.get())

        # --- Managers ---
        self.vehicle_manager = VehicleManager()
        self.entity_manager = EntityManager()
        self.dispatch_manager = DispatchManager()
        self.location_manager = LocationManager()
        self.layout_manager = LayoutManager(self.location_manager)
        self.api_client = ApiClient(
            self.vehicle_manager, self.entity_manager, self.dispatch_manager
        )

        # --- Fonts ---
        self.font_normal = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        self.font_bold = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL, weight="bold")
        self.font_large_bold = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_LARGE, weight="bold")
        self.font_small = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL)
        self.font_small_italic = ctk.CTkFont(
            family=FONT_FAMILY, size=FONT_SIZE_SMALL, slant="italic"
        )

        # --- Auth & Services ---
        self.auth_manager = AuthManager.get_instance()
        self.notification_service = NotificationService.get_instance()

        # --- Tab Manager (delegate) ---
        self.tab_manager = TabManager(self)

        self._show_login_dialog()

    # ------------------------------------------------------------------ Auth --

    def _show_login_dialog(self) -> None:
        self.after(100, self._open_login)

    def _open_login(self) -> None:
        LoginDialog(self, on_success_callback=self._on_login_success).wait_window()

    def _on_login_success(self, user: dict) -> None:
        logging.info(f"Đăng nhập thành công: {user['username']} ({user['role']})")
        self.deiconify()
        self.update()          # render window frame before blocking tab build
        self._build_ui()
        self._setup_keyboard_shortcuts()
        self._setup_notification_checks()
        self._web_dashboard = WebDashboardManager(self)

        # PERF-02: delay 3s để UI tải xong trước khi start background thread
        self.after(3000, self._start_normalization)
        self.after(10000, self._check_for_updates)
        logging.info(f"Ứng dụng {APP_VERSION} đã khởi động thành công.")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _start_normalization(self) -> None:
        """Khởi động background normalization sau khi UI đã tải xong."""
        self.status_var.set("Đang chuẩn hóa dữ liệu chủ hàng...")
        self.vehicle_manager.start_background_normalization(
            callback=lambda changed: self.after(0, self._on_normalization_done, changed)
        )

    def _on_normalization_done(self, changed: bool) -> None:
        # Gọi trên main thread — an toàn để dùng self.conn
        self.vehicle_manager._refresh_known_owners()
        self.status_var.set(self.get_translation("status_ready"))
        if changed:
            logging.info("Owner normalization hoàn thành, làm mới dropdown chủ hàng.")
            for tab in (self.stock_tab, self.inbound_tab, self.outbound_tab):
                if hasattr(tab, "update_owner_filter_options"):
                    tab.update_owner_filter_options()
                elif hasattr(tab, "update_dropdowns"):
                    tab.update_dropdowns()

    # ----------------------------------------------------------------- i18n --

    def get_translation(self, key: str) -> str:
        lang = self.current_lang.get()
        return translations.get(key, {}).get(lang, key)

    # ------------------------------------------------------------------ UI ---

    def _build_ui(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

        self.title(f"{self.get_translation('app_title')} - {APP_VERSION}")
        self.geometry("1200x800")
        self.minsize(1024, 768)

        if not hasattr(self, "_initial_build_done"):
            self.center_window()
            self._initial_build_done = True

        self._build_menu()
        self._build_tabs()
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent")
        self._build_notification_panel()
        self._build_status_bar()
        self.after(100, self.inbound_tab.update_dropdowns)

    def _build_menu(self) -> None:
        self.main_menu = Menu(self)
        menu_font = (FONT_FAMILY, FONT_SIZE_SMALL)
        self.file_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.tools_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.settings_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.user_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.lang_menu = Menu(self.settings_menu, tearoff=0, font=menu_font)
        self.theme_menu = Menu(self.settings_menu, tearoff=0, font=menu_font)
        self.configure(menu=self.main_menu)
        self._update_menu_text()

    def _update_menu_text(self) -> None:
        for m in (
            self.main_menu, self.file_menu, self.tools_menu,
            self.settings_menu, self.user_menu, self.lang_menu, self.theme_menu,
        ):
            m.delete(0, "end")

        self.main_menu.add_cascade(label=self.get_translation("menu_file"), menu=self.file_menu)
        self.main_menu.add_cascade(label=self.get_translation("menu_tools"), menu=self.tools_menu)
        self.main_menu.add_cascade(label=self.get_translation("menu_settings"), menu=self.settings_menu)

        current_user = self.auth_manager.get_current_user()
        user_menu_label = f"👤 {current_user['username']}" if current_user else "👤 Tài khoản"
        self.main_menu.add_cascade(label=user_menu_label, menu=self.user_menu)

        self.file_menu.add_command(
            label=self.get_translation("menu_exit"), command=self.on_close, accelerator="Alt+F4"
        )
        self.tools_menu.add_command(
            label=self.get_translation("menu_create_vouchers"), command=self.open_voucher_creation_tool
        )
        self.tools_menu.add_command(
            label=self.get_translation("menu_archive_explorer"), command=self.open_archive_explorer
        )
        self.tools_menu.add_separator()
        self.tools_menu.add_command(
            label=self.get_translation("menu_deleted_vehicles"), command=self.open_deleted_vehicles
        )
        self.tools_menu.add_separator()
        self.tools_menu.add_command(
            label=self.get_translation("menu_pdf_report"), command=self._open_pdf_report
        )
        self.tools_menu.add_command(
            label=self.get_translation("menu_print_templates"), command=self._open_print_templates
        )

        self.user_menu.add_command(
            label=self.get_translation("menu_change_password"), command=self._open_change_password
        )
        if self.auth_manager.has_permission(Permission.USER_VIEW):
            self.user_menu.add_command(
                label=self.get_translation("menu_user_management"), command=self._open_user_management
            )
        if self.auth_manager.has_permission(Permission.AUDIT_VIEW):
            self.user_menu.add_command(
                label=self.get_translation("menu_login_history"), command=self._open_login_history
            )
        self.user_menu.add_separator()
        self.user_menu.add_command(
            label=self.get_translation("menu_logout"), command=self._logout, accelerator="Ctrl+Q"
        )

        self.settings_menu.add_cascade(
            label=self.get_translation("menu_language"), menu=self.lang_menu
        )
        self.lang_menu.add_radiobutton(
            label=self.get_translation("lang_vi"), variable=self.current_lang,
            value="vi", command=self.change_language,
        )
        self.lang_menu.add_radiobutton(
            label=self.get_translation("lang_en"), variable=self.current_lang,
            value="en", command=self.change_language,
        )
        self.settings_menu.add_cascade(
            label=self.get_translation("menu_theme"), menu=self.theme_menu
        )
        self.theme_menu.add_radiobutton(
            label=self.get_translation("theme_light"), variable=self.current_theme,
            value="Light", command=self.change_theme,
        )
        self.theme_menu.add_radiobutton(
            label=self.get_translation("theme_dark"), variable=self.current_theme,
            value="Dark", command=self.change_theme,
        )
        self.theme_menu.add_radiobutton(
            label=self.get_translation("theme_system"), variable=self.current_theme,
            value="System", command=self.change_theme,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label=self.get_translation("menu_manage_drivers"), command=self.manage_drivers
        )
        self.settings_menu.add_command(
            label=self.get_translation("menu_manage_transports"), command=self.manage_transport_vehicles
        )
        self.settings_menu.add_command(
            label=self.get_translation("menu_manage_layout"), command=self.manage_layout
        )
        self.settings_menu.add_command(
            label=self.get_translation("menu_select_voucher_template"),
            command=self.select_voucher_template,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label=self.get_translation("menu_notification_settings"),
            command=self._open_notification_settings,
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label=self.get_translation("menu_config"), command=self._open_config_dialog
        )
        self.settings_menu.add_command(
            label=self.get_translation("menu_onboarding"), command=self._open_onboarding
        )
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label=self.get_translation("menu_archive"), command=self.prompt_archive_data
        )

    def _build_tabs(self) -> None:
        self.tabs_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs_container.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.tabs = ctk.CTkTabview(self.tabs_container, command=self.on_tab_change)
        self.tabs.pack(side="left", fill="both", expand=True)

        tab_keys = [
            "tab_inbound", "tab_dispatch", "tab_outbound", "tab_stock",
            "tab_search", "tab_yard_map", "tab_dashboard", "tab_log",
        ]
        self.tab_map = {k: self.tabs.add(self.get_translation(k)) for k in tab_keys}
        self._build_web_dashboard_button()

        self.inbound_tab = InboundTab(self.tab_map["tab_inbound"], self)
        self.update_idletasks()
        self.dispatch_tab = DispatchTab(self.tab_map["tab_dispatch"], self)
        self.update_idletasks()
        self.outbound_tab = OutboundTab(self.tab_map["tab_outbound"], self)
        self.update_idletasks()
        self.stock_tab = StockTab(self.tab_map["tab_stock"], self)
        self.update_idletasks()
        self.search_tab = SearchTab(self.tab_map["tab_search"], self)
        self.update_idletasks()
        self.yard_map_tab = YardMapTab(self.tab_map["tab_yard_map"], self)
        self.update_idletasks()
        self.dashboard_tab = DashboardTab(self.tab_map["tab_dashboard"], self)
        self.update_idletasks()
        self.log_tab = LogTab(self.tab_map["tab_log"], self)
        self.update_idletasks()

        # Register tabs với TabManager
        self.tab_manager.register_tabs(
            self.inbound_tab, self.dispatch_tab, self.outbound_tab, self.stock_tab,
            self.search_tab, self.yard_map_tab, self.dashboard_tab, self.log_tab,
        )

        self.update_all_tabs_language()

    def update_all_tabs_language(self) -> None:
        self.tab_manager.update_all_languages()

    def _build_web_dashboard_button(self) -> None:
        self.web_btn_frame = ctk.CTkFrame(self.tabs_container, fg_color="transparent")
        self.web_btn_frame.pack(side="right", anchor="n", padx=(5, 0), pady=(5, 0))
        self.web_dashboard_btn = ctk.CTkButton(
            self.web_btn_frame,
            text="🌐 Web Dashboard",
            command=self._launch_web_dashboard,
            width=140, height=32,
            fg_color="#2980b9", hover_color="#3498db",
            font=self.font_normal,
        )
        self.web_dashboard_btn.pack(pady=(0, 5))
        self.web_stop_btn = ctk.CTkButton(
            self.web_btn_frame,
            text="⏹ Dừng",
            command=self._stop_web_dashboard,
            width=140, height=28,
            fg_color="#c0392b", hover_color="#e74c3c",
            font=self.font_small,
        )

    def _update_web_dashboard_buttons(self) -> None:
        if hasattr(self, "_web_dashboard"):
            self._web_dashboard._update_buttons()

    def _build_status_bar(self) -> None:
        status_bar_frame = ctk.CTkFrame(self, height=30)
        status_bar_frame.pack(side="bottom", fill="x", padx=0, pady=0)
        self.status_var = ctk.StringVar(value=self.get_translation("status_ready"))
        self.status_label = ctk.CTkLabel(
            status_bar_frame, textvariable=self.status_var, anchor="w", font=self.font_normal
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=10)

        current_user = self.auth_manager.get_current_user()
        if current_user:
            role_key = {
                "admin": "role_admin", "operator": "role_operator", "viewer": "role_viewer",
            }.get(current_user["role"], current_user["role"])
            role_display = self.get_translation(role_key)
            self.user_label = ctk.CTkLabel(
                status_bar_frame,
                text=f"👤 {current_user['username']} ({role_display})",
                anchor="e", font=self.font_normal, text_color="#3498db",
            )
            self.user_label.pack(side="right", padx=(0, 10))

        self.author_label = ctk.CTkLabel(
            status_bar_frame,
            text=self.get_translation("author_credit"),
            anchor="e", font=self.font_normal,
        )
        self.author_label.pack(side="right", padx=10)

    # -------------------------------------------------------- Tab Events -----

    def on_tab_change(self) -> None:
        """Delegate sang TabManager."""
        self.tab_manager.on_tab_change()

    def on_data_changed(self) -> None:
        """Delegate sang TabManager."""
        self.tab_manager.on_data_changed()

    # -------------------------------------------------------- Settings -------

    def change_language(self, *args: object) -> None:
        new_lang = self.current_lang.get()
        if self.config.get("Settings", "language") != new_lang:
            self.config.set("Settings", "language", new_lang)
            logging.info(f"Ngôn ngữ đã được đổi thành '{new_lang}'.")
            self._build_ui()

    def change_theme(self, *args: object) -> None:
        theme = self.current_theme.get()
        ctk.set_appearance_mode(theme)
        self.config.set("Settings", "theme", theme)

    def center_window(self) -> None:
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = self.winfo_width(), self.winfo_height()
        x = (sw // 2) - (w // 2)
        y = max(0, (sh // 2) - (h // 2) - 40)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # -------------------------------------------------------- Auth Dialogs ---

    def _logout(self) -> None:
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
            self.auth_manager.logout()
            logging.info("Người dùng đã đăng xuất")
            self.withdraw()
            self._open_login()

    def _open_change_password(self) -> None:
        ChangePasswordDialog(self)

    def _open_user_management(self) -> None:
        if not self.auth_manager.has_permission(Permission.USER_VIEW):
            messagebox.showerror("Lỗi", "Bạn không có quyền truy cập chức năng này!")
            return
        UserManagementDialog(self)

    def _open_login_history(self) -> None:
        LoginHistoryDialog(self)

    # -------------------------------------------------------- Notifications --

    def _build_notification_panel(self) -> None:
        self.notification_panel = NotificationPanel(
            self, notification_service=self.notification_service, position="bottom-right"
        )
        if self.notification_panel.service.get_unread():
            self.notification_panel.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-40)

    def _setup_notification_checks(self) -> None:
        self.after(5000, self._run_notification_checks)
        self._notification_check_job = self.after(30 * 60 * 1000, self._periodic_notification_check)

    def _run_notification_checks(self) -> None:
        try:
            self.notification_service.run_all_checks(
                vehicle_manager=self.vehicle_manager, location_manager=self.location_manager
            )
        except Exception as e:
            logging.error(f"Error running notification checks: {e}")

    def _periodic_notification_check(self) -> None:
        self._run_notification_checks()
        self._notification_check_job = self.after(30 * 60 * 1000, self._periodic_notification_check)

    def _open_notification_settings(self) -> None:
        NotificationSettingsDialog(self, self.notification_service)

    # -------------------------------------------------------- Updates --------

    def _check_for_updates(self) -> None:
        def on_result(info: dict) -> None:
            if info and info.get("is_newer"):
                new_version = info.get("version", "")
                url = info.get("url", "")
                self.after(0, lambda: self.show_toast(f"Phiên bản mới {new_version}!\n{url}"))
                logging.info(f"Update available: {new_version} — {url}")

        check_for_updates(APP_VERSION, callback=on_result)

    # -------------------------------------------------------- Keyboard -------

    def _setup_keyboard_shortcuts(self) -> None:
        bindings = [
            ("<F5>", self._shortcut_refresh),
            ("<Control-n>", self._shortcut_new_vehicle),
            ("<Control-N>", self._shortcut_new_vehicle),
            ("<Control-f>", self._shortcut_search),
            ("<Control-F>", self._shortcut_search),
            ("<Control-e>", self._shortcut_export),
            ("<Control-E>", self._shortcut_export),
            ("<Control-d>", self._shortcut_dispatch),
            ("<Control-D>", self._shortcut_dispatch),
            ("<Control-m>", self._shortcut_yard_map),
            ("<Control-M>", self._shortcut_yard_map),
            ("<Control-b>", self._shortcut_dashboard),
            ("<Control-B>", self._shortcut_dashboard),
            ("<Control-o>", self._shortcut_outbound),
            ("<Control-O>", self._shortcut_outbound),
            ("<Control-t>", self._shortcut_stock),
            ("<Control-T>", self._shortcut_stock),
            ("<Escape>", self._shortcut_escape),
            ("<Control-q>", self._shortcut_logout),
            ("<Control-Q>", self._shortcut_logout),
            ("<F1>", self._shortcut_help),
        ]
        for key, handler in bindings:
            self.bind(key, handler)
        logging.info("Keyboard shortcuts initialized")

    def _shortcut_refresh(self, event: object = None) -> str:
        self.tab_manager.refresh_active_tab()
        self.show_toast(self.get_translation("shortcut_refreshed"))
        return "break"

    def _shortcut_new_vehicle(self, event: object = None) -> str:
        self.tab_manager.switch_to("tab_inbound", "entry_vin")
        self.inbound_tab.update_dropdowns()
        return "break"

    def _shortcut_search(self, event: object = None) -> str:
        self.tab_manager.switch_to("tab_search", "search_entry")
        return "break"

    def _shortcut_export(self, event: object = None) -> str:
        selected = self.tabs.get()
        if selected == self.get_translation("tab_stock") and hasattr(self.stock_tab, "export_stock"):
            self.stock_tab.export_stock()
        elif selected == self.get_translation("tab_dashboard") and hasattr(self.dashboard_tab, "export_pdf"):
            self.dashboard_tab.export_pdf()
        else:
            self.show_toast(self.get_translation("shortcut_export_not_available"))
        return "break"

    def _shortcut_dispatch(self, event: object = None) -> str:
        self.tabs.set(self.get_translation("tab_dispatch"))
        self.dispatch_tab.update_dropdowns()
        return "break"

    def _shortcut_yard_map(self, event: object = None) -> str:
        self.tabs.set(self.get_translation("tab_yard_map"))
        if hasattr(self.yard_map_tab, "refresh_data"):
            self.yard_map_tab.refresh_data()
        return "break"

    def _shortcut_dashboard(self, event: object = None) -> str:
        self.tabs.set(self.get_translation("tab_dashboard"))
        return "break"

    def _shortcut_escape(self, event: object = None) -> str:
        selected = self.tabs.get()
        if selected == self.get_translation("tab_stock"):
            if hasattr(self.stock_tab, "selected_vins"):
                self.stock_tab.selected_vins.clear()
                self.stock_tab.update_stock_list()
                self.stock_tab._update_selected_count_label()
        elif selected == self.get_translation("tab_search"):
            if hasattr(self.search_tab, "search_entry"):
                self.search_tab.search_entry.delete(0, "end")
        return "break"

    def _shortcut_logout(self, event: object = None) -> str:
        self._logout()
        return "break"

    def _shortcut_outbound(self, event: object = None) -> str:
        self.tabs.set(self.get_translation("tab_outbound"))
        self.outbound_tab.update_dropdowns()
        if hasattr(self.outbound_tab, "scan_entry"):
            self.after(100, lambda: self.outbound_tab.scan_entry.focus_set())
        return "break"

    def _shortcut_stock(self, event: object = None) -> str:
        self.tabs.set(self.get_translation("tab_stock"))
        return "break"

    def _shortcut_help(self, event: object = None) -> str:
        messagebox.showinfo(
            self.get_translation("help_shortcuts_title"),
            self.get_translation("help_shortcuts_text"),
            parent=self,
        )
        return "break"

    # --------------------------------------------------------- UI Helpers ----

    def show_toast(self, message: str) -> None:
        Toast(self, message)

    def log_to_widget(self, widget: object, message: str, tag: object = None) -> None:
        try:
            if widget.winfo_exists():
                widget.configure(state="normal")
                timestamp = datetime.now().strftime("[%H:%M:%S]")
                widget.insert("end", f"{timestamp} {message}\n", tag)
                widget.see("end")
                widget.configure(state="disabled")
        except Exception:
            pass

    # ------------------------------------------------------ Menu Commands ----

    def manage_drivers(self) -> None:
        ManagementDialog(self, self.get_translation("dialog_manage_drivers_title"), ENTITY_TYPE_DRIVER)
        self.on_data_changed()

    def manage_transport_vehicles(self) -> None:
        ManagementDialog(
            self, self.get_translation("dialog_manage_transports_title"), ENTITY_TYPE_TRANSPORT
        )
        self.on_data_changed()

    def manage_layout(self) -> None:
        LayoutManagementDialog(self, self.location_manager)
        self.on_data_changed()

    def select_voucher_template(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file Mẫu Phiếu Vận Chuyển",
            filetypes=[("Word Documents", "*.docx")],
        )
        if path:
            self.config.set("Paths", "voucher_template_path", path)
            save_config(self.config)
            self.show_toast(f"Đã cập nhật mẫu phiếu: {os.path.basename(path)}")

    def open_voucher_creation_tool(self) -> None:
        default_filename = f"PHIEU_VC_{datetime.now().strftime('%d%m%Y_%H%M')}.docx"
        VoucherCreationDialog(self, default_output_filename=default_filename)

    def open_archive_explorer(self) -> None:
        ArchiveExplorerDialog(self)

    def open_deleted_vehicles(self) -> None:
        DeletedVehiclesDialog(
            self, vehicle_manager=self.vehicle_manager, on_restore_callback=self.on_data_changed
        )

    def _open_pdf_report(self) -> None:
        from ui.pdf_report_dialog import PDFReportDialog
        PDFReportDialog(self)

    def _open_print_templates(self) -> None:
        from ui.print_templates_dialog import PrintTemplatesDialog
        PrintTemplatesDialog(self)

    def _open_config_dialog(self) -> None:
        from ui.config_dialog import ConfigDialog
        ConfigDialog(self)

    def _open_onboarding(self) -> None:
        from ui.onboarding_dialog import OnboardingDialog
        OnboardingDialog(self)

    def _launch_web_dashboard(self) -> None:
        if hasattr(self, "_web_dashboard"):
            self._web_dashboard.launch()

    def _stop_web_dashboard(self) -> None:
        if hasattr(self, "_web_dashboard"):
            self._web_dashboard.stop()

    def prompt_for_history_export(self) -> None:
        dialog = DateRangeDialog(self, title=self.get_translation("menu_export_history"))
        if dialog.result:
            start_date, end_date = dialog.result
            self.stock_tab.export_history(start_date, end_date)

    def prompt_archive_data(self) -> None:
        dialog = DateRangeDialog(self, title=self.get_translation("menu_archive"))
        if not dialog.result:
            return
        start_date, end_date = dialog.result
        confirm_msg = self.get_translation("confirm_archive_msg").format(
            start=start_date.strftime("%d/%m/%Y"),
            end=end_date.strftime("%d/%m/%Y"),
        )
        if messagebox.askyesno(
            self.get_translation("confirm_archive_title"), confirm_msg, icon="warning"
        ):
            self.status_var.set(self.get_translation("status_archiving"))
            self.update_idletasks()
            result = self.vehicle_manager.archive_shipped_vehicles(start_date, end_date)
            if result["success"]:
                messagebox.showinfo(
                    self.get_translation("dialog_archive_complete_title"), result["message"]
                )
            else:
                messagebox.showerror(self.get_translation("dialog_error_title"), result["message"])
            self.status_var.set(self.get_translation("status_ready"))
            self.on_data_changed()

    # ------------------------------------------------------- Lifecycle ------

    def _sync_owner_map(self) -> None:
        """Cập nhật owner_map.json với các tên chủ hàng canonical hiện tại trong DB."""
        try:
            import json, re, unidecode as _ud
            from config import OWNER_MAP_FILE

            owners = self.vehicle_manager._known_owners
            if not owners:
                return

            map_path = OWNER_MAP_FILE
            try:
                with open(map_path, 'r', encoding='utf-8') as f:
                    owner_map = json.load(f)
            except Exception:
                owner_map = {"_comment": "Owner name normalization map"}

            added = 0
            for canonical in owners:
                lower = canonical.lower()
                ascii_ver = _ud.unidecode(lower)
                for variant in (lower, ascii_ver,
                                lower.replace(' ', ''), ascii_ver.replace(' ', '')):
                    if variant and variant not in owner_map:
                        owner_map[variant] = canonical
                        added += 1

            if added > 0:
                os.makedirs(os.path.dirname(map_path), exist_ok=True)
                with open(map_path, 'w', encoding='utf-8') as f:
                    json.dump(owner_map, f, ensure_ascii=False, indent=4)
                logging.info(f"owner_map.json: thêm {added} variants mới khi đóng app.")
        except Exception as e:
            logging.warning(f"_sync_owner_map thất bại (non-critical): {e}")

    def on_close(self) -> None:
        if messagebox.askokcancel(
            self.get_translation("confirm_exit_title"),
            self.get_translation("confirm_exit_msg"),
        ):
            self._sync_owner_map()
            if hasattr(self, "_web_dashboard") and self._web_dashboard.is_running:
                self._web_dashboard.stop()
            save_config(self.config)
            BaseManager.close_connection()
            self.destroy()
