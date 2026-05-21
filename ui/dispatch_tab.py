# ui/dispatch_tab.py
import customtkinter as ctk
from tkinter import ttk, messagebox
from config import PAD_GENERAL, PAD_SMALL
from ui.components import style_treeview, add_right_click_menu, AutocompleteEntry  # === BỔ SUNG MỚI ===
from ui.camera_scanner import CameraScannerDialog

class DispatchTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.vehicle_manager = self.app.vehicle_manager
        self.entity_manager = self.app.entity_manager
        self.dispatch_manager = self.app.dispatch_manager

        self.driver_map = {}
        self.transport_map = {}
        self.current_dispatch_id = None

        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        creation_frame = ctk.CTkFrame(self.parent)
        creation_frame.grid(row=0, column=0, padx=PAD_GENERAL, pady=PAD_GENERAL, sticky="ew")
        creation_frame.grid_columnconfigure(1, weight=1)

        self.lbl_creation_title = ctk.CTkLabel(creation_frame, text="", font=self.app.font_bold)
        self.lbl_creation_title.grid(row=0, column=0, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")

        self.lbl_driver = ctk.CTkLabel(creation_frame, text="", font=self.app.font_normal)
        self.lbl_driver.grid(row=1, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        # === PHASE 2.5: AutocompleteEntry for driver ===
        self.driver_entry = AutocompleteEntry(
            creation_frame,
            suggestions=self._get_driver_suggestions,
            font=self.app.font_normal,
            placeholder_text=self.app.get_translation("autocomplete_driver_hint") if hasattr(self.app, 'get_translation') else ""
        )
        self.driver_entry.grid(row=1, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        add_right_click_menu(self.app, self.driver_entry.entry)

        self.lbl_transport = ctk.CTkLabel(creation_frame, text="", font=self.app.font_normal)
        self.lbl_transport.grid(row=2, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        # === PHASE 2.5: AutocompleteEntry for transport ===
        self.transport_entry = AutocompleteEntry(
            creation_frame,
            suggestions=self._get_transport_suggestions,
            font=self.app.font_normal,
            placeholder_text=self.app.get_translation("autocomplete_transport_hint") if hasattr(self.app, 'get_translation') else ""
        )
        self.transport_entry.grid(row=2, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        add_right_click_menu(self.app, self.transport_entry.entry)

        self.btn_create_dispatch = ctk.CTkButton(creation_frame, text="", command=self.create_dispatch, font=self.app.font_normal)
        self.btn_create_dispatch.grid(row=3, column=1, padx=PAD_SMALL, pady=PAD_GENERAL, sticky="e")

        current_dispatch_frame = ctk.CTkFrame(self.parent)
        current_dispatch_frame.grid(row=1, column=0, padx=PAD_GENERAL, pady=0, sticky="nsew")
        current_dispatch_frame.grid_columnconfigure(0, weight=1)
        current_dispatch_frame.grid_rowconfigure(2, weight=1)

        title_frame = ctk.CTkFrame(current_dispatch_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        self.lbl_current_dispatch_title = ctk.CTkLabel(title_frame, text="", font=self.app.font_bold)
        self.lbl_current_dispatch_title.grid(row=0, column=0, sticky="w")

        self.btn_cancel_dispatch = ctk.CTkButton(
            title_frame, text="", command=self.cancel_dispatch, 
            font=self.app.font_normal, fg_color="#D32F2F", hover_color="#B71C1C"
        )
        self.btn_cancel_dispatch.grid(row=0, column=1, sticky="e")

        add_vehicle_frame = ctk.CTkFrame(current_dispatch_frame, fg_color="transparent")
        add_vehicle_frame.grid(row=1, column=0, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        add_vehicle_frame.grid_columnconfigure(1, weight=1)

        self.lbl_add_vehicle = ctk.CTkLabel(add_vehicle_frame, text="", font=self.app.font_normal)
        self.lbl_add_vehicle.pack(side="left", padx=(0, PAD_SMALL))
        self.vin_entry = ctk.CTkEntry(add_vehicle_frame, font=self.app.font_normal)
        self.vin_entry.pack(side="left", fill="x", expand=True)
        self.vin_entry.bind("<Return>", self.add_vehicle_to_dispatch)
        add_right_click_menu(self.app, self.vin_entry) # === BỔ SUNG MỚI ===
        
        self.btn_open_camera = ctk.CTkButton(add_vehicle_frame, text="📷", width=30, command=self.open_camera_scanner)
        self.btn_open_camera.pack(side="left", padx=(PAD_SMALL, 0))

        cols = ("stt", "vin", "owner", "vehicle_type")
        self.tree = ttk.Treeview(current_dispatch_frame, columns=cols, show="headings")
        self.tree.grid(row=2, column=0, sticky="nsew", padx=PAD_SMALL, pady=PAD_SMALL)
        style_treeview(self.app, self.tree)
        self.tree.column("stt", width=50, anchor="center", stretch=False)
        self.tree.column("vin", width=200)
        self.tree.column("owner", width=150)
        self.tree.column("vehicle_type", width=120)

        self.btn_complete_dispatch = ctk.CTkButton(current_dispatch_frame, text="", command=self.complete_dispatch, font=self.app.font_normal)
        self.btn_complete_dispatch.grid(row=3, column=0, padx=PAD_SMALL, pady=PAD_GENERAL, sticky="e")

        self.update_language()

    # === PHASE 2.5: Autocomplete suggestions ===
    def _get_driver_suggestions(self):
        """Lấy danh sách tài xế cho gợi ý tự động."""
        try:
            drivers = self.entity_manager.get_all_active_drivers()
            return [d['name'] for d in drivers if d.get('name')]
        except Exception:
            return []
    
    def _get_transport_suggestions(self):
        """Lấy danh sách xe vận chuyển cho gợi ý tự động."""
        try:
            vehicles = self.entity_manager.get_all_active_transport_vehicles()
            return [v['license_plate'] for v in vehicles if v.get('license_plate')]
        except Exception:
            return []
    # === END PHASE 2.5 ===

    def update_language(self):
        self.lbl_creation_title.configure(text=self.app.get_translation("frame_create_dispatch"))
        self.lbl_driver.configure(text=self.app.get_translation("lbl_driver"))
        self.lbl_transport.configure(text=self.app.get_translation("lbl_transport_vehicle"))
        self.btn_create_dispatch.configure(text=self.app.get_translation("btn_create_dispatch"))
        self.lbl_add_vehicle.configure(text=self.app.get_translation("lbl_add_vehicle_to_dispatch"))
        self.vin_entry.configure(placeholder_text=self.app.get_translation("placeholder_scan_vin"))
        self.btn_complete_dispatch.configure(text=self.app.get_translation("btn_complete_dispatch"))
        self.btn_cancel_dispatch.configure(text=self.app.get_translation("btn_cancel_dispatch"))
        
        self.tree.heading("stt", text=self.app.get_translation("tree_stt"))
        self.tree.heading("vin", text=self.app.get_translation("tree_vin"))
        self.tree.heading("owner", text=self.app.get_translation("tree_owner"))
        self.tree.heading("vehicle_type", text=self.app.get_translation("tree_type"))
        
        self.load_open_dispatch()

    def open_camera_scanner(self):
        dialog = CameraScannerDialog(self.app)
        if dialog.result:
            self.vin_entry.delete(0, "end")
            self.vin_entry.insert(0, dialog.result)
            self.add_vehicle_to_dispatch()

    def update_dropdowns(self):
        # === PHASE 2.5: Cập nhật maps cho autocomplete ===
        drivers = self.entity_manager.get_all_active_drivers()
        self.driver_map = {d['name']: d['id'] for d in drivers}

        transport_vehicles = self.entity_manager.get_all_active_transport_vehicles()
        self.transport_map = {v['license_plate']: v['id'] for v in transport_vehicles}
        # === END PHASE 2.5 ===

    def load_open_dispatch(self):
        open_dispatches = self.dispatch_manager.get_open_dispatch_details()
        if open_dispatches:
            self.current_dispatch_id = list(open_dispatches.keys())[0]
            dispatch_details = open_dispatches[self.current_dispatch_id]
            
            title = self.app.get_translation("frame_current_dispatch_title").format(
                id=self.current_dispatch_id, 
                driver=dispatch_details['driver_name'], 
                vehicle=dispatch_details['license_plate']
            )
            self.lbl_current_dispatch_title.configure(text=title)
            
            self.update_vehicle_list(dispatch_details['vehicles'])
            self.vin_entry.configure(state="normal")
            self.btn_complete_dispatch.configure(state="normal")
            self.btn_create_dispatch.configure(state="disabled")
            self.btn_cancel_dispatch.configure(state="normal")
        else:
            self.reset_ui()

    def create_dispatch(self):
        # === PHASE 2.5: Sử dụng entry thay vì combo ===
        original_driver_name = self.driver_entry.get().strip()
        from data_normalizer import normalize_driver_name as _norm_name
        driver_name = _norm_name(original_driver_name)
        
        # Hiển thị toast cảnh báo sửa lỗi chính tả nếu có sự thay đổi
        if original_driver_name and driver_name != original_driver_name:
            self.app.show_toast(f"⚠️ Tự động sửa tài xế gõ sai từ '{original_driver_name}' thành '{driver_name}'")
            self.driver_entry.delete(0, "end")
            self.driver_entry.insert(0, driver_name)

        transport_plate = self.transport_entry.get().strip()

        if not driver_name or not transport_plate:
            messagebox.showwarning(self.app.get_translation("warn_missing_dispatch_info"), 
                                    self.app.get_translation("warn_missing_dispatch_info_msg"))
            return

        if driver_name not in self.driver_map:
            prompt = self.app.get_translation("prompt_add_new_driver").format(name=driver_name)
            if messagebox.askyesno("Xác nhận Thêm mới", prompt, parent=self.app):
                result = self.entity_manager.add_driver(driver_name, "", "", "Tự động thêm từ phiếu xuất")
                if not result["success"]:
                    messagebox.showerror("Lỗi", result["message"], parent=self.app)
                    return
                self.update_dropdowns()
            else:
                return
        
        if transport_plate not in self.transport_map:
            prompt = self.app.get_translation("prompt_add_new_transport").format(plate=transport_plate)
            if messagebox.askyesno("Xác nhận Thêm mới", prompt, parent=self.app):
                result = self.entity_manager.add_transport_vehicle(transport_plate, "", "Tự động thêm từ phiếu xuất")
                if not result["success"]:
                    messagebox.showerror("Lỗi", result["message"], parent=self.app)
                    return
                self.update_dropdowns()
            else:
                return
        
        driver_id = self.driver_map.get(driver_name)
        transport_id = self.transport_map.get(transport_plate)

        new_dispatch_id = self.dispatch_manager.create_dispatch(driver_id, transport_id)
        if new_dispatch_id:
            # Clear entries sau khi tạo thành công
            self.driver_entry.delete(0, "end")
            self.transport_entry.delete(0, "end")
            self.app.show_toast(self.app.get_translation("toast_dispatch_created").format(id=new_dispatch_id))
            self.load_open_dispatch()
        else:
            messagebox.showerror("Lỗi", "Không thể tạo phiếu xuất mới.")

    def add_vehicle_to_dispatch(self, event=None):
        vin = self.vin_entry.get().strip().upper()
        if not vin: return

        vehicle = self.vehicle_manager.find_vehicle_in_stock(vin)
        if not vehicle:
            messagebox.showwarning(self.app.get_translation("warn_not_in_stock_or_added"), 
                                   self.app.get_translation("warn_not_in_stock_or_added_msg").format(vin=vin))
            self.vin_entry.delete(0, "end")
            return
        
        self.dispatch_manager.add_vehicle_to_dispatch(vin, self.current_dispatch_id)
        self.app.show_toast(self.app.get_translation("toast_vehicle_added_to_shipment").format(vin=vin))
        self.vin_entry.delete(0, "end")
        self.load_open_dispatch()

    def cancel_dispatch(self):
        if not self.current_dispatch_id: return
        
        confirm_msg = self.app.get_translation("confirm_cancel_dispatch_msg").format(id=self.current_dispatch_id)
        if messagebox.askyesno(self.app.get_translation("confirm_cancel_dispatch_title"), confirm_msg, icon='warning', parent=self.app):
            result = self.dispatch_manager.cancel_dispatch(self.current_dispatch_id)
            if result["success"]:
                self.app.show_toast(result["message"])
                self.reset_ui()
                self.app.on_data_changed()
            else:
                messagebox.showerror("Lỗi", result["message"], parent=self.app)

    def complete_dispatch(self):
        if not self.current_dispatch_id: return
        
        confirm_msg = self.app.get_translation("confirm_complete_dispatch_msg").format(id=self.current_dispatch_id)
        if messagebox.askyesno(self.app.get_translation("confirm_complete_dispatch_title"), confirm_msg, icon='question', parent=self.app):
            result = self.dispatch_manager.complete_dispatch(self.current_dispatch_id)
            if result["success"]:
                self.app.show_toast(result["message"])
                self.reset_ui()
                self.app.on_data_changed()
            else:
                messagebox.showerror("Lỗi", result["message"], parent=self.app)

    def update_vehicle_list(self, vehicles):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for idx, vehicle in enumerate(vehicles, 1):
            self.tree.insert("", "end", values=(idx, vehicle['vin'], vehicle['owner'], vehicle['vehicle_type']))

    def reset_ui(self):
        self.current_dispatch_id = None
        self.lbl_current_dispatch_title.configure(text=self.app.get_translation("frame_current_dispatch_empty"))
        self.vin_entry.configure(state="disabled")
        self.btn_complete_dispatch.configure(state="disabled")
        self.btn_cancel_dispatch.configure(state="disabled")
        self.btn_create_dispatch.configure(state="normal")
        self.update_vehicle_list([])
        
        # === SỬA LỖI: Không gọi on_data_changed từ đây ===
        # self.app.on_data_changed() # Dòng này gây ra vòng lặp
        # Thay vào đó, chỉ cần cập nhật dropdown của chính nó
        self.update_dropdowns()
        # ============================================