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
    bao gồm tạo thủ công, import từ file Excel, và quản lý các khu đã tạo.
    """
    def __init__(self, parent, location_manager):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.location_manager = location_manager
        self.layout_manager = LayoutManager(location_manager)
        
        self.title(self.app.get_translation("manage_layout_title"))
        self.geometry("600x550")
        self.resizable(False, False)

        # --- Khung tạo thủ công ---
        manual_frame = ctk.CTkFrame(self)
        manual_frame.pack(pady=PAD_GENERAL, padx=PAD_GENERAL, fill="x")
        manual_frame.grid_columnconfigure((0, 1), weight=1)

        lbl_manual_title = ctk.CTkLabel(manual_frame, text="➕ Tạo Khu mới:", font=ctk.CTkFont(weight="bold"))
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

        # --- Khung quản lý khu đã tạo ---
        manage_frame = ctk.CTkFrame(self)
        manage_frame.pack(pady=PAD_GENERAL, padx=PAD_GENERAL, fill="x")
        manage_frame.grid_columnconfigure(0, weight=1)

        lbl_manage_title = ctk.CTkLabel(manage_frame, text="📋 Quản lý Khu đã tạo:", font=ctk.CTkFont(weight="bold"))
        lbl_manage_title.grid(row=0, column=0, columnspan=3, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")

        # Dropdown chọn khu
        self.block_var = ctk.StringVar(value="")
        self.block_menu = ctk.CTkOptionMenu(
            manage_frame,
            variable=self.block_var,
            values=["-- Chọn khu --"],
            width=250,
            command=self._on_block_selected
        )
        self.block_menu.grid(row=1, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")

        # Nút đổi tên
        btn_rename = ctk.CTkButton(
            manage_frame, 
            text="✏️ Đổi tên", 
            command=self.rename_block,
            width=100,
            fg_color="#3498db"
        )
        btn_rename.grid(row=1, column=1, padx=PAD_SMALL, pady=PAD_SMALL)

        # Nút xóa
        btn_delete = ctk.CTkButton(
            manage_frame, 
            text="🗑️ Xóa", 
            command=self.delete_block,
            width=100,
            fg_color="#e74c3c"
        )
        btn_delete.grid(row=1, column=2, padx=PAD_SMALL, pady=PAD_SMALL)

        # Thông tin khu đã chọn
        self.block_info_label = ctk.CTkLabel(
            manage_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.block_info_label.grid(row=2, column=0, columnspan=3, padx=PAD_SMALL, pady=(0, PAD_SMALL), sticky="w")

        # --- Khung import Excel ---
        excel_frame = ctk.CTkFrame(self)
        excel_frame.pack(pady=PAD_GENERAL, padx=PAD_GENERAL, fill="x")
        excel_frame.grid_columnconfigure((0, 1), weight=1)

        lbl_excel_title = ctk.CTkLabel(excel_frame, text="📥 Import từ Excel:", font=ctk.CTkFont(weight="bold"))
        lbl_excel_title.grid(row=0, column=0, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")

        btn_import = ctk.CTkButton(excel_frame, text=self.app.get_translation("btn_import_excel_source"), command=self.import_from_excel)
        btn_import.grid(row=1, column=0, padx=PAD_SMALL, pady=PAD_GENERAL, sticky="ew")

        btn_template = ctk.CTkButton(excel_frame, text=self.app.get_translation("btn_download_template"), command=self.download_template)
        btn_template.grid(row=1, column=1, padx=PAD_SMALL, pady=PAD_GENERAL, sticky="ew")

        # Load danh sách khu
        self._load_blocks()

        self.grab_set()
        self.wait_window()

    def _load_blocks(self):
        """Load danh sách các khu đã tạo."""
        blocks = self.location_manager.get_all_blocks()
        if blocks:
            self.block_menu.configure(values=["-- Chọn khu --"] + blocks)
            self.block_var.set("-- Chọn khu --")
        else:
            self.block_menu.configure(values=["-- Chưa có khu nào --"])
            self.block_var.set("-- Chưa có khu nào --")
        self.block_info_label.configure(text="")

    def _on_block_selected(self, value):
        """Khi người dùng chọn một khu."""
        if value.startswith("--"):
            self.block_info_label.configure(text="")
            return
        
        # Lấy thống kê của khu
        stats = self.location_manager.get_block_statistics(value)
        if stats:
            info_text = f"📊 Khu [{value}]: {stats['total']} vị trí ({stats['occupied']} đang sử dụng, {stats['free']} trống)"
            self.block_info_label.configure(text=info_text, text_color="#2c3e50")
        else:
            self.block_info_label.configure(text="", text_color="gray")

    def rename_block(self):
        """Đổi tên khu đã chọn."""
        old_name = self.block_var.get()
        if old_name.startswith("--"):
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một khu để đổi tên!", parent=self)
            return
        
        # Dialog nhập tên mới
        dialog = ctk.CTkInputDialog(
            text=f"Nhập tên mới cho khu [{old_name}]:",
            title="Đổi tên Khu"
        )
        new_name = dialog.get_input()
        
        if not new_name or not new_name.strip():
            return
        
        new_name = new_name.strip().upper()
        
        if new_name == old_name:
            return
        
        # Kiểm tra tên mới đã tồn tại chưa
        existing_blocks = self.location_manager.get_all_blocks()
        if new_name in existing_blocks:
            messagebox.showerror("Lỗi", f"Khu [{new_name}] đã tồn tại!", parent=self)
            return
        
        # Thực hiện đổi tên
        success = self.location_manager.rename_block(old_name, new_name)
        if success:
            messagebox.showinfo("Thành công", f"Đã đổi tên [{old_name}] thành [{new_name}]!", parent=self)
            self._load_blocks()
            self.app.on_data_changed()
        else:
            messagebox.showerror("Lỗi", "Không thể đổi tên khu!", parent=self)

    def delete_block(self):
        """Xóa khu đã chọn."""
        block_name = self.block_var.get()
        if block_name.startswith("--"):
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một khu để xóa!", parent=self)
            return
        
        # Lấy thống kê để cảnh báo
        stats = self.location_manager.get_block_statistics(block_name)
        
        warning_msg = f"Bạn có chắc muốn xóa khu [{block_name}]?\n\n"
        if stats and stats['occupied'] > 0:
            warning_msg += f"⚠️ CẢNH BÁO: Có {stats['occupied']} vị trí đang có xe!\n"
            warning_msg += "Các xe sẽ mất vị trí sau khi xóa.\n\n"
        warning_msg += f"Tổng cộng {stats['total'] if stats else 0} vị trí sẽ bị xóa."
        
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            warning_msg,
            icon="warning",
            parent=self
        )
        
        if not confirm:
            return
        
        # Thực hiện xóa
        success, deleted_count = self.location_manager.delete_block(block_name)
        if success:
            messagebox.showinfo("Thành công", f"Đã xóa khu [{block_name}] ({deleted_count} vị trí)!", parent=self)
            self._load_blocks()
            self.app.on_data_changed()
        else:
            messagebox.showerror("Lỗi", "Không thể xóa khu!", parent=self)

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