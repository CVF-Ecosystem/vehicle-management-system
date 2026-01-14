# ui/search_tab.py
"""
Advanced Search Tab - Phase 2.1
Tab tìm kiếm nâng cao với filter theo trạng thái, ngày, block.
"""
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import threading
import utils
from config import STATUS_SHIPPED
from ui.components import style_treeview, add_right_click_menu, AutocompleteEntry, harmonize_combobox_style
from ui.vehicle_timeline_dialog import VehicleTimelineDialog


class SearchTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.vehicle_manager = self.app.vehicle_manager
        self.location_manager = self.app.location_manager

        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        # === SEARCH FRAME ===
        search_frame = ctk.CTkFrame(self.parent)
        search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        search_frame.grid_columnconfigure((1, 3, 5), weight=1)

        # Title
        self.lbl_title = ctk.CTkLabel(search_frame, text="", font=self.app.font_bold)
        self.lbl_title.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky="w")

        # Row 1: VIN, Owner, Type
        self.lbl_vin = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_vin.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # === PHASE 2.5: AutocompleteEntry for VIN ===
        self.vin_entry = AutocompleteEntry(
            search_frame, 
            suggestions=self._get_vin_suggestions,
            show_dropdown_button=False,
            font=self.app.font_normal
        )
        self.vin_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.vin_entry.entry)

        self.lbl_owner = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_owner.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        # === PHASE 2.5: AutocompleteEntry for Owner ===
        self.owner_entry = AutocompleteEntry(
            search_frame,
            suggestions=self._get_owner_suggestions,
            font=self.app.font_normal
        )
        self.owner_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.owner_entry.entry)
        # === END PHASE 2.5 ===

        self.lbl_type = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_type.grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.type_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.type_entry.grid(row=1, column=5, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.type_entry)

        # Row 2: Transport, Driver, Status
        self.lbl_transport = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_transport.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.transport_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.transport_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.transport_entry)

        self.lbl_driver = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_driver.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.driver_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.driver_entry.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.driver_entry)

        self.lbl_status = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_status.grid(row=2, column=4, padx=5, pady=5, sticky="w")
        # Map internal values to display values
        self.status_map = {"all": "all", "in_stock": "in_stock", "shipped": "shipped"}
        self.status_var = ctk.StringVar(value="all")
        self.status_combo = ctk.CTkComboBox(
            search_frame, 
            values=["all", "in_stock", "shipped"],  # Will be updated in update_language
            variable=self.status_var,
            font=self.app.font_normal,
            state="readonly"
        )
        self.status_combo.grid(row=2, column=5, padx=5, pady=5, sticky="ew")
        harmonize_combobox_style(self.status_combo)

        # Row 3: Date Filter, Date From, Date To, Block
        self.lbl_date_field = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_date_field.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.date_field_map = {"date_in": "date_in", "date_out": "date_out"}
        self.date_field_var = ctk.StringVar(value="date_in")
        self.date_field_combo = ctk.CTkComboBox(
            search_frame,
            values=["date_in", "date_out"],  # Will be updated in update_language
            variable=self.date_field_var,
            font=self.app.font_normal,
            state="readonly",
            width=120
        )
        self.date_field_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        harmonize_combobox_style(self.date_field_combo)

        # Date From
        date_from_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        date_from_frame.grid(row=3, column=2, padx=5, pady=5, sticky="ew")
        self.lbl_from_date = ctk.CTkLabel(date_from_frame, text="", font=self.app.font_normal)
        self.lbl_from_date.pack(side="left", padx=(0, 5))
        self.date_from_entry = DateEntry(
            date_from_frame, 
            date_pattern='yyyy-mm-dd',
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2
        )
        self.date_from_entry.pack(side="left")
        self.date_from_entry.delete(0, "end")  # Clear default date

        # Date To
        date_to_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        date_to_frame.grid(row=3, column=3, padx=5, pady=5, sticky="ew")
        self.lbl_to_date = ctk.CTkLabel(date_to_frame, text="", font=self.app.font_normal)
        self.lbl_to_date.pack(side="left", padx=(0, 5))
        self.date_to_entry = DateEntry(
            date_to_frame,
            date_pattern='yyyy-mm-dd',
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2
        )
        self.date_to_entry.pack(side="left")
        self.date_to_entry.delete(0, "end")  # Clear default date

        # Block filter
        self.lbl_block = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_block.grid(row=3, column=4, padx=5, pady=5, sticky="w")
        self.block_var = ctk.StringVar(value=self.app.get_translation("status_all") or "Tất cả")
        self.block_combo = ctk.CTkComboBox(
            search_frame,
            values=[self.app.get_translation("status_all") or "Tất cả"],
            variable=self.block_var,
            font=self.app.font_normal,
            state="readonly"
        )
        self.block_combo.grid(row=3, column=5, padx=5, pady=5, sticky="ew")
        harmonize_combobox_style(self.block_combo)

        # Row 4: Buttons
        btn_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=6, padx=5, pady=10, sticky="e")

        self.btn_clear = ctk.CTkButton(
            btn_frame, 
            text="", 
            command=self.clear_filters,
            font=self.app.font_normal,
            fg_color="#757575",
            hover_color="#616161",
            width=100
        )
        self.btn_clear.pack(side="left", padx=5)

        self.btn_search = ctk.CTkButton(
            btn_frame, 
            text="", 
            command=self.perform_search, 
            font=self.app.font_normal,
            width=120
        )
        self.btn_search.pack(side="left", padx=5)

        # === RESULT FRAME ===
        result_frame = ctk.CTkFrame(self.parent)
        result_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        cols = ("stt", "vin", "owner", "vehicle_type", "status", "location", "date_in", "date_out", "transport", "driver")
        self.tree = ttk.Treeview(result_frame, columns=cols, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        style_treeview(self.app, self.tree)

        self.tree.column("stt", width=40, anchor="center", stretch=False)
        self.tree.column("vin", width=150)
        self.tree.column("owner", width=120)
        self.tree.column("vehicle_type", width=100)
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("location", width=100, anchor="center")
        self.tree.column("date_in", width=120, anchor="center")
        self.tree.column("date_out", width=120, anchor="center")
        self.tree.column("transport", width=100)
        self.tree.column("driver", width=120)

        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind Enter key to search
        self.vin_entry.bind("<Return>", lambda e: self.perform_search())
        self.owner_entry.bind("<Return>", lambda e: self.perform_search())
        self.type_entry.bind("<Return>", lambda e: self.perform_search())
        self.transport_entry.bind("<Return>", lambda e: self.perform_search())
        self.driver_entry.bind("<Return>", lambda e: self.perform_search())
        
        # Bind double-click to show timeline
        self.tree.bind("<Double-1>", self._on_double_click)

        self._load_blocks()
        self.update_language()

    # === PHASE 2.5: Autocomplete suggestion methods ===
    def _get_vin_suggestions(self):
        """Lấy danh sách VIN cho gợi ý tự động."""
        try:
            vehicles = self.vehicle_manager.get_all_vehicles()
            return [v['vin'] for v in vehicles if v.get('vin')]
        except Exception:
            return []
    
    def _get_owner_suggestions(self):
        """Lấy danh sách chủ hàng cho gợi ý tự động."""
        return self.vehicle_manager.get_distinct_owners()
    # === END PHASE 2.5 ===

    def _load_blocks(self):
        """Load danh sách blocks vào combo box."""
        try:
            blocks = self.location_manager.get_all_blocks()
            all_display = self.app.get_translation("status_all") or "Tất cả"
            block_values = [all_display] + blocks
            self.block_combo.configure(values=block_values)
            # Ensure selection is valid
            if self.block_combo.get() not in block_values:
                self.block_combo.set(all_display)
        except Exception:
            pass

    def _get_block_internal_value(self) -> str:
        """Map block display value back to internal value for search."""
        display = (self.block_combo.get() or "").strip()
        all_display = (self.app.get_translation("status_all") or "Tất cả").strip()
        if not display or display == all_display:
            return ""
        return display

    def clear_filters(self):
        """Xóa tất cả filters."""
        self.vin_entry.delete(0, "end")
        self.owner_entry.delete(0, "end")
        self.type_entry.delete(0, "end")
        self.transport_entry.delete(0, "end")
        self.driver_entry.delete(0, "end")
        # Reset combos to first value (translated)
        self.status_combo.set(self.app.get_translation("status_all"))
        self.date_field_combo.set(self.app.get_translation("date_field_date_in"))
        self.date_from_entry.delete(0, "end")
        self.date_to_entry.delete(0, "end")
        self.block_combo.set(self.app.get_translation("status_all") or "Tất cả")
        
        # Clear results
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.app.status_var.set(self.app.get_translation("status_ready"))

    def update_language(self):
        self.lbl_title.configure(text=self.app.get_translation("frame_advanced_search"))
        self.lbl_vin.configure(text=self.app.get_translation("lbl_vin"))
        self.lbl_owner.configure(text=self.app.get_translation("lbl_owner"))
        self.lbl_type.configure(text=self.app.get_translation("lbl_vehicle_type"))
        self.lbl_transport.configure(text=self.app.get_translation("lbl_transport_vehicle"))
        self.lbl_driver.configure(text=self.app.get_translation("lbl_driver"))
        self.lbl_status.configure(text=self.app.get_translation("lbl_status"))
        self.lbl_date_field.configure(text=self.app.get_translation("lbl_date_filter"))
        self.lbl_from_date.configure(text=self.app.get_translation("lbl_from_date"))
        self.lbl_to_date.configure(text=self.app.get_translation("lbl_to_date"))
        self.lbl_block.configure(text=self.app.get_translation("lbl_block"))
        self.btn_search.configure(text=self.app.get_translation("btn_search"))
        self.btn_clear.configure(text=self.app.get_translation("btn_clear_filters"))

        # Update combo box display values
        current_status = self.status_var.get()
        status_display = [
            self.app.get_translation("status_all"),
            self.app.get_translation("status_in_stock"),
            self.app.get_translation("status_shipped")
        ]
        self.status_combo.configure(values=status_display)
        # Restore selection by index
        status_index = {"all": 0, "in_stock": 1, "shipped": 2}.get(current_status, 0)
        self.status_combo.set(status_display[status_index])
        
        current_date_field = self.date_field_var.get()
        date_field_display = [
            self.app.get_translation("date_field_date_in"),
            self.app.get_translation("date_field_date_out")
        ]
        self.date_field_combo.configure(values=date_field_display)
        date_field_index = {"date_in": 0, "date_out": 1}.get(current_date_field, 0)
        self.date_field_combo.set(date_field_display[date_field_index])

        self.tree.heading("stt", text=self.app.get_translation("tree_stt"))
        self.tree.heading("vin", text=self.app.get_translation("tree_vin"))
        self.tree.heading("owner", text=self.app.get_translation("tree_owner"))
        self.tree.heading("vehicle_type", text=self.app.get_translation("tree_type"))
        self.tree.heading("status", text=self.app.get_translation("tree_status"))
        self.tree.heading("location", text=self.app.get_translation("tree_location"))
        self.tree.heading("date_in", text=self.app.get_translation("tree_date_in"))
        self.tree.heading("date_out", text=self.app.get_translation("tree_date_out"))
        self.tree.heading("transport", text=self.app.get_translation("tree_transport_vehicle"))
        self.tree.heading("driver", text=self.app.get_translation("tree_driver"))

        # Refresh block list so the first option shows translated "All" (instead of blank).
        self._load_blocks()

    def _get_status_internal_value(self):
        """Chuyển đổi giá trị hiển thị của status combo về giá trị internal."""
        current_display = self.status_combo.get()
        status_all = self.app.get_translation("status_all")
        status_in_stock = self.app.get_translation("status_in_stock")
        status_shipped = self.app.get_translation("status_shipped")
        
        if current_display == status_in_stock:
            return "in_stock"
        elif current_display == status_shipped:
            return "shipped"
        else:
            return "all"
    
    def _get_date_field_internal_value(self):
        """Chuyển đổi giá trị hiển thị của date field combo về giá trị internal."""
        current_display = self.date_field_combo.get()
        date_in_display = self.app.get_translation("date_field_date_in")
        
        if current_display == date_in_display:
            return "date_in"
        else:
            return "date_out"

    def perform_search(self):
        """Bắt đầu quá trình tìm kiếm trong một luồng riêng."""
        self.app.status_var.set(self.app.get_translation("status_loading"))
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Get date values
        date_from = self.date_from_entry.get().strip()
        date_to = self.date_to_entry.get().strip()

        vin_query = (self.vin_entry.get() or "").strip().upper()

        # VIN is the most reliable identifier. If VIN is provided, search by VIN only
        # to avoid false negatives caused by mismatched/incorrect data-entry fields.
        if vin_query:
            search_params = {
                "vin": vin_query,
                "owner": "",
                "vehicle_type": "",
                "transport": "",
                "driver": "",
                "status_filter": "all",
                "date_from": "",
                "date_to": "",
                "date_field": self._get_date_field_internal_value(),
                "block": "",
            }
        else:
            search_params = {
                "vin": "",
                "owner": (self.owner_entry.get() or "").strip(),
                "vehicle_type": (self.type_entry.get() or "").strip(),
                "transport": (self.transport_entry.get() or "").strip(),
                "driver": (self.driver_entry.get() or "").strip(),
                "status_filter": self._get_status_internal_value(),
                "date_from": date_from,
                "date_to": date_to,
                "date_field": self._get_date_field_internal_value(),
                "block": self._get_block_internal_value(),
            }

        threading.Thread(
            target=self._search_background,
            args=(search_params,),
            daemon=True
        ).start()

    def _search_background(self, search_params):
        """Thực hiện truy vấn CSDL trong luồng nền."""
        results = self.vehicle_manager.search_all_vehicles(**search_params)
        if self.parent.winfo_exists():
            self.app.after(0, self._update_search_results, results)

    def _update_search_results(self, results):
        """Cập nhật Treeview với kết quả tìm kiếm trên luồng chính."""
        if not self.parent.winfo_exists(): 
            return

        for idx, row in enumerate(results, 1):
            date_in_str = utils.format_datetime_for_display(row.get("date_in"))
            date_out_str = utils.format_datetime_for_display(row.get("date_out"))
            status_str = self.app.get_translation("status_shipped") if row["status"] == STATUS_SHIPPED else self.app.get_translation("status_in_stock")
            location_name = row.get("full_location_name", "")

            self.tree.insert("", "end", values=(
                idx, 
                row.get("vin", ""), 
                row.get("owner", ""), 
                row.get("vehicle_type", ""), 
                status_str,
                location_name, 
                date_in_str, 
                date_out_str, 
                row.get("transport_vehicle", ""), 
                row.get("driver_name", "")
            ))
        
        status_text = self.app.get_translation("status_search_result").format(count=len(results))
        self.app.status_var.set(status_text)

    def _on_double_click(self, event):
        """Handle double-click on search result to show vehicle timeline."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item.get("values", [])
        if len(values) >= 2:
            vin = values[1]  # VIN is second column
            if vin:
                lang = getattr(self.app, 'current_language', 'vi')
                VehicleTimelineDialog(self.app, vin, self.vehicle_manager, lang)