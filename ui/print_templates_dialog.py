# ui/print_templates_dialog.py
"""
Dialog quản lý các template in ấn.
- Xem trước template
- Chọn template mặc định
- Tùy chỉnh các thông tin cơ bản
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import json

class PrintTemplatesDialog(ctk.CTkToplevel):
    """Dialog quản lý template in ấn."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.transient(parent)
        
        self.title(self.app.get_translation("print_templates_title"))
        self.geometry("750x650")
        self.resizable(True, True)
        
        self.templates = self._load_templates()
        self.selected_template = None
        
        self._build_ui()
        self.grab_set()
        self.center_window()
    
    def center_window(self):
        """Căn giữa cửa sổ."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")
    
    def _load_templates(self):
        """Load danh sách template có sẵn."""
        templates = [
            {
                "id": "qr_tag_standard",
                "name_key": "template_qr_tag_standard",
                "description_key": "template_qr_tag_standard_desc",
                "type": "qr_tag",
                "size": "8x4.5 cm",
                "default": True
            },
            {
                "id": "qr_tag_compact",
                "name_key": "template_qr_tag_compact",
                "description_key": "template_qr_tag_compact_desc",
                "type": "qr_tag",
                "size": "6x3.5 cm",
                "default": False
            },
            {
                "id": "voucher_standard",
                "name_key": "template_voucher_standard",
                "description_key": "template_voucher_standard_desc",
                "type": "voucher",
                "size": "A4",
                "default": True
            },
            {
                "id": "report_landscape",
                "name_key": "template_report_landscape",
                "description_key": "template_report_landscape_desc",
                "type": "report",
                "size": "A4 Landscape",
                "default": True
            },
            {
                "id": "report_portrait",
                "name_key": "template_report_portrait",
                "description_key": "template_report_portrait_desc",
                "type": "report",
                "size": "A4 Portrait",
                "default": False
            },
        ]
        return templates
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🖨️ " + self.app.get_translation("print_templates_title"),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(pady=(15, 10))
        
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left: Template list
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        
        ctk.CTkLabel(
            left_frame,
            text=self.app.get_translation("print_templates_list"),
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Template type filter
        filter_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        self.type_filter = ctk.StringVar(value="all")
        types = [
            ("all", self.app.get_translation("filter_all")),
            ("qr_tag", "QR Tag"),
            ("voucher", self.app.get_translation("template_type_voucher")),
            ("report", self.app.get_translation("template_type_report")),
        ]
        
        for value, text in types:
            ctk.CTkRadioButton(
                filter_frame,
                text=text,
                variable=self.type_filter,
                value=value,
                command=self._filter_templates,
                width=80
            ).pack(side="left", padx=5)
        
        # Template listbox
        self.template_list = ctk.CTkScrollableFrame(left_frame, height=250)
        self.template_list.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._populate_templates()
        
        # Right: Preview
        right_frame = ctk.CTkFrame(main_frame, width=200)
        right_frame.pack(side="right", fill="both", padx=(5, 10), pady=10)
        right_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            right_frame,
            text=self.app.get_translation("print_template_preview"),
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Preview area
        self.preview_frame = ctk.CTkFrame(right_frame, fg_color="#f0f0f0")
        self.preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text=self.app.get_translation("print_select_template"),
            wraplength=160,
            justify="center"
        )
        self.preview_label.pack(expand=True)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text=self.app.get_translation("btn_close"),
            command=self.destroy,
            width=100,
            fg_color="gray"
        ).pack(side="right", padx=5)
        
        self.set_default_btn = ctk.CTkButton(
            btn_frame,
            text=self.app.get_translation("print_set_default"),
            command=self._set_default,
            width=150,
            state="disabled"
        )
        self.set_default_btn.pack(side="right", padx=5)
    
    def _populate_templates(self):
        """Hiển thị danh sách template."""
        # Clear existing
        for widget in self.template_list.winfo_children():
            widget.destroy()
        
        type_filter = self.type_filter.get()
        
        for template in self.templates:
            if type_filter != "all" and template["type"] != type_filter:
                continue
            
            self._create_template_card(template)
    
    def _create_template_card(self, template):
        """Tạo card cho một template."""
        card = ctk.CTkFrame(self.template_list)
        card.pack(fill="x", pady=3)
        
        # Left content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        
        # Name with default indicator
        name = self.app.get_translation(template["name_key"])
        if template["default"]:
            name += " ⭐"
        
        ctk.CTkLabel(
            content_frame,
            text=name,
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w")
        
        # Size
        ctk.CTkLabel(
            content_frame,
            text=f"{self.app.get_translation('print_size')}: {template['size']}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w")
        
        # Select button
        select_btn = ctk.CTkButton(
            card,
            text=self.app.get_translation("btn_select"),
            width=70,
            height=28,
            command=lambda t=template: self._select_template(t)
        )
        select_btn.pack(side="right", padx=10, pady=8)
        
        # Bind click on card
        card.bind("<Button-1>", lambda e, t=template: self._select_template(t))
    
    def _filter_templates(self):
        """Lọc template theo loại."""
        self._populate_templates()
    
    def _select_template(self, template):
        """Chọn template."""
        self.selected_template = template
        self.set_default_btn.configure(state="normal")
        
        # Update preview
        name = self.app.get_translation(template["name_key"])
        desc = self.app.get_translation(template["description_key"])
        
        preview_text = f"""📄 {name}

{self.app.get_translation('print_size')}: {template['size']}

{desc}

{'⭐ ' + self.app.get_translation('print_is_default') if template['default'] else ''}"""
        
        self.preview_label.configure(text=preview_text)
    
    def _set_default(self):
        """Đặt template làm mặc định."""
        if not self.selected_template:
            return
        
        template_type = self.selected_template["type"]
        
        # Update defaults
        for t in self.templates:
            if t["type"] == template_type:
                t["default"] = (t["id"] == self.selected_template["id"])
        
        # Refresh list
        self._populate_templates()
        
        # Update preview
        self._select_template(self.selected_template)
        
        messagebox.showinfo(
            self.app.get_translation("success_title"),
            self.app.get_translation("print_default_set").format(
                name=self.app.get_translation(self.selected_template["name_key"])
            ),
            parent=self
        )
