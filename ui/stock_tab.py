# ui/stock_tab.py
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, Menu, simpledialog
from datetime import datetime
import logging
import threading
import math

from report_generators import excel_generator
import utils
from config import PAD_GENERAL, PAD_SMALL
from ui.components import EditVehicleDialog, DateRangeDialog, style_treeview, LocationSwapDialog, add_right_click_menu
from data_normalizer import normalizer

class StockTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.vehicle_manager = self.app.vehicle_manager
        self._search_job = None

        self.current_page = 1
        self.total_pages = 1
        self.items_per_page = 100

        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        filter_frame = ctk.CTkFrame(self.parent)
        filter_frame.grid(row=0, column=0, padx=PAD_GENERAL, pady=(PAD_GENERAL, PAD_SMALL), sticky="ew")
        filter_frame.grid_columnconfigure(1, weight=1)

        self.lbl_filter_owner = ctk.CTkLabel(filter_frame, text="", font=self.app.font_normal)
        self.lbl_filter_owner.grid(row=0, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        self.owner_filter_var = ctk.StringVar()
        self.owner_filter_combo = ctk.CTkComboBox(filter_frame, variable=self.owner_filter_var, command=self.update_stock_list, font=self.app.font_normal)
        self.owner_filter_combo.grid(row=0, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        add_right_click_menu(self.app, self.owner_filter_combo)

        self.lbl_search = ctk.CTkLabel(filter_frame, text="", font=self.app.font_normal)
        self.lbl_search.grid(row=1, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        self.search_entry = ctk.CTkEntry(filter_frame, font=self.app.font_normal)
        self.search_entry.grid(row=1, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)
        add_right_click_menu(self.app, self.search_entry)

        button_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=PAD_SMALL, sticky="w")
        self.btn_refresh = ctk.CTkButton(button_frame, text="", width=120, command=self.refresh_all, font=self.app.font_normal)
        self.btn_refresh.pack(side="left", padx=PAD_SMALL)

        self.export_menu_button = ctk.CTkButton(button_frame, text="", width=150, command=self._show_export_menu_command, font=self.app.font_normal)
        self.export_menu_button.pack(side="left", padx=PAD_SMALL)
        self.export_menu = Menu(self.export_menu_button, tearoff=0, font=("Arial", 12))

        list_frame = ctk.CTkFrame(self.parent)
        list_frame.grid(row=1, column=0, padx=PAD_GENERAL, pady=(PAD_SMALL, 0), sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        cols = ("stt", "vin", "vehicle_type", "owner", "location", "date_in")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        style_treeview(self.app, self.tree)
        
        self.tree.column("stt", width=50, anchor="center", stretch=False)
        self.tree.column("vin", width=200)
        self.tree.column("vehicle_type", width=120)
        self.tree.column("owner", width=150)
        self.tree.column("location", width=120, anchor="center")
        self.tree.column("date_in", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Button-3>", self.show_context_menu)
        self.context_menu = Menu(self.tree, tearoff=0, font=("Arial", 12))
        
        pagination_frame = ctk.CTkFrame(self.parent)
        pagination_frame.grid(row=2, column=0, padx=PAD_GENERAL, pady=(0, PAD_GENERAL), sticky="ew")
        pagination_frame.grid_columnconfigure(1, weight=1)

        # === CẬP NHẬT: Sử dụng key dịch thuật ===
        self.btn_prev_page = ctk.CTkButton(pagination_frame, text=self.app.get_translation("pagination_prev"), command=self.prev_page, font=self.app.font_normal)
        self.btn_prev_page.grid(row=0, column=0, padx=10)

        self.page_label = ctk.CTkLabel(pagination_frame, text="", font=self.app.font_normal)
        self.page_label.grid(row=0, column=1, pady=5)

        self.btn_next_page = ctk.CTkButton(pagination_frame, text=self.app.get_translation("pagination_next"), command=self.next_page, font=self.app.font_normal)
        self.btn_next_page.grid(row=0, column=2, padx=10)
        # ========================================
        self.update_language()
        self.app.bind("<F5>", lambda event: self.refresh_all())

    def _show_export_menu_command(self):
        x = self.export_menu_button.winfo_rootx()
        y = self.export_menu_button.winfo_rooty()
        height = self.export_menu_button.winfo_height()
        self.export_menu.tk_popup(x, y + height)

    def update_language(self):
        self.lbl_filter_owner.configure(text=self.app.get_translation("lbl_filter_owner"))
        self.lbl_search.configure(text=self.app.get_translation("lbl_search_vin_owner"))
        self.search_entry.configure(placeholder_text=self.app.get_translation("lbl_search_vin_owner"))
        self.btn_refresh.configure(text=self.app.get_translation("btn_refresh"))
        self.export_menu_button.configure(text=self.app.get_translation("btn_export_reports"))
        
        self.export_menu.delete(0, "end")
        self.export_menu.add_command(label=self.app.get_translation("menu_export_stock"), command=self.export_stock)
        self.export_menu.add_command(label=self.app.get_translation("menu_export_summary"), command=self.export_summary)
        self.export_menu.add_command(label=self.app.get_translation("menu_export_history"), command=self.app.prompt_for_history_export)

        self.tree.heading("stt", text=self.app.get_translation("tree_stt"))
        self.tree.heading("vin", text=self.app.get_translation("tree_vin"))
        self.tree.heading("vehicle_type", text=self.app.get_translation("tree_type"))
        self.tree.heading("owner", text=self.app.get_translation("tree_owner"))
        self.tree.heading("location", text=self.app.get_translation("tree_location"))
        self.tree.heading("date_in", text=self.app.get_translation("tree_date_in"))

        self.context_menu.delete(0, "end")
        self.context_menu.add_command(label=self.app.get_translation("ctx_menu_edit"), command=self.edit_selected_vehicle)
        self.context_menu.add_command(label=self.app.get_translation("ctx_menu_swap_location"), command=self.swap_selected_vehicle_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.app.get_translation("ctx_menu_delete"), command=self.delete_selected_vehicle)
        # === CẬP NHẬT: Cập nhật lại text cho các nút phân trang khi đổi ngôn ngữ ===
        self.btn_prev_page.configure(text=self.app.get_translation("pagination_prev"))
        self.btn_next_page.configure(text=self.app.get_translation("pagination_next"))
        # Cập nhật lại label trang nếu nó đã có nội dung
        if self.total_pages > 0:
            self.page_label.configure(text=self.app.get_translation("pagination_page_info").format(current=self.current_page, total=self.total_pages))
        # ========================================================================
        
        self.update_owner_filter_options()

    def refresh_all(self):
        self.search_entry.delete(0, "end")
        self.update_owner_filter_options()
        self.current_page = 1
        self.update_stock_list()

    def _on_search_key_release(self, event):
        if self._search_job:
            self.parent.after_cancel(self._search_job)
        self._search_job = self.parent.after(500, lambda: self.update_stock_list(event="search"))

    def update_stock_list(self, event=None):
        if event:
            self.current_page = 1

        self.app.status_var.set(self.app.get_translation("status_loading"))
        
        owner_filter = self.owner_filter_var.get()
        search_term = self.search_entry.get().strip()
        
        threading.Thread(
            target=self._load_stock_data_background,
            args=(owner_filter, search_term),
            daemon=True
        ).start()

    def _load_stock_data_background(self, owner_filter, search_term):
        if owner_filter == self.app.get_translation("combobox_all"):
            owner_filter = None
        if not search_term:
            search_term = None
        
        total_items = self.vehicle_manager.get_in_stock_count(owner_filter=owner_filter, search_term=search_term)
        self.total_pages = math.ceil(total_items / self.items_per_page)
        if self.total_pages == 0: self.total_pages = 1

        offset = (self.current_page - 1) * self.items_per_page
            
        stock_data = self.vehicle_manager.get_in_stock(
            owner_filter=owner_filter, 
            search_term=search_term,
            limit=self.items_per_page,
            offset=offset
        )
        if self.parent.winfo_exists():
            self.app.after(0, self._update_treeview_data, stock_data, total_items)

    def _update_treeview_data(self, stock_data, total_items):
        if not self.parent.winfo_exists(): return
        
        for i in self.tree.get_children():
            self.tree.delete(i)

        offset = (self.current_page - 1) * self.items_per_page
        for idx, row in enumerate(stock_data, 1):
            stt = offset + idx
            date_in_str = utils.format_datetime_for_display(row["date_in"])
            location_name = row.get("full_location_name", "N/A")
            self.tree.insert("", "end", values=(stt, row["vin"], row["vehicle_type"], row["owner"], location_name, date_in_str))

        status_text = self.app.get_translation("status_stock_count").format(count=total_items)
        self.app.status_var.set(status_text)
        
        self.page_label.configure(text=f"Trang {self.current_page} / {self.total_pages}")
        # === CẬP NHẬT: Sử dụng key dịch thuật ===
        self.page_label.configure(text=self.app.get_translation("pagination_page_info").format(current=self.current_page, total=self.total_pages))
        # ========================================  
        self.btn_prev_page.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next_page.configure(state="normal" if self.current_page < self.total_pages else "disabled")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_stock_list()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_stock_list()

    def update_owner_filter_options(self):
        all_text = self.app.get_translation("combobox_all")
        owners = [all_text] + self.vehicle_manager.get_distinct_owners()
        current_val = self.owner_filter_var.get()
        self.owner_filter_combo.configure(values=owners)
        if current_val not in owners:
            self.owner_filter_combo.set(all_text)

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def get_selected_vin(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return None
        item = self.tree.item(selected_items[0])
        return item['values'][1]

    def edit_selected_vehicle(self):
        vin = self.get_selected_vin()
        if not vin:
            messagebox.showwarning(self.app.get_translation("warn_no_selection"), self.app.get_translation("warn_no_selection_msg"))
            return

        vehicle_info = self.vehicle_manager.get_vehicle_by_vin(vin)
        if not vehicle_info:
            messagebox.showerror("Lỗi", f"Không tìm thấy thông tin cho xe có VIN: {vin}")
            return

        dialog = EditVehicleDialog(self.app, vehicle_info)
        if dialog.result:
            res = dialog.result
            new_owner = normalizer.normalize_owner(res["owner"])
            new_type = normalizer.normalize_vehicle_type(res["vehicle_type"])
            
            if not new_owner:
                messagebox.showwarning(self.app.get_translation("warn_missing_info"), self.app.get_translation("warn_missing_info_msg"))
                return

            if res["original_vin"] != res["new_vin"]:
                result = self.vehicle_manager.update_vin(res["original_vin"], res["new_vin"], new_owner, new_type)
            else:
                result = self.vehicle_manager.update_vehicle_details(vin, new_owner, new_type)

            if result["success"]:
                self.app.show_toast("Cập nhật thông tin xe thành công!")
                self.update_stock_list()
            else:
                messagebox.showerror("Lỗi", f"Không thể cập nhật thông tin xe:\n{result['message']}")

    def swap_selected_vehicle_location(self):
        vin = self.get_selected_vin()
        if not vin:
            messagebox.showwarning(self.app.get_translation("warn_no_selection"), self.app.get_translation("warn_no_selection_msg"))
            return

        vehicle_info = self.vehicle_manager.get_vehicle_by_vin(vin)
        if not vehicle_info:
            messagebox.showerror("Lỗi", f"Không tìm thấy thông tin cho xe có VIN: {vin}")
            return
        
        dialog = LocationSwapDialog(self.app, vehicle_info, self.app.location_manager)
        if dialog.result:
            self.update_stock_list()

    def delete_selected_vehicle(self):
        vin = self.get_selected_vin()
        if not vin:
            messagebox.showwarning(self.app.get_translation("warn_no_selection"), self.app.get_translation("warn_no_selection_msg"))
            return

        confirm_msg = self.app.get_translation("confirm_delete_msg").format(item=vin)
        if messagebox.askyesno(self.app.get_translation("confirm_delete_title"), confirm_msg, icon='warning'):
            result = self.vehicle_manager.soft_delete_vehicle(vin)
            if result["success"]:
                self.app.show_toast("Đã xóa xe thành công.")
                self.app.on_data_changed()
            else:
                messagebox.showerror("Lỗi", f"Không thể xóa xe: {result['message']}")

    def _run_export_in_thread(self, export_function, *args):
        self.app.status_var.set(self.app.get_translation("status_exporting"))
        
        def worker():
            result = export_function(*args)
            def update_ui():
                if not self.parent.winfo_exists(): return
                if result["success"]: self.app.show_toast(self.app.get_translation("toast_export_success"))
                else: messagebox.showerror("Lỗi Xuất File", result["message"])
                self.app.status_var.set(self.app.get_translation("status_ready"))
            
            if self.parent.winfo_exists():
                self.app.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def export_stock(self):
        highlight_days_str = simpledialog.askstring(
            self.app.get_translation("dialog_conditional_formatting_title"),
            self.app.get_translation("dialog_conditional_formatting_prompt"),
            parent=self.app
        )
        if highlight_days_str is None: return
        
        highlight_threshold = None
        if highlight_days_str:
            try: highlight_threshold = int(highlight_days_str)
            except ValueError:
                messagebox.showwarning("Lỗi", "Vui lòng nhập một con số.", parent=self.app)
                return
        
        default_name = utils.get_default_filename(self.app.get_translation("menu_export_stock"), ".xlsx")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile=default_name)
        if not path: return

        def do_export(file_path, threshold):
            data = self.vehicle_manager.get_in_stock(limit=-1) # Lấy tất cả dữ liệu để export
            cols = {
                "vin": self.app.get_translation("tree_vin"),
                "owner": self.app.get_translation("tree_owner"),
                "vehicle_type": self.app.get_translation("tree_type"),
                "full_location_name": self.app.get_translation("tree_location"),
                "date_in": self.app.get_translation("tree_date_in"),
                "days_in_stock": self.app.get_translation("excel_days_in_stock")
            }
            highlight_config = {"threshold": threshold, "column_name": self.app.get_translation("excel_days_in_stock")}
            return excel_generator.generate_excel_report(file_path, data, cols, highlight_config=highlight_config)

        self._run_export_in_thread(do_export, path, highlight_threshold)

    def export_summary(self):
        dialog = DateRangeDialog(self.app, title=self.app.get_translation("menu_export_summary"))
        if not dialog.result: return
        start_date, end_date = dialog.result
        
        default_name = utils.get_default_filename(self.app.get_translation("report_dispatch_summary"), ".xlsx")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile=default_name)
        if not path: return

        def do_export(file_path, start, end):
            data = self.app.api_client.get_export_summary(start, end)
            total_row = None
            if data:
                total_in = sum(item['total_in'] for item in data)
                total_out = sum(item['total_out'] for item in data)
                total_stock = sum(item['stock'] for item in data)
                total_row = {'owner': self.app.get_translation('pdf_total_row'), 'total_in': total_in, 'total_out': total_out, 'stock': total_stock}
            cols = {"owner": self.app.get_translation("tree_owner"), "total_in": self.app.get_translation("pdf_col_total_in"), "total_out": self.app.get_translation("pdf_col_total_out"), "stock": self.app.get_translation("pdf_col_stock")}
            return excel_generator.generate_excel_report(file_path, data, cols, total_row)

        self._run_export_in_thread (do_export, path, start_date, end_date)
