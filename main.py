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
from ui.log_tab import LogTab
from ui.dispatch_tab import DispatchTab
from ui.components import Toast, DateRangeDialog
from ui.management_dialogs import ManagementDialog
from ui.layout_management_dialog import LayoutManagementDialog
from ui.voucher_creation_dialog import VoucherCreationDialog
from ui.archive_explorer_dialog import ArchiveExplorerDialog # Đảm bảo import này tồn tại
from ui.deleted_vehicles_dialog import DeletedVehiclesDialog
from config import APP_VERSION, APP_NAME, FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_LARGE, FONT_SIZE_SMALL
class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_logging()
        
        self.config = load_config()
        self.current_lang = ctk.StringVar(value=self.config.get("Settings", "language", fallback="vi"))
        self.current_theme = ctk.StringVar(value=self.config.get("Settings", "theme", fallback="System"))
        
        ctk.set_appearance_mode(self.current_theme.get())
        
        self.font_normal = ctk.CTkFont(family="Arial", size=14)
        self.font_bold = ctk.CTkFont(family="Arial", size=14, weight="bold")
        self.font_small_italic = ctk.CTkFont(family="Arial", size=12, slant="italic")
        
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
        # -------------------------------------------------
        
        self._build_ui()
        
        logging.info(f"Ứng dụng {APP_VERSION} đã khởi động thành công.")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
                
        self._build_status_bar()
        self.after(100, self.inbound_tab.update_dropdowns)
        # ==========================================================
        
        #self.on_data_changed()

        
    def _build_menu(self):
        self.main_menu = Menu(self)
        menu_font = ("Arial", 12)
        self.file_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.tools_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.settings_menu = Menu(self.main_menu, tearoff=0, font=menu_font)
        self.lang_menu = Menu(self.settings_menu, tearoff=0, font=menu_font)
        self.theme_menu = Menu(self.settings_menu, tearoff=0, font=menu_font)
        self.configure(menu=self.main_menu)
        self._update_menu_text()

    def _update_menu_text(self):
        self.main_menu.delete(0, "end")
        self.file_menu.delete(0, "end")
        self.tools_menu.delete(0, "end")
        self.settings_menu.delete(0, "end")
        self.lang_menu.delete(0, "end")
        self.theme_menu.delete(0, "end")

        self.main_menu.add_cascade(label=self.get_translation("menu_file"), menu=self.file_menu)
        self.main_menu.add_cascade(label=self.get_translation("menu_tools"), menu=self.tools_menu)
        self.main_menu.add_cascade(label=self.get_translation("menu_settings"), menu=self.settings_menu)

        self.file_menu.add_command(label=self.get_translation("menu_exit"), command=self.on_close)
        self.tools_menu.add_command(label=self.get_translation("menu_create_vouchers"), command=self.open_voucher_creation_tool)
        # === CẬP NHẬT: Sử dụng key dịch thuật ===
        self.tools_menu.add_command(label=self.get_translation("menu_archive_explorer"), command=self.open_archive_explorer)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label=self.get_translation("menu_deleted_vehicles"), command=self.open_deleted_vehicles)
        # ===================


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
        self.settings_menu.add_command(label=self.get_translation("menu_archive"), command=self.prompt_archive_data)

    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        tab_names = ["tab_inbound", "tab_dispatch", "tab_outbound", "tab_stock", "tab_search", "tab_dashboard", "tab_log"]
        self.tab_map = {name: self.tabs.add(self.get_translation(name)) for name in tab_names}

        # === SỬA LỖI: Khởi tạo tất cả các đối tượng tab trước ===
        self.inbound_tab = InboundTab(self.tab_map["tab_inbound"], self)
        self.dispatch_tab = DispatchTab(self.tab_map["tab_dispatch"], self)
        self.outbound_tab = OutboundTab(self.tab_map["tab_outbound"], self)
        self.stock_tab = StockTab(self.tab_map["tab_stock"], self)
        self.search_tab = SearchTab(self.tab_map["tab_search"], self)
        self.dashboard_tab = DashboardTab(self.tab_map["tab_dashboard"], self)
        self.log_tab = LogTab(self.tab_map["tab_log"], self)
        
        # Sau khi tất cả các tab đã được tạo, mới gọi update_language
        self.update_all_tabs_language()
        # =====================================================

    def update_all_tabs_language(self):
        """Cập nhật ngôn ngữ cho tất cả các tab."""
        for tab in [self.inbound_tab, self.dispatch_tab, self.outbound_tab, self.stock_tab, self.search_tab, self.dashboard_tab]:
            if hasattr(tab, 'update_language'):
                tab.update_language()

    def _build_status_bar(self):
        """Xây dựng thanh trạng thái ở dưới cùng cửa sổ."""
        status_bar_frame = ctk.CTkFrame(self, height=30)
        status_bar_frame.pack(side="bottom", fill="x", padx=0, pady=0) # pack vào self
        self.status_var = ctk.StringVar(value=self.get_translation("status_ready"))
        self.status_label = ctk.CTkLabel(status_bar_frame, textvariable=self.status_var, anchor="w", font=self.font_normal)
        self.status_label.pack(side="left", fill="x", expand=True, padx=10)
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

    def on_tab_change(self):
        """Xử lý sự kiện khi người dùng chuyển tab (Lazy Loading)."""
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
        """Hàm điều phối làm mới giao diện khi có thay đổi dữ liệu."""
        logging.info("Phát hiện thay đổi dữ liệu, đang làm mới các thành phần liên quan.")
        if hasattr(self, 'stock_tab'):
            self.stock_tab.refresh_all()
        if hasattr(self, 'inbound_tab'):
            self.inbound_tab.update_dropdowns()
        if hasattr(self, 'outbound_tab'):
            self.outbound_tab.update_dropdowns()
        if hasattr(self, 'dispatch_tab'):
            self.dispatch_tab.update_dropdowns()

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
            save_config(self.config)
            BaseManager.close_connection()
            self.destroy()

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
    # Đảm bảo đóng kết nối CSDL khi ứng dụng kết thúc
    BaseManager.close_connection()
    # logging.info("Ứng dụng đã đóng.")