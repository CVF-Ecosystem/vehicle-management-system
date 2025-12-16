# ui/search_tab.py
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
import threading
import utils
from config import STATUS_SHIPPED
from ui.components import style_treeview, add_right_click_menu # === BỔ SUNG MỚI ===

class SearchTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.vehicle_manager = self.app.vehicle_manager

        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        search_frame = ctk.CTkFrame(self.parent)
        search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        search_frame.grid_columnconfigure((1, 3), weight=1)

        self.lbl_title = ctk.CTkLabel(search_frame, text="", font=self.app.font_bold)
        self.lbl_title.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="w")

        self.lbl_vin = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_vin.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.vin_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.vin_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.vin_entry) # === BỔ SUNG MỚI ===

        self.lbl_owner = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_owner.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.owner_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.owner_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.owner_entry) # === BỔ SUNG MỚI ===

        self.lbl_type = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_type.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.type_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.type_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.type_entry) # === BỔ SUNG MỚI ===

        self.lbl_transport = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_transport.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.transport_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.transport_entry.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.transport_entry) # === BỔ SUNG MỚI ===

        self.lbl_driver = ctk.CTkLabel(search_frame, text="", font=self.app.font_normal)
        self.lbl_driver.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.driver_entry = ctk.CTkEntry(search_frame, font=self.app.font_normal)
        self.driver_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, self.driver_entry) # === BỔ SUNG MỚI ===

        self.btn_search = ctk.CTkButton(search_frame, text="", command=self.perform_search, font=self.app.font_normal)
        self.btn_search.grid(row=3, column=3, padx=5, pady=10, sticky="e")

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
        
        self.update_language()

    def update_language(self):
        self.lbl_title.configure(text=self.app.get_translation("frame_global_search"))
        self.lbl_vin.configure(text=self.app.get_translation("lbl_vin"))
        self.lbl_owner.configure(text=self.app.get_translation("lbl_owner"))
        self.lbl_type.configure(text=self.app.get_translation("lbl_vehicle_type"))
        self.lbl_transport.configure(text=self.app.get_translation("lbl_transport_vehicle"))
        self.lbl_driver.configure(text=self.app.get_translation("lbl_driver"))
        self.btn_search.configure(text=self.app.get_translation("btn_search"))

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

    def perform_search(self):
        """Bắt đầu quá trình tìm kiếm trong một luồng riêng."""
        self.app.status_var.set(self.app.get_translation("status_loading"))
        for i in self.tree.get_children():
            self.tree.delete(i)

        search_params = {
            "vin": self.vin_entry.get().strip(),
            "owner": self.owner_entry.get().strip(),
            "vehicle_type": self.type_entry.get().strip(),
            "transport": self.transport_entry.get().strip(),
            "driver": self.driver_entry.get().strip()
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
        if not self.parent.winfo_exists(): return

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