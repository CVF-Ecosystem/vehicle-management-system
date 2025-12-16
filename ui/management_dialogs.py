# ui/management_dialogs.py
import customtkinter as ctk
from tkinter import messagebox, Listbox, END, filedialog
import pandas as pd
import os
from report_generators import excel_generator
import utils
from config import (
    ENTITY_TYPE_DRIVER, EXPECTED_DRIVER_NAME_COL, EXPECTED_DRIVER_PHONE_COL,
    EXPECTED_DRIVER_CCCD_COL, EXPECTED_PLATE_COL, EXPECTED_TRANSPORT_TYPE_COL, 
    EXPECTED_NOTES_COL
)
from ui.components import add_right_click_menu # === BỔ SUNG MỚI ===

class ManagementDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, item_type):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.title(title)
        self.geometry("500x550")
        self.entity_manager = self.app.entity_manager
        self.item_type = item_type
        self.items_map = {}

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(0, weight=1)

        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.listbox = Listbox(list_frame, font=("Arial", 12), borderwidth=0, highlightthickness=0)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ctk.CTkScrollbar(list_frame, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        btn_add = ctk.CTkButton(self, text=self.app.get_translation("btn_add_new"), command=self.add_item, font=self.app.font_normal)
        btn_add.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        btn_edit = ctk.CTkButton(self, text=self.app.get_translation("btn_edit"), command=self.edit_item, font=self.app.font_normal)
        btn_edit.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        btn_delete = ctk.CTkButton(self, text=self.app.get_translation("btn_delete"), command=self.delete_item, fg_color="#D32F2F", hover_color="#B71C1C", font=self.app.font_normal)
        btn_delete.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

        import_frame = ctk.CTkFrame(self)
        import_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        import_frame.grid_columnconfigure((0, 1), weight=1)

        btn_import = ctk.CTkButton(import_frame, text=self.app.get_translation("btn_import_from_excel"), command=self._import_from_excel, font=self.app.font_normal)
        btn_import.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        btn_template = ctk.CTkButton(import_frame, text=self.app.get_translation("btn_download_template"), command=self._download_template, font=self.app.font_normal)
        btn_template.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        export_frame = ctk.CTkFrame(self)
        export_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        export_frame.grid_columnconfigure(0, weight=1)

        btn_export = ctk.CTkButton(export_frame, text=self.app.get_translation("btn_export_to_excel"), command=self._export_to_excel, font=self.app.font_normal)
        btn_export.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.load_items()
        self.grab_set()
        self.wait_window()

    def _download_template(self):
        if self.item_type == ENTITY_TYPE_DRIVER:
            template_data = {
                EXPECTED_DRIVER_NAME_COL: ["Nguyễn Văn A", "Trần Thị B"],
                EXPECTED_DRIVER_PHONE_COL: ["090xxxxxxx", "091xxxxxxx"],
                EXPECTED_DRIVER_CCCD_COL: ["012345678901", "109876543210"],
                EXPECTED_NOTES_COL: ["Tài xế kinh nghiệm", ""]
            }
            filename = "driver_template.xlsx"
        else:
            template_data = {
                EXPECTED_PLATE_COL: ["51C-123.45", "60A-543.21"],
                EXPECTED_TRANSPORT_TYPE_COL: ["Xe đầu kéo", "Xe tải"],
                EXPECTED_NOTES_COL: ["", "Xe mới"]
            }
            filename = "transport_template.xlsx"

        path = filedialog.asksaveasfilename(
            title="Lưu file mẫu", defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")], initialfile=filename, parent=self
        )
        if not path: return
        
        try:
            df = pd.DataFrame(template_data)
            df.to_excel(path, index=False)
            messagebox.showinfo("Thành công", f"Đã lưu file mẫu tại:\n{os.path.abspath(path)}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo file mẫu: {e}", parent=self)

    def _import_from_excel(self):
        path = filedialog.askopenfilename(
            title="Chọn file Excel để import", filetypes=[("Excel files", "*.xlsx;*.xls")], parent=self
        )
        if not path: return

        try:
            df = pd.read_excel(path, dtype=str).fillna('')
            df.columns = [c.strip().upper() for c in df.columns]
        except Exception as e:
            messagebox.showerror("Lỗi Đọc File", f"Không thể đọc file Excel:\n{e}", parent=self)
            return

        success_count = 0
        skipped_count = 0

        if self.item_type == ENTITY_TYPE_DRIVER:
            if EXPECTED_DRIVER_NAME_COL not in df.columns:
                msg = self.app.get_translation("err_column_missing_msg").format(col=EXPECTED_DRIVER_NAME_COL)
                messagebox.showerror(self.app.get_translation("err_column_missing_generic"), msg, parent=self)
                return
            
            for _, row in df.iterrows():
                name = row.get(EXPECTED_DRIVER_NAME_COL, '').strip()
                if not name: continue
                phone = row.get(EXPECTED_DRIVER_PHONE_COL, '').strip()
                cccd = row.get(EXPECTED_DRIVER_CCCD_COL, '').strip()
                notes = row.get(EXPECTED_NOTES_COL, '').strip()
                result = self.entity_manager.add_driver(name, phone, cccd, notes)
                if result["success"]: success_count += 1
                else: skipped_count += 1
        else:
            if EXPECTED_PLATE_COL not in df.columns:
                msg = self.app.get_translation("err_column_missing_msg").format(col=EXPECTED_PLATE_COL)
                messagebox.showerror(self.app.get_translation("err_column_missing_generic"), msg, parent=self)
                return

            for _, row in df.iterrows():
                plate = row.get(EXPECTED_PLATE_COL, '').strip()
                if not plate: continue
                v_type = row.get(EXPECTED_TRANSPORT_TYPE_COL, '').strip()
                notes = row.get(EXPECTED_NOTES_COL, '').strip()
                result = self.entity_manager.add_transport_vehicle(plate, v_type, notes)
                if result["success"]: success_count += 1
                else: skipped_count += 1
        
        self.load_items()
        summary_msg = self.app.get_translation("import_summary_message").format(s=success_count, e=skipped_count)
        messagebox.showinfo(self.app.get_translation("import_summary_title"), summary_msg, parent=self)

    def _export_to_excel(self):
        if self.item_type == ENTITY_TYPE_DRIVER:
            data = self.entity_manager.get_all_active_drivers()
            cols = {
                'name': EXPECTED_DRIVER_NAME_COL,
                'phone': EXPECTED_DRIVER_PHONE_COL,
                'cccd': EXPECTED_DRIVER_CCCD_COL,
                'notes': EXPECTED_NOTES_COL
            }
            filename_base = "Danh_sach_Tai_xe"
        else:
            data = self.entity_manager.get_all_active_transport_vehicles()
            cols = {
                'license_plate': EXPECTED_PLATE_COL,
                'type': EXPECTED_TRANSPORT_TYPE_COL,
                'notes': EXPECTED_NOTES_COL
            }
            filename_base = "Danh_sach_Xe_VC"

        if not data:
            messagebox.showinfo("Thông báo", "Không có dữ liệu để xuất.", parent=self)
            return

        default_name = utils.get_default_filename(filename_base, ".xlsx")
        path = filedialog.asksaveasfilename(
            title="Lưu file Excel", defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")], initialfile=default_name, parent=self
        )
        if not path: return

        result = excel_generator.generate_excel_report(path, data, cols)
        if result["success"]:
            self.app.show_toast("Xuất file thành công!")
        else:
            messagebox.showerror("Lỗi", f"Không thể xuất file:\n{result['message']}", parent=self)


    def load_items(self):
        self.listbox.delete(0, END)
        self.items_map.clear()
        if self.item_type == ENTITY_TYPE_DRIVER:
            items = self.entity_manager.get_all_active_drivers()
            display_key = 'name'
        else:
            items = self.entity_manager.get_all_active_transport_vehicles()
            display_key = 'license_plate'
        
        for item in items:
            self.listbox.insert(END, item[display_key])
            self.items_map[item[display_key]] = item

    def get_selected_item(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning(self.app.get_translation("warn_no_selection"), 
                                   self.app.get_translation("warn_no_selection_msg"), 
                                   parent=self)
            return None
        selected_text = self.listbox.get(selected_indices[0])
        return self.items_map.get(selected_text)
    
    def add_item(self):
        if self.item_type == ENTITY_TYPE_DRIVER:
            title = self.app.get_translation("dialog_add_driver_title")
            fields = {
                self.app.get_translation("lbl_driver_name"): "", 
                self.app.get_translation("lbl_phone"): "", 
                self.app.get_translation("lbl_cccd"): "",
                self.app.get_translation("lbl_notes"): ""
            }
            dialog = EntryDialog(self, self.app, title, fields)
            if dialog.result:
                result = self.entity_manager.add_driver(
                    dialog.result[self.app.get_translation("lbl_driver_name")], 
                    dialog.result[self.app.get_translation("lbl_phone")], 
                    dialog.result[self.app.get_translation("lbl_cccd")],
                    dialog.result[self.app.get_translation("lbl_notes")]
                )
                if not result["success"]: messagebox.showerror("Lỗi", result["message"], parent=self)
        else:
            title = self.app.get_translation("add_transport_title")
            fields = {
                self.app.get_translation("field_license_plate"): "", 
                self.app.get_translation("field_vehicle_type_transport"): "", 
                self.app.get_translation("field_notes"): ""
            }
            dialog = EntryDialog(self, self.app, title, fields)
            if dialog.result:
                result = self.entity_manager.add_transport_vehicle(
                    dialog.result[self.app.get_translation("field_license_plate")], 
                    dialog.result[self.app.get_translation("field_vehicle_type_transport")], 
                    dialog.result[self.app.get_translation("field_notes")]
                )
                if not result["success"]: messagebox.showerror("Lỗi", result["message"], parent=self)
        self.load_items()

    def edit_item(self):
        selected_item = self.get_selected_item()
        if not selected_item: return

        if self.item_type == ENTITY_TYPE_DRIVER:
            title = self.app.get_translation("dialog_edit_driver_title")
            fields = {
                self.app.get_translation("lbl_driver_name"): selected_item.get('name', ''), 
                self.app.get_translation("lbl_phone"): selected_item.get('phone', ''), 
                self.app.get_translation("lbl_cccd"): selected_item.get('cccd', ''),
                self.app.get_translation("lbl_notes"): selected_item.get('notes', '')
            }
            dialog = EntryDialog(self, self.app, title, fields)
            if dialog.result:
                result = self.entity_manager.update_driver(
                    selected_item['id'], 
                    dialog.result[self.app.get_translation("lbl_driver_name")], 
                    dialog.result[self.app.get_translation("lbl_phone")], 
                    dialog.result[self.app.get_translation("lbl_cccd")],
                    dialog.result[self.app.get_translation("lbl_notes")]
                )
                if not result["success"]: messagebox.showerror("Lỗi", result["message"], parent=self)
        else:
            title = self.app.get_translation("edit_transport_title")
            fields = {
                self.app.get_translation("field_license_plate"): selected_item.get('license_plate', ''), 
                self.app.get_translation("field_vehicle_type_transport"): selected_item.get('type', ''), 
                self.app.get_translation("field_notes"): selected_item.get('notes', '')
            }
            dialog = EntryDialog(self, self.app, title, fields)
            if dialog.result:
                result = self.entity_manager.update_transport_vehicle(
                    selected_item['id'], 
                    dialog.result[self.app.get_translation("field_license_plate")], 
                    dialog.result[self.app.get_translation("field_vehicle_type_transport")], 
                    dialog.result[self.app.get_translation("field_notes")]
                )
                if not result["success"]: messagebox.showerror("Lỗi", result["message"], parent=self)
        self.load_items()

    def delete_item(self):
        selected_item = self.get_selected_item()
        if not selected_item: return

        key = 'name' if self.item_type == ENTITY_TYPE_DRIVER else 'license_plate'
        confirm_msg = self.app.get_translation("confirm_delete_msg").format(item=selected_item.get(key, ''))
        
        if messagebox.askyesno(self.app.get_translation("confirm_delete_title"), confirm_msg, icon='warning', parent=self):
            if self.item_type == ENTITY_TYPE_DRIVER:
                result = self.entity_manager.soft_delete_driver(selected_item['id'])
            else:
                result = self.entity_manager.soft_delete_transport_vehicle(selected_item['id'])
            
            if not result["success"]:
                messagebox.showerror("Lỗi", result["message"], parent=self)
            self.load_items()

class EntryDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, title, fields):
        super().__init__(parent)
        self.transient(parent)
        self.app = app
        self.title(title)
        self.fields = fields
        self.entries = {}
        self.result = None

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(padx=15, pady=15)

        for i, (label, value) in enumerate(fields.items()):
            ctk.CTkLabel(main_frame, text=f"{label}:", font=self.app.font_normal).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ctk.CTkEntry(main_frame, width=250, font=self.app.font_normal)
            entry.grid(row=i, column=1, padx=5, pady=5)
            if value: entry.insert(0, value)
            self.entries[label] = entry
            add_right_click_menu(self.app, entry) # === BỔ SUNG MỚI ===

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_save"), command=self.on_ok, font=self.app.font_normal).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_cancel"), command=self.destroy, font=self.app.font_normal).pack(side="left", padx=10)
        
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        self.result = {}
        first_field_label = list(self.fields.keys())[0]
        first_field_value = self.entries[first_field_label].get().strip()
        if not first_field_value:
            messagebox.showwarning(self.app.get_translation("warn_missing_info"), 
                                   self.app.get_translation("warn_field_empty_msg").format(field=first_field_label), 
                                   parent=self)
            return
        
        for label, entry in self.entries.items():
            self.result[label] = entry.get().strip()
        self.destroy()