# ui/inbound_tab.py
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
import logging
import threading
import os
import webbrowser

from data_normalizer import normalizer
import excel_importer
from report_generators import pdf_generator
from config import PAD_GENERAL, PAD_SMALL
from ui.camera_scanner import CameraScannerDialog
from ui.components import add_right_click_menu # === BỔ SUNG MỚI ===

class InboundTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.vehicle_manager = self.app.vehicle_manager
        self.location_manager = self.app.location_manager
        self.location_map = {}

        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        manual_frame = ctk.CTkFrame(self.parent)
        manual_frame.grid(row=0, column=0, padx=PAD_GENERAL, pady=(PAD_GENERAL, PAD_SMALL), sticky="ew")
        manual_frame.grid_columnconfigure(1, weight=1)

        self.lbl_manual_entry = ctk.CTkLabel(manual_frame, text="", font=self.app.font_bold)
        self.lbl_manual_entry.grid(row=0, column=0, columnspan=3, padx=PAD_SMALL, pady=(PAD_SMALL, PAD_GENERAL), sticky="w")

        self.lbl_vin = ctk.CTkLabel(manual_frame, text="", font=self.app.font_normal)
        self.lbl_vin.grid(row=1, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        
        vin_frame = ctk.CTkFrame(manual_frame, fg_color="transparent")
        vin_frame.grid(row=1, column=1, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        vin_frame.grid_columnconfigure(0, weight=1)
        
        self.vin_entry = ctk.CTkEntry(vin_frame, font=self.app.font_normal)
        self.vin_entry.grid(row=0, column=0, sticky="ew")
        add_right_click_menu(self.app, self.vin_entry) # === BỔ SUNG MỚI ===

        self.btn_open_camera = ctk.CTkButton(vin_frame, text="📷", width=30, command=self.open_camera_scanner)
        self.btn_open_camera.grid(row=0, column=1, padx=(PAD_SMALL, 0))

        self.lbl_owner = ctk.CTkLabel(manual_frame, text="", font=self.app.font_normal)
        self.lbl_owner.grid(row=2, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        self.owner_combo = ctk.CTkComboBox(manual_frame, values=[], font=self.app.font_normal)
        self.owner_combo.grid(row=2, column=1, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        self.owner_combo.set("")
        self.owner_combo.bind("<<ComboboxSelected>>", self._on_owner_selected)
        add_right_click_menu(self.app, self.owner_combo) # === BỔ SUNG MỚI ===

        self.lbl_vehicle_type = ctk.CTkLabel(manual_frame, text="", font=self.app.font_normal)
        self.lbl_vehicle_type.grid(row=3, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        self.type_combo = ctk.CTkComboBox(manual_frame, values=[], font=self.app.font_normal)
        self.type_combo.grid(row=3, column=1, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        self.type_combo.set("")
        add_right_click_menu(self.app, self.type_combo) # === BỔ SUNG MỚI ===

        self.lbl_location = ctk.CTkLabel(manual_frame, text="", font=self.app.font_normal)
        self.lbl_location.grid(row=4, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        self.location_combo = ctk.CTkComboBox(manual_frame, values=[], command=self._on_location_select, font=self.app.font_normal)
        self.location_combo.grid(row=4, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        self.location_combo.set("")
        add_right_click_menu(self.app, self.location_combo) # === BỔ SUNG MỚI ===
        
        self.btn_find_location = ctk.CTkButton(manual_frame, text="", width=120, command=self._find_next_location, font=self.app.font_normal)
        self.btn_find_location.grid(row=4, column=2, padx=(0, PAD_SMALL), pady=PAD_SMALL)
        
        self.lbl_location_info = ctk.CTkLabel(manual_frame, text="", font=self.app.font_small_italic)
        self.lbl_location_info.grid(row=5, column=1, columnspan=2, padx=PAD_SMALL, pady=(0, PAD_SMALL), sticky="w")

        self.btn_save = ctk.CTkButton(manual_frame, text="", command=self.add_vehicle, font=self.app.font_normal)
        self.btn_save.grid(row=6, column=0, pady=PAD_GENERAL, padx=PAD_SMALL, sticky="w")
        # === TÍNH NĂNG MỚI: Thêm phím tắt Ctrl+S ===
        self.app.bind("<Control-s>", lambda event: self.add_vehicle())
        self.app.bind("<Control-S>", lambda event: self.add_vehicle()) # Cho cả trường hợp CapsLock
        # ==========================================

        bulk_frame = ctk.CTkFrame(self.parent)
        bulk_frame.grid(row=1, column=0, padx=PAD_GENERAL, pady=(PAD_SMALL, PAD_GENERAL), sticky="nsew")
        bulk_frame.grid_columnconfigure(1, weight=1)
        bulk_frame.grid_rowconfigure(1, weight=1)

        self.lbl_bulk_import = ctk.CTkLabel(bulk_frame, text="", font=self.app.font_bold)
        self.lbl_bulk_import.grid(row=0, column=0, columnspan=2, padx=PAD_SMALL, pady=(PAD_SMALL, PAD_GENERAL), sticky="w")

        self.btn_import = ctk.CTkButton(bulk_frame, text="", command=self.import_excel, font=self.app.font_normal)
        self.btn_import.grid(row=1, column=0, padx=PAD_GENERAL, pady=PAD_SMALL, sticky="nw")

        self.inbound_log_text = ctk.CTkTextbox(bulk_frame, wrap="word", state="disabled", font=("Courier New", 12))
        self.inbound_log_text.grid(row=1, column=1, padx=(0, PAD_GENERAL), pady=PAD_SMALL, sticky="nsew")
        self.inbound_log_text.tag_config("error", foreground="red")
        self.inbound_log_text.tag_config("info", foreground="#00A0E5")
        add_right_click_menu(self.app, self.inbound_log_text) # === BỔ SUNG MỚI ===

        self.update_language()
        self.update_dropdowns()

    def update_language(self):
        self.lbl_manual_entry.configure(text=self.app.get_translation("frame_manual_entry"))
        self.lbl_vin.configure(text=self.app.get_translation("lbl_vin"))
        self.lbl_owner.configure(text=self.app.get_translation("lbl_owner"))
        self.lbl_vehicle_type.configure(text=self.app.get_translation("lbl_vehicle_type"))
        self.lbl_location.configure(text=self.app.get_translation("lbl_location"))
        self.btn_find_location.configure(text=self.app.get_translation("btn_find_location"))
        self.btn_save.configure(text=self.app.get_translation("btn_save_vehicle"))
        self.lbl_bulk_import.configure(text=self.app.get_translation("frame_bulk_import"))
        self.btn_import.configure(text=self.app.get_translation("btn_import_excel"))

    def open_camera_scanner(self):
        dialog = CameraScannerDialog(self.app)
        if dialog.result:
            self.vin_entry.delete(0, "end")
            self.vin_entry.insert(0, dialog.result)
            self.owner_combo.focus()

    def update_dropdowns(self):
        owners = self.vehicle_manager.get_distinct_owners()
        self.owner_combo.configure(values=owners)
        
        all_vehicle_types = self.vehicle_manager.get_distinct_vehicle_types()
        self.type_combo.configure(values=all_vehicle_types)
        
        free_locations = self.location_manager.get_all_free_locations()
        self.location_map = {loc['full_location_name']: loc['id'] for loc in free_locations}
        self.location_combo.configure(values=list(self.location_map.keys()))
        self.location_combo.set("")
        self.lbl_location_info.configure(text="")

    def _on_owner_selected(self, event=None):
        selected_owner = self.owner_combo.get()
        if selected_owner:
            specific_vehicle_types = self.vehicle_manager.get_distinct_vehicle_types(owner_filter=selected_owner)
            self.type_combo.configure(values=specific_vehicle_types)
            if specific_vehicle_types:
                self.type_combo.set(specific_vehicle_types[0])
            else:
                self.type_combo.set("")
        else:
            all_vehicle_types = self.vehicle_manager.get_distinct_vehicle_types()
            self.type_combo.configure(values=all_vehicle_types)
            self.type_combo.set("")

    def _on_location_select(self, selected_location):
        # === SỬA LỖI: Sử dụng key dịch thuật ===
        location_id = self.location_map.get(selected_location, 'N/A')
        self.lbl_location_info.configure(text=self.app.get_translation("lbl_location_id_info").format(id=location_id))
        # =====================================

    def _find_next_location(self):
        next_loc = self.location_manager.get_next_available_location()
        if next_loc:
            self.location_combo.set(next_loc['full_location_name'])
            self._on_location_select(next_loc['full_location_name'])
        else:
            messagebox.showwarning(
                self.app.get_translation("warn_no_location_available"), 
                self.app.get_translation("warn_no_location_available_msg"), 
                parent=self.app
            )

    def add_vehicle(self):
        raw_vin = self.vin_entry.get().strip()
        owner = normalizer.normalize_owner(self.owner_combo.get())
        vehicle_type = normalizer.normalize_vehicle_type(self.type_combo.get())
        
        # Validate VIN
        vin_result = normalizer.validate_vin(raw_vin, strict=False)
        if not vin_result["valid"]:
            messagebox.showwarning(
                self.app.get_translation("warn_invalid_vin_title"), 
                self.app.get_translation("warn_invalid_vin_msg").format(error=vin_result["message"]),
                parent=self.app
            )
            self.vin_entry.focus()
            return
        
        vin = vin_result["normalized"]
        
        if not owner:
            messagebox.showwarning(self.app.get_translation("warn_missing_info"), self.app.get_translation("warn_missing_info_msg"))
            return

        location_name = self.location_combo.get()
        location_id = self.location_map.get(location_name)
        if not location_id:
            messagebox.showwarning(self.app.get_translation("warn_missing_info"), self.app.get_translation("warn_no_location_selected"))
            return

        date_in_obj = datetime.now()
        result = self.vehicle_manager.add_vehicle(vin, owner, vehicle_type, date_in_obj, location_id)
        
        if result["success"]:
            self.location_manager.set_location_occupied(location_id, True)
            self.app.show_toast(self.app.get_translation("toast_add_success"))
            
            # === SỬA LỖI: Sử dụng key dịch thuật ===
            prompt_title = self.app.get_translation("dialog_print_tag_title")
            prompt_message = self.app.get_translation("dialog_print_tag_prompt").format(vin=vin)
            if messagebox.askyesno(prompt_title, prompt_message):
            # =====================================
                vehicle_info = {
                    "vin": vin, "owner": owner, "vehicle_type": vehicle_type,
                    "full_location_name": location_name, "date_in": date_in_obj.isoformat()
                }
                self.create_and_open_tag(vehicle_info)
            
            self.app.on_data_changed()
            
            self.vin_entry.delete(0, "end")
            self.owner_combo.set("")
            self.type_combo.set("")
            
            self.vin_entry.focus()
            self.vin_entry.select_range(0, 'end')
        else:
            messagebox.showerror(self.app.get_translation("err_add_fail"), result["message"])

    def create_and_open_tag(self, vehicle_info):
        default_filename = f"QR Code_Xe_{vehicle_info['vin']}.pdf"
        file_path = filedialog.asksaveasfilename(
            title=self.app.get_translation("dialog_save_qr_title"), 
            initialfile=default_filename,
            defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")]
        )
        if not file_path: return

        def worker():
            result = pdf_generator.generate_vehicle_tag_pdf(file_path, vehicle_info)
            def update_ui():
                if not self.parent.winfo_exists(): return
                if result["success"]:
                    self.app.show_toast(self.app.get_translation("toast_qr_created_success"))
                    try: os.startfile(file_path)
                    except AttributeError: webbrowser.open(file_path)
                else: 
                    messagebox.showerror(
                        self.app.get_translation("err_create_qr_title"), 
                        self.app.get_translation("err_create_qr_msg").format(error=result['message'])
                    )
            
            if self.parent.winfo_exists():
                self.app.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if not path: return

        self.inbound_log_text.configure(state="normal")
        self.inbound_log_text.delete("1.0", "end")
        self.inbound_log_text.configure(state="disabled")

        def worker():
            res = excel_importer.import_vehicles_from_excel(
                path, self.vehicle_manager, self.location_manager, normalizer.normalize_owner
            )
            def update_ui():
                if not self.parent.winfo_exists(): return
                
                for error_detail in res["error_details"]:
                    self.app.log_to_widget(self.inbound_log_text, error_detail, "error")
                
                summary_msg = self.app.get_translation("import_summary_log").format(
                    success=res['success'], errors=res['errors']
                )
                self.app.log_to_widget(self.inbound_log_text, summary_msg, "info")
                
                messagebox.showinfo(
                    self.app.get_translation("import_result_title"), 
                    self.app.get_translation("import_result_msg").format(
                        total=res['total'], success=res['success'], errors=res['errors']
                    )
                )
                
                if res["success"] > 0:
                    self.app.on_data_changed()

            if self.parent.winfo_exists():
                self.app.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()