# ui/archive_explorer_dialog.py
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import threading
from ui.components import DateRangeDialog, style_treeview, harmonize_combobox_style
from report_generators import excel_generator
import utils

class ArchiveExplorerDialog(ctk.CTkToplevel):
    """
    Tra cứu và quản lý dữ liệu đã Soft-Archive (is_archived=1).
    Đọc trực tiếp từ DB chính — không cần file .db bên ngoài.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.vehicle_manager = parent.vehicle_manager
        self.title(self.app.get_translation("dialog_archive_explorer_title"))
        self.geometry("900x600")
        self.resizable(True, True)

        self.start_date = None
        self.end_date = None
        self._current_data = []

        self._build_ui()
        self.grab_set()

    def _build_ui(self):
        # --- Toolbar ---
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(12, 0))

        ctk.CTkLabel(toolbar, text=self.app.get_translation("lbl_time_period"),
                     font=self.app.font_normal).pack(side="left", padx=(0, 5))

        self.date_range_label = ctk.CTkLabel(
            toolbar,
            text=self.app.get_translation("lbl_not_selected"),
            font=self.app.font_normal,
            text_color="gray"
        )
        self.date_range_label.pack(side="left", padx=(0, 8))

        ctk.CTkButton(toolbar, text=self.app.get_translation("btn_select_period"),
                      command=self.select_date_range,
                      width=90, font=self.app.font_normal).pack(side="left", padx=(0, 4))

        ctk.CTkButton(toolbar, text="🔍 Xem",
                      command=self.load_archive_data,
                      width=80, fg_color="#2980b9", hover_color="#3498db",
                      font=self.app.font_normal).pack(side="left", padx=(0, 12))

        # Lọc chủ hàng
        ctk.CTkLabel(toolbar, text="Chủ hàng:", font=self.app.font_normal).pack(side="left", padx=(0, 4))
        self.owner_filter_var = ctk.StringVar()
        self.owner_combo = ctk.CTkComboBox(toolbar, variable=self.owner_filter_var,
                                           values=["Tất cả"], width=150, font=self.app.font_normal)
        self.owner_combo.set("Tất cả")
        self.owner_combo.pack(side="left", padx=(0, 12))
        harmonize_combobox_style(self.owner_combo)

        # Nút xuất Excel
        ctk.CTkButton(toolbar, text="📥 Xuất Excel",
                      command=self.export_to_excel,
                      width=110, font=self.app.font_bold).pack(side="right", padx=(4, 0))

        # Nút Hoàn tác archive
        ctk.CTkButton(toolbar, text="↩ Hoàn tác archive",
                      command=self.unarchive_selected,
                      width=140, fg_color="#e67e22", hover_color="#d35400",
                      font=self.app.font_normal).pack(side="right", padx=(0, 4))

        # --- Label đếm ---
        self.count_label = ctk.CTkLabel(self, text="", font=self.app.font_small,
                                        text_color="gray")
        self.count_label.pack(anchor="w", padx=18, pady=(6, 0))

        # --- Treeview ---
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(6, 15))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("stt", "vin", "owner", "vehicle_type", "date_in", "date_out",
                "transport_vehicle", "driver_name", "archived_at", "archived_by")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        style_treeview(self.app, self.tree)

        headers = {
            "stt": ("STT", 45),
            "vin": ("SỐ KHUNG", 190),
            "owner": ("CHỦ HÀNG", 130),
            "vehicle_type": ("LOẠI XE", 110),
            "date_in": ("NGÀY NHẬP", 120),
            "date_out": ("NGÀY XUẤT", 120),
            "transport_vehicle": ("XE VẬN CHUYỂN", 120),
            "driver_name": ("TÀI XẾ", 100),
            "archived_at": ("NGÀY LƯU TRỮ", 130),
            "archived_by": ("NGƯỜI LƯU TRỮ", 100),
        }
        for col, (heading, width) in headers.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="center" if col in ("stt", "date_in", "date_out", "archived_at") else "w")

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar_y.set)
        scrollbar_y.grid(row=0, column=1, sticky="ns")

        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscroll=scrollbar_x.set)
        scrollbar_x.grid(row=1, column=0, sticky="ew")

    def select_date_range(self):
        dialog = DateRangeDialog(self.app, self.app.get_translation("dialog_archive_explorer_title"))
        if dialog.result:
            self.start_date, self.end_date = dialog.result
            from_label = self.start_date.strftime('%d/%m/%Y')
            to_label = self.end_date.strftime('%d/%m/%Y')
            self.date_range_label.configure(
                text=f"Từ {from_label} đến {to_label}",
                text_color=("black", "white")
            )

    def load_archive_data(self):
        owner = self.owner_filter_var.get()
        owner_filter = None if owner == "Tất cả" else owner

        def worker():
            result = self.vehicle_manager.get_archived_vehicles_from_main_db(
                start_date=self.start_date,
                end_date=self.end_date,
                owner_filter=owner_filter
            )
            self.after(0, lambda: self._update_tree(result))

        threading.Thread(target=worker, daemon=True).start()

    def _update_tree(self, result):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not result.get("success"):
            messagebox.showerror("Lỗi", result.get("message", "Không thể tải dữ liệu."), parent=self)
            return

        self._current_data = result.get("data", [])

        # Cập nhật filter chủ hàng
        owners = sorted(set(r.get("owner", "") for r in self._current_data if r.get("owner")))
        self.owner_combo.configure(values=["Tất cả"] + owners)

        for idx, row in enumerate(self._current_data, 1):
            date_in_str = utils.format_datetime_for_display(row.get("date_in", ""))
            date_out_str = utils.format_datetime_for_display(row.get("date_out", ""))
            archived_at_str = utils.format_datetime_for_display(row.get("archived_at", ""))

            self.tree.insert("", "end", values=(
                idx,
                row.get("vin", ""),
                row.get("owner", ""),
                row.get("vehicle_type", ""),
                date_in_str,
                date_out_str,
                row.get("transport_vehicle", ""),
                row.get("driver_name", ""),
                archived_at_str,
                row.get("archived_by", ""),
            ))

        count = len(self._current_data)
        self.count_label.configure(
            text=f"Tìm thấy {count} bản ghi đã lưu trữ." if count > 0 else "Không có dữ liệu archive trong khoảng thời gian đã chọn."
        )

    def unarchive_selected(self):
        """Hoàn tác archive cho khoảng thời gian đã chọn."""
        if not self.start_date or not self.end_date:
            messagebox.showwarning("Chưa chọn thời gian",
                                   "Vui lòng chọn khoảng thời gian trước.", parent=self)
            return

        count = len(self._current_data)
        if count == 0:
            messagebox.showinfo("Không có dữ liệu", "Không có bản ghi nào để hoàn tác.", parent=self)
            return

        if not messagebox.askyesno(
            "Xác nhận hoàn tác",
            f"Bạn có chắc muốn HOÀN TÁC lưu trữ cho {count} xe?\n\n"
            f"Xe sẽ xuất hiện trở lại trong lịch sử xuất bãi.",
            parent=self
        ):
            return

        result = self.vehicle_manager.unarchive_vehicles(self.start_date, self.end_date)
        if result["success"]:
            self.app.show_toast(f"Đã hoàn tác {result['count']} bản ghi archive.")
            self.load_archive_data()
            self.app.on_data_changed()
        else:
            messagebox.showerror("Lỗi", result["message"], parent=self)

    def export_to_excel(self):
        if not self._current_data:
            messagebox.showwarning("Không có dữ liệu",
                                   "Vui lòng tải dữ liệu trước khi xuất.", parent=self)
            return

        suffix = ""
        if self.start_date and self.end_date:
            suffix = f"_{self.start_date.strftime('%d%m%Y')}_{self.end_date.strftime('%d%m%Y')}"
        default_name = f"Luu_tru{suffix}.xlsx"
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=default_name
        )
        if not path:
            return

        cols = {
            "vin": self.app.get_translation("tree_vin"),
            "owner": self.app.get_translation("tree_owner"),
            "vehicle_type": self.app.get_translation("tree_type"),
            "date_in": self.app.get_translation("tree_date_in"),
            "date_out": self.app.get_translation("tree_date_out"),
            "transport_vehicle": self.app.get_translation("tree_transport_vehicle"),
            "driver_name": self.app.get_translation("tree_driver"),
            "archived_at": "Ngày lưu trữ",
            "archived_by": "Người lưu trữ",
        }

        def worker():
            result = excel_generator.generate_excel_report(path, self._current_data, cols)
            def update_ui():
                if result.get("success"):
                    self.app.show_toast(self.app.get_translation("toast_export_archive_success"))
                else:
                    messagebox.showerror("Lỗi", result.get("message", ""), parent=self)
            self.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()