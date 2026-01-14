# ui/inbound_tab.py
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
import logging
import threading
import os
import webbrowser
import json
import tempfile

from data_normalizer import normalizer
import excel_importer
from report_generators import pdf_generator
from config import PAD_GENERAL, PAD_SMALL
from ui.camera_scanner import CameraScannerDialog
from ui.components import add_right_click_menu, AutocompleteEntry, harmonize_combobox_style  # === BỔ SUNG MỚI ===

# Auto-save draft file path
DRAFT_FILE = os.path.join(tempfile.gettempdir(), "vehicle_mgmt_inbound_draft.json")

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
        
        # === PHASE 2.5: AutocompleteEntry for VIN ===
        self.vin_entry = AutocompleteEntry(
            vin_frame,
            suggestions=self._get_vin_suggestions,
            font=self.app.font_normal,
            placeholder_text=self.app.get_translation("autocomplete_vin_hint") if hasattr(self.app, 'get_translation') else ""
        )
        self.vin_entry.grid(row=0, column=0, sticky="ew")
        add_right_click_menu(self.app, self.vin_entry.entry)

        self.btn_open_camera = ctk.CTkButton(vin_frame, text="📷", width=30, command=self.open_camera_scanner)
        self.btn_open_camera.grid(row=0, column=1, padx=(PAD_SMALL, 0))

        self.lbl_owner = ctk.CTkLabel(manual_frame, text="", font=self.app.font_normal)
        self.lbl_owner.grid(row=2, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        # === PHASE 2.5: AutocompleteEntry for owner ===
        self.owner_entry = AutocompleteEntry(
            manual_frame, 
            suggestions=self._get_owner_suggestions,
            font=self.app.font_normal,
            placeholder_text=self.app.get_translation("autocomplete_owner_hint") if hasattr(self.app, 'get_translation') else ""
        )
        self.owner_entry.grid(row=2, column=1, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        self.owner_entry.bind("<<AutocompleteSelected>>", self._on_owner_selected)
        add_right_click_menu(self.app, self.owner_entry.entry)
        # === END PHASE 2.5 ===

        self.lbl_vehicle_type = ctk.CTkLabel(manual_frame, text="", font=self.app.font_normal)
        self.lbl_vehicle_type.grid(row=3, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        self.type_combo = ctk.CTkComboBox(manual_frame, values=[], font=self.app.font_normal)
        self.type_combo.grid(row=3, column=1, columnspan=2, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        harmonize_combobox_style(self.type_combo)
        self.type_combo.set("")
        add_right_click_menu(self.app, self.type_combo) # === BỔ SUNG MỚI ===

        self.lbl_location = ctk.CTkLabel(manual_frame, text="", font=self.app.font_normal)
        self.lbl_location.grid(row=4, column=0, padx=PAD_SMALL, pady=PAD_SMALL, sticky="w")
        self.location_combo = ctk.CTkComboBox(manual_frame, values=[], command=self._on_location_select, font=self.app.font_normal)
        self.location_combo.grid(row=4, column=1, padx=PAD_SMALL, pady=PAD_SMALL, sticky="ew")
        harmonize_combobox_style(self.location_combo)
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
        bulk_frame.grid_columnconfigure(0, weight=1)
        bulk_frame.grid_rowconfigure(2, weight=1)

        self.lbl_bulk_import = ctk.CTkLabel(bulk_frame, text="", font=self.app.font_bold)
        self.lbl_bulk_import.grid(row=0, column=0, padx=PAD_SMALL, pady=(PAD_SMALL, 0), sticky="w")

        # Row 1: Nút Import + Progress (inline)
        import_row = ctk.CTkFrame(bulk_frame, fg_color="transparent")
        import_row.grid(row=1, column=0, padx=PAD_GENERAL, pady=(PAD_SMALL, 0), sticky="ew")
        import_row.grid_columnconfigure(1, weight=1)

        self.btn_import = ctk.CTkButton(import_row, text="", command=self.import_excel, font=self.app.font_normal, width=140)
        self.btn_import.grid(row=0, column=0, sticky="w")

        # Progress label + bar (ẩn mặc định, hiện khi import) - cùng hàng với nút
        self.progress_label = ctk.CTkLabel(import_row, text="", font=self.app.font_small)
        self.progress_label.grid(row=0, column=1, padx=(PAD_GENERAL, 0), sticky="w")
        self.progress_label.grid_remove()

        self.progress_bar = ctk.CTkProgressBar(import_row, width=200)
        self.progress_bar.grid(row=0, column=2, padx=(PAD_SMALL, 0), sticky="e")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        # Row 2: Log textbox - full width, expandable (ngay dưới nút Import)
        self.inbound_log_text = ctk.CTkTextbox(bulk_frame, wrap="word", state="disabled", font=("Consolas", 11), height=150)
        self.inbound_log_text.grid(row=2, column=0, padx=PAD_GENERAL, pady=(PAD_SMALL, PAD_SMALL), sticky="nsew")
        self.inbound_log_text.tag_config("error", foreground="red")
        self.inbound_log_text.tag_config("info", foreground="#00A0E5")
        add_right_click_menu(self.app, self.inbound_log_text) # === BỔ SUNG MỚI ===

        self.update_language()
        self.update_dropdowns()
        
        # === Auto-save draft: Setup ===
        self._draft_timer = None
        self._setup_autosave()
        self._restore_draft()

    def _setup_autosave(self):
        """Setup auto-save triggers on entry changes."""
        def on_change(*args):
            self._schedule_draft_save()
        
        # Bind to entry changes
        self.vin_entry.entry.bind("<KeyRelease>", on_change)
        self.owner_entry.entry.bind("<KeyRelease>", on_change)
        self.type_combo.bind("<<ComboboxSelected>>", on_change)
        self.location_combo.bind("<<ComboboxSelected>>", on_change)
    
    def _schedule_draft_save(self):
        """Schedule draft save with debounce (save after 1 second of inactivity)."""
        if self._draft_timer:
            self.app.after_cancel(self._draft_timer)
        self._draft_timer = self.app.after(1000, self._save_draft)
    
    def _save_draft(self):
        """Save current form data to draft file."""
        try:
            draft_data = {
                "vin": self.vin_entry.get(),
                "owner": self.owner_entry.get(),
                "vehicle_type": self.type_combo.get(),
                "location": self.location_combo.get(),
                "timestamp": datetime.now().isoformat()
            }
            # Only save if there's actual data
            if any([draft_data["vin"], draft_data["owner"], draft_data["vehicle_type"]]):
                with open(DRAFT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(draft_data, f, ensure_ascii=False)
                logging.debug(f"Draft saved: {draft_data}")
        except Exception as e:
            logging.warning(f"Could not save draft: {e}")
    
    def _restore_draft(self):
        """Restore draft data if exists and ask user to recover."""
        try:
            if os.path.exists(DRAFT_FILE):
                with open(DRAFT_FILE, 'r', encoding='utf-8') as f:
                    draft_data = json.load(f)
                
                # Check if draft has data
                if any([draft_data.get("vin"), draft_data.get("owner"), draft_data.get("vehicle_type")]):
                    # Ask user if they want to restore
                    timestamp = draft_data.get("timestamp", "")
                    restore_msg = self.app.get_translation("draft_restore_prompt").format(
                        vin=draft_data.get("vin", ""),
                        owner=draft_data.get("owner", ""),
                        time=timestamp[:19].replace("T", " ") if timestamp else ""
                    )
                    if messagebox.askyesno(
                        self.app.get_translation("draft_restore_title"),
                        restore_msg,
                        parent=self.app
                    ):
                        # Restore data
                        if draft_data.get("vin"):
                            self.vin_entry.delete(0, "end")
                            self.vin_entry.insert(0, draft_data["vin"])
                        if draft_data.get("owner"):
                            self.owner_entry.delete(0, "end")
                            self.owner_entry.insert(0, draft_data["owner"])
                        if draft_data.get("vehicle_type"):
                            self.type_combo.set(draft_data["vehicle_type"])
                        if draft_data.get("location"):
                            self.location_combo.set(draft_data["location"])
                            self._on_location_select(draft_data["location"])
                    
                    # Clear draft after restore prompt
                    self._clear_draft()
        except Exception as e:
            logging.warning(f"Could not restore draft: {e}")
    
    def _clear_draft(self):
        """Clear the draft file."""
        try:
            if os.path.exists(DRAFT_FILE):
                os.remove(DRAFT_FILE)
        except Exception:
            pass

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

    # === PHASE 2.5: Autocomplete suggestions ===
    def _get_vin_suggestions(self):
        """Lấy danh sách VIN đang trong kho cho gợi ý tự động (hỗ trợ nhập lại)."""
        try:
            # Gợi ý VIN từ xe đang trong kho để hỗ trợ nhập lại
            vehicles = self.vehicle_manager.get_in_stock()
            return [v['vin'] for v in vehicles if v.get('vin')]
        except Exception:
            return []
    
    def _get_owner_suggestions(self):
        """Lấy danh sách chủ hàng cho gợi ý tự động."""
        return self.vehicle_manager.get_distinct_owners()
    # === END PHASE 2.5 ===

    def open_camera_scanner(self):
        dialog = CameraScannerDialog(self.app)
        if dialog.result:
            self.vin_entry.delete(0, "end")
            self.vin_entry.insert(0, dialog.result)
            self.owner_entry.focus()  # Phase 2.5: Changed from owner_combo

    def update_dropdowns(self):
        # Phase 2.5: Owner suggestions are handled by AutocompleteEntry
        # owners = self.vehicle_manager.get_distinct_owners()
        
        all_vehicle_types = self.vehicle_manager.get_distinct_vehicle_types()
        self.type_combo.configure(values=all_vehicle_types)
        
        free_locations = self.location_manager.get_all_free_locations()
        self.location_map = {loc['full_location_name']: loc['id'] for loc in free_locations}
        self.location_combo.configure(values=list(self.location_map.keys()))
        self.location_combo.set("")
        self.lbl_location_info.configure(text="")

    def _on_owner_selected(self, event=None):
        selected_owner = self.owner_entry.get()  # Phase 2.5: Changed from owner_combo
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
        owner = normalizer.normalize_owner(self.owner_entry.get())  # Phase 2.5: Changed from owner_combo
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
            
            # Clear draft after successful save
            self._clear_draft()
            
            self.vin_entry.delete(0, "end")
            self.owner_entry.delete(0, "end")  # Phase 2.5: Changed from owner_combo.set("")
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
        
        # Show progress bar
        self.progress_bar.set(0)
        self.progress_label.configure(text=self.app.get_translation("import_reading_file") if hasattr(self.app, 'get_translation') else "Reading file...")
        self.progress_bar.grid()
        self.progress_label.grid()
        self.btn_import.configure(state="disabled")
        
        def progress_callback(current, total, message=""):
            """Callback to update progress bar from worker thread."""
            def update():
                if not self.parent.winfo_exists(): return
                progress = current / total if total > 0 else 0
                self.progress_bar.set(progress)
                if message:
                    self.progress_label.configure(text=message)
                else:
                    self.progress_label.configure(text=f"{current}/{total}")
            if self.parent.winfo_exists():
                self.app.after(0, update)

        def worker():
            res = excel_importer.import_vehicles_from_excel(
                path, self.vehicle_manager, self.location_manager, normalizer.normalize_owner,
                progress_callback=progress_callback
            )
            def update_ui():
                if not self.parent.winfo_exists(): return
                
                # Hide progress bar
                self.progress_bar.grid_remove()
                self.progress_label.grid_remove()
                self.btn_import.configure(state="normal")
                
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