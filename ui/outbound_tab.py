# ui/outbound_tab.py
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import logging
from config import PAD_GENERAL, PAD_SMALL
from ui.camera_scanner import CameraScannerDialog
from ui.components import add_right_click_menu, AutocompleteEntry  # === BỔ SUNG MỚI ===

class OutboundTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.vehicle_manager = self.app.vehicle_manager
        self.entity_manager = self.app.entity_manager
        self.location_manager = self.app.location_manager

        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)
        
        outbound_frame = ctk.CTkFrame(self.parent)
        outbound_frame.grid(row=0, column=0, padx=PAD_GENERAL, pady=(PAD_GENERAL, PAD_SMALL), sticky="ew")
        outbound_frame.grid_columnconfigure(1, weight=1)
        
        self.lbl_outbound_info = ctk.CTkLabel(outbound_frame, text="", font=self.app.font_bold)
        self.lbl_outbound_info.grid(row=0, column=0, columnspan=2, padx=PAD_SMALL, pady=(PAD_SMALL, PAD_GENERAL), sticky="w")
        
        self.lbl_scan_qr = ctk.CTkLabel(outbound_frame, text="", font=self.app.font_normal)
        self.lbl_scan_qr.grid(row=1, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        
        scan_frame = ctk.CTkFrame(outbound_frame, fg_color="transparent")
        scan_frame.grid(row=1, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        scan_frame.grid_columnconfigure(0, weight=1)

        # === PHASE 2.5: AutocompleteEntry for VIN ===
        self.scan_entry = AutocompleteEntry(
            scan_frame,
            suggestions=self._get_vin_suggestions,
            font=self.app.font_normal,
            placeholder_text=self.app.get_translation("autocomplete_vin_hint") if hasattr(self.app, 'get_translation') else ""
        )
        self.scan_entry.grid(row=0, column=0, sticky="ew")
        self.scan_entry.bind("<Return>", self.process_out)
        add_right_click_menu(self.app, self.scan_entry.entry)

        self.btn_open_camera = ctk.CTkButton(scan_frame, text="📷", width=30, command=self.open_camera_scanner)
        self.btn_open_camera.grid(row=0, column=1, padx=(PAD_SMALL, 0))
        
        self.lbl_transport = ctk.CTkLabel(outbound_frame, text="", font=self.app.font_normal)
        self.lbl_transport.grid(row=2, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        # === PHASE 2.5: AutocompleteEntry for transport ===
        self.transport_entry = AutocompleteEntry(
            outbound_frame,
            suggestions=self._get_transport_suggestions,
            font=self.app.font_normal,
            placeholder_text=self.app.get_translation("autocomplete_transport_hint") if hasattr(self.app, 'get_translation') else ""
        )
        self.transport_entry.grid(row=2, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        add_right_click_menu(self.app, self.transport_entry.entry)
        
        self.lbl_driver = ctk.CTkLabel(outbound_frame, text="", font=self.app.font_normal)
        self.lbl_driver.grid(row=3, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        # === PHASE 2.5: AutocompleteEntry for driver ===
        self.driver_entry = AutocompleteEntry(
            outbound_frame,
            suggestions=self._get_driver_suggestions,
            font=self.app.font_normal,
            placeholder_text=self.app.get_translation("autocomplete_driver_hint") if hasattr(self.app, 'get_translation') else ""
        )
        self.driver_entry.grid(row=3, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        add_right_click_menu(self.app, self.driver_entry.entry)
        
        self.btn_process_out = ctk.CTkButton(outbound_frame, text="", command=self.process_out, font=self.app.font_normal)
        self.btn_process_out.grid(row=4, column=0, pady=PAD_GENERAL, padx=PAD_SMALL, sticky="w")
        
        log_frame = ctk.CTkFrame(self.parent)
        log_frame.grid(row=1, column=0, padx=PAD_GENERAL, pady=(PAD_SMALL, PAD_GENERAL), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        self.outbound_log_text = ctk.CTkTextbox(log_frame, wrap="word", state="disabled", font=("Courier New", 12))
        self.outbound_log_text.grid(row=0, column=0, sticky="nsew")
        self.outbound_log_text.tag_config("error", foreground="red")
        self.outbound_log_text.tag_config("success", foreground="green")
        add_right_click_menu(self.app, self.outbound_log_text) # === BỔ SUNG MỚI ===

        self.update_language()
        self.update_dropdowns()

    def update_language(self):
        self.lbl_outbound_info.configure(text=self.app.get_translation("frame_outbound_info"))
        self.lbl_scan_qr.configure(text=self.app.get_translation("lbl_scan_qr"))
        self.lbl_transport.configure(text=self.app.get_translation("lbl_transport_vehicle"))
        self.lbl_driver.configure(text=self.app.get_translation("lbl_driver"))
        self.btn_process_out.configure(text=self.app.get_translation("btn_process_dispatch"))

    # === PHASE 2.5: Autocomplete suggestions ===
    def _get_vin_suggestions(self):
        """Lấy danh sách VIN đang trong kho cho gợi ý tự động."""
        try:
            vehicles = self.vehicle_manager.get_in_stock()
            return [v['vin'] for v in vehicles if v.get('vin')]
        except Exception:
            return []
    
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

    def update_dropdowns(self):
        # === PHASE 2.5: AutocompleteEntry tự lấy suggestions, chỉ cần log ===
        logging.info("Đã cập nhật danh sách tài xế và xe vận chuyển cho tab Xuất lẻ.")

    def open_camera_scanner(self):
        dialog = CameraScannerDialog(self.app)
        if dialog.result:
            self.scan_entry.delete(0, "end")
            self.scan_entry.insert(0, dialog.result)
            self.process_out()

    def process_out(self, event=None):
        vin = self.scan_entry.get().strip().upper()
        if not vin: return

        # === PHASE 2.5: Sử dụng entry thay vì combo ===
        transport_plate = self.transport_entry.get().strip()
        driver_name = self.driver_entry.get().strip()

        # Tái sử dụng driver_map và transport_map từ dispatch_tab để kiểm tra
        if driver_name and (driver_name not in self.app.dispatch_tab.driver_map):
            prompt = self.app.get_translation("prompt_add_new_driver").format(name=driver_name)
            if messagebox.askyesno("Xác nhận Thêm mới", prompt, parent=self.app):
                result = self.entity_manager.add_driver(driver_name, "", "", "Tự động thêm từ xuất lẻ")
                if not result["success"]:
                    messagebox.showerror("Lỗi", result["message"], parent=self.app)
                    return
                self.update_dropdowns()
                self.app.dispatch_tab.update_dropdowns() # Đồng bộ lại dispatch_tab
            else:
                return
        
        if transport_plate and (transport_plate not in self.app.dispatch_tab.transport_map):
            prompt = self.app.get_translation("prompt_add_new_transport").format(plate=transport_plate)
            if messagebox.askyesno("Xác nhận Thêm mới", prompt, parent=self.app):
                result = self.entity_manager.add_transport_vehicle(transport_plate, "", "Tự động thêm từ xuất lẻ")
                if not result["success"]:
                    messagebox.showerror("Lỗi", result["message"], parent=self.app)
                    return
                self.update_dropdowns()
                self.app.dispatch_tab.update_dropdowns() # Đồng bộ lại dispatch_tab
            else:
                return
        
        vehicle_data = self.vehicle_manager.find_vehicle_in_stock(vin)
        if not vehicle_data:
            log_msg = f"Xuất kho thất bại: không tìm thấy VIN {vin} trong kho."
            logging.warning(log_msg)
            self.app.log_to_widget(self.outbound_log_text, log_msg, "error")
            messagebox.showwarning(self.app.get_translation("warn_not_found"), self.app.get_translation("warn_not_found_msg").format(vin=vin))
            return
        
        # === Confirm dialog trước khi xuất xe ===
        owner = vehicle_data.get('owner', 'N/A')
        vehicle_type = vehicle_data.get('vehicle_type', 'N/A')
        confirm_msg = self.app.get_translation("confirm_outbound_msg").format(
            vin=vin,
            owner=owner,
            vehicle_type=vehicle_type,
            transport=transport_plate or 'N/A',
            driver=driver_name or 'N/A'
        )
        if not messagebox.askyesno(
            self.app.get_translation("confirm_outbound_title"),
            confirm_msg,
            parent=self.app
        ):
            return
        
        location_id_to_free = vehicle_data.get('location_id')

        result = self.vehicle_manager.update_to_out(vin, datetime.now(), transport_plate, driver_name)
        
        if result["success"]:
            if location_id_to_free:
                self.location_manager.set_location_occupied(location_id_to_free, False)

            log_msg = f"Đã xuất kho xe: VIN={vin}, Xe VC={transport_plate}, Tài xế={driver_name}"
            logging.info(log_msg)
            self.app.log_to_widget(self.outbound_log_text, log_msg, "success")
            self.app.show_toast(self.app.get_translation("toast_shipped_success").format(vin=vin))
            self.app.on_data_changed()
            self.scan_entry.delete(0, "end")
            self.scan_entry.focus()
        else:
            log_msg = f"Lỗi khi xuất kho VIN {vin}: {result['message']}"
            logging.error(log_msg)
            self.app.log_to_widget(self.outbound_log_text, log_msg, "error")
            messagebox.showerror("Lỗi", f"Không thể xuất kho cho VIN {vin}:\n{result['message']}")