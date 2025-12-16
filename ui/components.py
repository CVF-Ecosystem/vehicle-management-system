# ui/components.py
import customtkinter as ctk
from tkinter import Menu, Toplevel, Label, messagebox, ttk
from tkcalendar import DateEntry
from datetime import datetime
from data_normalizer import normalizer

def add_right_click_menu(app, widget):
    """Thêm một menu chuột phải (Cắt, Sao chép, Dán) vào một widget."""
    menu = Menu(widget, tearoff=0, font=("Arial", 12))
    
    menu.add_command(label=app.get_translation("ctx_menu_cut"), command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label=app.get_translation("ctx_menu_copy"), command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label=app.get_translation("ctx_menu_paste"), command=lambda: widget.event_generate("<<Paste>>"))
    
    def update_menu_state(event):
        try:
            has_selection = widget.selection_get()
            menu.entryconfigure(app.get_translation("ctx_menu_cut"), state="normal" if has_selection else "disabled")
            menu.entryconfigure(app.get_translation("ctx_menu_copy"), state="normal" if has_selection else "disabled")
        except:
            menu.entryconfigure(app.get_translation("ctx_menu_cut"), state="disabled")
            menu.entryconfigure(app.get_translation("ctx_menu_copy"), state="disabled")
        
        try:
            # Kiểm tra xem clipboard có nội dung không
            widget.clipboard_get()
            menu.entryconfigure(app.get_translation("ctx_menu_paste"), state="normal")
        except:
            menu.entryconfigure(app.get_translation("ctx_menu_paste"), state="disabled")

    def show_menu(event):
        update_menu_state(event)
        menu.tk_popup(event.x_root, event.y_root)

    # Sử dụng bind_class để áp dụng cho cả phần Entry bên trong CTkComboBox
    if isinstance(widget, ctk.CTkComboBox):
        widget._entry.bind("<Button-3>", show_menu)
    else:
        widget.bind("<Button-3>", show_menu)

def style_treeview(app, tree):
    """Áp dụng style của CustomTkinter cho một widget ttk.Treeview."""
    style = ttk.Style()
    
    bg_color = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
    text_color = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
    selected_color = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
    header_bg = app._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"])
    
    style.theme_use('default')
    style.map('Treeview', background=[('selected', selected_color)], foreground=[('selected', text_color)])
    style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, rowheight=28, font=("Arial", 12))
    style.configure("Treeview.Heading", background=header_bg, foreground=text_color, font=("Arial", 12, "bold"))
    style.map("Treeview.Heading", relief=[('active','groove'),('!active','flat')])

class Toast:
    """Một thông báo nhỏ, tự động biến mất ở phía trên cửa sổ."""
    def __init__(self, parent, message, duration=2500):
        self.parent = parent
        self.top = Toplevel(parent)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        
        bg_color = "#333"
        fg_color = "white"
        
        Label(self.top, text=message, bg=bg_color, fg=fg_color, padx=15, pady=8, font=("Arial", 12, "bold")).pack()
        self.top.update_idletasks()
        
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        
        toast_width = self.top.winfo_width()
        
        x = parent_x + (parent_width // 2) - (toast_width // 2)
        y = parent_y + 50
        
        self.top.geometry(f"+{x}+{y}")
        self.top.after(duration, self.top.destroy)

class DateRangeDialog(ctk.CTkToplevel):
    """Một hộp thoại để chọn khoảng thời gian (Từ ngày - Đến ngày)."""
    def __init__(self, parent, title):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        # === SỬA LỖI: Tăng chiều cao của cửa sổ ===
        self.geometry("350x200")
        # ========================================
        self.result = None
        
        self.app = parent.app if hasattr(parent, 'app') else parent

        # === SỬA LỖI: Thêm padding để giao diện thoáng hơn ===
        self.lbl_from = ctk.CTkLabel(self, text=self.app.get_translation("lbl_from_date"), font=self.app.font_normal)
        self.lbl_from.pack(pady=(20, 5)) # Tăng padding ở trên
        self.start_date_entry = DateEntry(self, width=12, date_pattern="dd/mm/yyyy", font=("Arial", 10))
        self.start_date_entry.pack(pady=5)

        self.lbl_to = ctk.CTkLabel(self, text=self.app.get_translation("lbl_to_date"), font=self.app.font_normal)
        self.lbl_to.pack(pady=5)
        self.end_date_entry = DateEntry(self, width=12, date_pattern="dd/mm/yyyy", font=("Arial", 10))
        self.end_date_entry.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        # =====================================================
        
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_ok"), command=self.on_ok, font=self.app.font_normal).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_cancel"), command=self.destroy, font=self.app.font_normal).pack(side="left", padx=10)
        
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        start_date = datetime.combine(self.start_date_entry.get_date(), datetime.min.time())
        end_date = datetime.combine(self.end_date_entry.get_date(), datetime.max.time())
        self.result = (start_date, end_date)
        self.destroy()

class EditVehicleDialog(ctk.CTkToplevel):
    """Hộp thoại để chỉnh sửa thông tin chi tiết của một chiếc xe."""
    def __init__(self, parent, vehicle_info):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.title(f"{self.app.get_translation('ctx_menu_edit')}: {vehicle_info['vin']}")
        self.geometry("400x280")
        self.result = None
        self.original_vin = vehicle_info.get('vin', '')

        self.lbl_vin = ctk.CTkLabel(self, text=self.app.get_translation("lbl_vin"), font=self.app.font_normal)
        self.lbl_vin.pack(pady=(10, 0))
        self.vin_entry = ctk.CTkEntry(self, width=300, font=self.app.font_normal)
        self.vin_entry.insert(0, self.original_vin)
        self.vin_entry.pack()
        add_right_click_menu(self.app, self.vin_entry)

        self.lbl_owner = ctk.CTkLabel(self, text=self.app.get_translation("lbl_owner"), font=self.app.font_normal)
        self.lbl_owner.pack(pady=(10, 0))
        self.owner_entry = ctk.CTkEntry(self, width=300, font=self.app.font_normal)
        self.owner_entry.insert(0, vehicle_info.get('owner', ''))
        self.owner_entry.pack()
        add_right_click_menu(self.app, self.owner_entry)

        self.lbl_type = ctk.CTkLabel(self, text=self.app.get_translation("lbl_vehicle_type"), font=self.app.font_normal)
        self.lbl_type.pack(pady=(10, 0))
        self.type_entry = ctk.CTkEntry(self, width=300, font=self.app.font_normal)
        self.type_entry.insert(0, vehicle_info.get('vehicle_type', ''))
        self.type_entry.pack()
        add_right_click_menu(self.app, self.type_entry)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_save"), command=self.on_ok, font=self.app.font_normal).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_cancel"), command=self.destroy, font=self.app.font_normal).pack(side="left", padx=10)
        
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        new_vin = self.vin_entry.get().strip().upper()
        if not new_vin:
            messagebox.showwarning(self.app.get_translation("warn_missing_info"), 
                                   self.app.get_translation("warn_field_empty_msg").format(field=self.app.get_translation("lbl_vin")), 
                                   parent=self)
            return

        self.result = {
            "original_vin": self.original_vin,
            "new_vin": new_vin,
            "owner": self.owner_entry.get().strip(),
            "vehicle_type": self.type_entry.get().strip()
        }
        self.destroy()

class LocationSwapDialog(ctk.CTkToplevel):
    """Hộp thoại để di chuyển một xe sang vị trí trống khác."""
    def __init__(self, parent, vehicle_info, location_manager):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.vehicle_manager = self.app.vehicle_manager
        self.location_manager = location_manager
        
        self.vin = vehicle_info.get('vin')
        self.current_location = vehicle_info.get('full_location_name', 'N/A')
        self.result = None

        self.title(self.app.get_translation("dialog_swap_location_title"))
        self.geometry("450x250")

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(info_frame, text=f"{self.app.get_translation('lbl_vin')} {self.vin}", font=self.app.font_bold).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=f"{self.app.get_translation('lbl_current_location')} {self.current_location}", font=self.app.font_normal).pack(anchor="w")

        swap_frame = ctk.CTkFrame(self, fg_color="transparent")
        swap_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(swap_frame, text=self.app.get_translation("lbl_new_location"), font=self.app.font_normal).pack(anchor="w")
        
        self.location_combo = ctk.CTkComboBox(swap_frame, values=[], font=self.app.font_normal)
        self.location_combo.pack(fill="x", pady=(5,0))
        add_right_click_menu(self.app, self.location_combo)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")

        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_confirm"), command=self.on_confirm, font=self.app.font_normal).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text=self.app.get_translation("btn_cancel"), command=self.destroy, font=self.app.font_normal).pack(side="right", expand=True, padx=5)

        self._load_free_locations()
        self.grab_set()
        self.wait_window()

    def _load_free_locations(self):
        free_locations = self.location_manager.get_all_free_locations()
        self.location_map = {loc['full_location_name']: loc['id'] for loc in free_locations}
        self.location_combo.configure(values=list(self.location_map.keys()))
        if self.location_map:
            self.location_combo.set(list(self.location_map.keys())[0])

    def on_confirm(self):
        selected_location_name = self.location_combo.get()
        if not selected_location_name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn một vị trí mới.", parent=self)
            return
            
        new_location_id = self.location_map.get(selected_location_name)
        
        result = self.vehicle_manager.swap_vehicle_location(self.vin, new_location_id)
        
        if result["success"]:
            self.app.show_toast(result["message"])
            self.result = True
            self.destroy()
        else:
            messagebox.showerror("Lỗi", result["message"], parent=self)