# ui/archive_explorer_dialog.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from config import ARCHIVES_DIR
from ui.components import DateRangeDialog, harmonize_combobox_style
from report_generators import excel_generator
import utils

class ArchiveExplorerDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.title(self.app.get_translation("dialog_archive_explorer_title"))
        self.geometry("600x250")

        self.archive_files = []

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        main_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(main_frame, text=self.app.get_translation("lbl_select_archive_file"), font=self.app.font_normal).grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.archive_file_combo = ctk.CTkComboBox(main_frame, values=[], font=self.app.font_normal)
        self.archive_file_combo.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        harmonize_combobox_style(self.archive_file_combo)

        ctk.CTkLabel(main_frame, text=self.app.get_translation("lbl_time_period"), font=self.app.font_normal).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        self.date_range_label = ctk.CTkLabel(main_frame, text=self.app.get_translation("lbl_not_selected"), font=self.app.font_normal)
        self.date_range_label.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        ctk.CTkButton(main_frame, text=self.app.get_translation("btn_select_period"), command=self.select_date_range, font=self.app.font_normal).grid(row=1, column=2, padx=5, pady=10)

        self.export_button = ctk.CTkButton(main_frame, text=self.app.get_translation("btn_export_archive_to_excel"), command=self.export_to_excel, font=self.app.font_bold, height=40)
        self.export_button.grid(row=2, column=0, columnspan=3, padx=5, pady=20, sticky="ew")

        self.start_date = None
        self.end_date = None
        self._load_archive_files()
        self.grab_set()
        self.wait_window()

    def _load_archive_files(self):
        if not os.path.exists(ARCHIVES_DIR):
            self.archive_file_combo.set(self.app.get_translation("msg_no_archive_folder"))
            self.archive_files = []
            return
        
        self.archive_files = [f for f in os.listdir(ARCHIVES_DIR) if f.endswith(('.db', '.archive'))]
        if self.archive_files:
            self.archive_file_combo.configure(values=self.archive_files)
            self.archive_file_combo.set(self.archive_files[0])
        else:
            self.archive_file_combo.set(self.app.get_translation("msg_no_archive_files"))

    def select_date_range(self):
        # === SỬA LỖI: Sử dụng key dịch thuật cho tiêu đề ===
        dialog = DateRangeDialog(self.app, self.app.get_translation("dialog_archive_explorer_title"))
        # ===============================================
        if dialog.result:
            self.start_date, self.end_date = dialog.result
            # === SỬA LỖI: Sử dụng key dịch thuật cho hiển thị ngày ===
            from_str = self.app.get_translation("lbl_from_date").replace(":", "")
            to_str = self.app.get_translation("lbl_to_date").replace(":", "")
            self.date_range_label.configure(text=f"{from_str} {self.start_date.strftime('%d/%m/%Y')} {to_str} {self.end_date.strftime('%d/%m/%Y')}")
            # =====================================================

    def export_to_excel(self):
        if not self.archive_files:
            messagebox.showerror(self.app.get_translation("dialog_error_title"), self.app.get_translation("err_select_valid_archive"), parent=self)
            return
        
        archive_file = self.archive_file_combo.get()
        
        if not self.start_date or not self.end_date:
            messagebox.showerror(self.app.get_translation("dialog_error_title"), self.app.get_translation("err_select_time_period"), parent=self)
            return

        archive_path = os.path.join(ARCHIVES_DIR, archive_file)
        
        result = self.app.vehicle_manager.get_archived_vehicles(archive_path, self.start_date, self.end_date)

        if not result["success"]:
            error_message = self.app.get_translation(result['message']) if self.app.get_translation(result['message']) != result['message'] else result['message']
            messagebox.showerror(self.app.get_translation("dialog_error_title"), self.app.get_translation("err_cannot_read_archive").format(error=error_message), parent=self)
            return
        
        data = result["data"]
        if not data:
            messagebox.showinfo(self.app.get_translation("dialog_info_title"), self.app.get_translation("info_no_data_in_archive"), parent=self)
            return

        default_name = f"Luu_tru_{self.start_date.strftime('%d%m%Y')}_{self.end_date.strftime('%d%m%Y')}.xlsx"
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile=default_name)
        if not path: return

        cols = {
            "vin": self.app.get_translation("tree_vin"), 
            "owner": self.app.get_translation("tree_owner"), 
            "vehicle_type": self.app.get_translation("tree_type"),
            "date_in": self.app.get_translation("tree_date_in"), 
            "date_out": self.app.get_translation("tree_date_out"),
            "transport_vehicle": self.app.get_translation("tree_transport_vehicle"), 
            "driver_name": self.app.get_translation("tree_driver")
        }
        
        export_result = excel_generator.generate_excel_report(path, data, cols)
        if export_result["success"]:
            self.app.show_toast(self.app.get_translation("toast_export_archive_success"))
            self.destroy()
        else:
            messagebox.showerror(self.app.get_translation("dialog_error_title"), f"Không thể xuất file:\n{export_result['message']}", parent=self)