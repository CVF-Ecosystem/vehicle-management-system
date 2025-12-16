# ui/layout_management_dialog.py
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import pandas as pd
from config import PAD_GENERAL, PAD_SMALL, EXPECTED_BLOCK_COL, EXPECTED_ROW_COL, EXPECTED_SLOT_COL
from layout_manager import LayoutManager

class LayoutManagementDialog(ctk.CTkToplevel):
    """
    Cửa sổ giao diện cho phép người dùng quản lý layout bãi xe,
    bao gồm tạo thủ công và import từ file Excel.
    """
    def __init__(self, parent, location_manager):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.layout_manager = LayoutManager(location_manager)
        
        self.title(self.app.get_translation("manage_layout_title"))
        self.geometry("550x380")
        self.resizable(False, False)

        # --- Khung tạo thủ công ---
        manual_frame = ctk.CTkFrame(self)
        manual_frame.pack(pady=PAD_GENERAL, padx=PAD_GENERAL, fill="x")
        manual_frame.grid_columnconfigure((0, 1), weight=1)

        lbl_manual_title = ctk.CTkLabel(manual_frame, text=self.app.get_translation("frame_manual_layout"), font=ctk.CTkFont(weight="bold"))
        lbl_manual_title.grid(row=0, column=0, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")

        self.block_entry = ctk.CTkEntry(manual_frame, placeholder_text=self.app.get_translation("placeholder_block"))
        self.block_entry.grid(row=1, column=0, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")

        self.row_start_entry = ctk.CTkEntry(manual_frame, placeholder_text=self.app.get_translation("placeholder_row_start"))
        self.row_start_entry.grid(row=2, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        
        self.row_end_entry = ctk.CTkEntry(manual_frame, placeholder_text=self.app.get_translation("placeholder_row_end"))
        self.row_end_entry.grid(row=2, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")

        self.slots_entry = ctk.CTkEntry(manual_frame, placeholder_text=self.app.get_translation("placeholder_slots"))
        self.slots_entry.grid(row=3, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")

        btn_generate = ctk.CTkButton(manual_frame, text=self.app.get_translation("btn_generate"), command=self.generate_manually)
        btn_generate.grid(row=3, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")

        # --- Khung import Excel ---
        excel_frame = ctk.CTkFrame(self)
        excel_frame.pack(pady=PAD_GENERAL, padx=PAD_GENERAL, fill="x")
        excel_frame.grid_columnconfigure((0, 1), weight=1)

        lbl_excel_title = ctk.CTkLabel(excel_frame, text=self.app.get_translation("frame_import_layout"), font=ctk.CTkFont(weight="bold"))
        lbl_excel_title.grid(row=0, column=0, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")

        btn_import = ctk.CTkButton(excel_frame, text=self.app.get_translation("btn_import_excel_source"), command=self.import_from_excel)
        btn_import.grid(row=1, column=0, padx=PAD_SMALL, pady=PAD_GENERAL, sticky="ew")

        btn_template = ctk.CTkButton(excel_frame, text=self.app.get_translation("btn_download_template"), command=self.download_template)
        btn_template.grid(row=1, column=1, padx=PAD_SMALL, pady=PAD_GENERAL, sticky="ew")

        self.grab_set()
        self.wait_window()

    def generate_manually(self):
        """Xử lý sự kiện nhấn nút 'Tạo Vị trí'."""
        block = self.block_entry.get()
        row_start = self.row_start_entry.get()
        row_end = self.row_end_entry.get()
        slots = self.slots_entry.get()

        if not all([block, row_start, row_end, slots]):
            messagebox.showwarning(self.app.get_translation("warn_missing_info"), "Vui lòng điền đầy đủ thông tin.", parent=self)
            return

        ok, added, skipped = self.layout_manager.generate_from_rules(block, row_start, row_end, slots)
        if ok:
            msg = self.app.get_translation("info_generate_success").format(s=added, e=skipped)
            messagebox.showinfo("Hoàn tất", msg, parent=self)
            self.app.on_data_changed() # Làm mới các dropdown vị trí
        else:
            messagebox.showerror(self.app.get_translation("err_invalid_input"), self.app.get_translation("err_invalid_input_msg"), parent=self)

    def import_from_excel(self):
        """Xử lý sự kiện nhấn nút 'Chọn File Excel...'."""
        path = filedialog.askopenfilename(
            title="Chọn file Excel chứa layout",
            filetypes=[("Excel files", "*.xlsx;*.xls")],
            parent=self
        )
        if not path:
            return

        ok, msg, added, skipped = self.layout_manager.generate_from_excel(path)
        if ok:
            info_msg = self.app.get_translation("info_import_success").format(s=added, e=skipped)
            messagebox.showinfo("Hoàn tất", info_msg, parent=self)
            self.app.on_data_changed() # Làm mới các dropdown vị trí
        else:
            error_title = self.app.get_translation("err_read_file")
            if "thiếu các cột" in msg:
                error_title = self.app.get_translation("err_column_missing")
            messagebox.showerror(error_title, msg, parent=self)

    def download_template(self):
        """Xử lý sự kiện nhấn nút 'Tải File Mẫu'."""
        path = filedialog.asksaveasfilename(
            title="Lưu file mẫu Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile="layout_template.xlsx",
            parent=self
        )
        if not path:
            return
        
        try:
            template_data = {
                EXPECTED_BLOCK_COL: ['A', 'A', 'B'],
                EXPECTED_ROW_COL: ['01', '01', '01'],
                EXPECTED_SLOT_COL: [1, 2, 1]
            }
            df = pd.DataFrame(template_data)
            df.to_excel(path, index=False)
            messagebox.showinfo("Thành công", f"Đã lưu file mẫu tại:\n{os.path.abspath(path)}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo file mẫu: {e}", parent=self)