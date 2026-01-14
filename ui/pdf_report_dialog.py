# ui/pdf_report_dialog.py
"""
Dialog cho phép tạo báo cáo PDF đa dạng.
- Báo cáo tồn kho theo chủ hàng
- Báo cáo nhập xuất theo khoảng thời gian
- Báo cáo xe đã xuất bãi
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta
import os
import threading

class PDFReportDialog(ctk.CTkToplevel):
    """Dialog tạo báo cáo PDF với nhiều loại báo cáo."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.transient(parent)
        
        self.title(self.app.get_translation("pdf_report_dialog_title"))
        self.geometry("650x700")
        self.resizable(True, True)
        
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
    
    def _build_ui(self):
        """Xây dựng giao diện."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="📄 " + self.app.get_translation("pdf_report_dialog_title"),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(pady=(15, 10))
        
        # Report type selection
        type_frame = ctk.CTkFrame(self)
        type_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            type_frame,
            text=self.app.get_translation("pdf_report_type"),
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.report_type = ctk.StringVar(value="stock_summary")
        
        report_types = [
            ("stock_summary", self.app.get_translation("pdf_type_stock_summary")),
            ("inbound_outbound", self.app.get_translation("pdf_type_inbound_outbound")),
            ("shipped_vehicles", self.app.get_translation("pdf_type_shipped")),
            ("full_inventory", self.app.get_translation("pdf_type_full_inventory")),
        ]
        
        for value, text in report_types:
            ctk.CTkRadioButton(
                type_frame,
                text=text,
                variable=self.report_type,
                value=value,
                command=self._on_type_change
            ).pack(anchor="w", padx=20, pady=3)
        
        # Date range frame
        self.date_frame = ctk.CTkFrame(self)
        self.date_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            self.date_frame,
            text=self.app.get_translation("pdf_date_range_label"),
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Quick date buttons
        quick_frame = ctk.CTkFrame(self.date_frame, fg_color="transparent")
        quick_frame.pack(fill="x", padx=10, pady=5)
        
        self.date_preset = ctk.StringVar(value="today")
        presets = [
            ("today", self.app.get_translation("pdf_preset_today")),
            ("week", self.app.get_translation("pdf_preset_week")),
            ("month", self.app.get_translation("pdf_preset_month")),
            ("custom", self.app.get_translation("pdf_preset_custom")),
        ]
        
        for i, (value, text) in enumerate(presets):
            ctk.CTkRadioButton(
                quick_frame,
                text=text,
                variable=self.date_preset,
                value=value,
                command=self._on_preset_change,
                width=100
            ).grid(row=0, column=i, padx=5, pady=5)
        
        # Custom date inputs
        self.custom_date_frame = ctk.CTkFrame(self.date_frame, fg_color="transparent")
        self.custom_date_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.custom_date_frame, text=self.app.get_translation("pdf_from_date")).grid(row=0, column=0, padx=5)
        self.entry_from = ctk.CTkEntry(self.custom_date_frame, width=120, placeholder_text="DD/MM/YYYY")
        self.entry_from.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(self.custom_date_frame, text=self.app.get_translation("pdf_to_date")).grid(row=0, column=2, padx=5)
        self.entry_to = ctk.CTkEntry(self.custom_date_frame, width=120, placeholder_text="DD/MM/YYYY")
        self.entry_to.grid(row=0, column=3, padx=5)
        
        # Owner filter
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            filter_frame,
            text=self.app.get_translation("pdf_filter_owner"),
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        owners = [self.app.get_translation("all_owners")] + self._get_owners()
        self.owner_combo = ctk.CTkComboBox(filter_frame, values=owners, width=300)
        self.owner_combo.set(self.app.get_translation("all_owners"))
        self.owner_combo.pack(padx=10, pady=5)
        
        # Options
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text=self.app.get_translation("pdf_options"),
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.include_chart = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text=self.app.get_translation("pdf_include_chart"),
            variable=self.include_chart
        ).pack(anchor="w", padx=20, pady=3)
        
        self.include_details = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text=self.app.get_translation("pdf_include_details"),
            variable=self.include_details
        ).pack(anchor="w", padx=20, pady=3)
        
        # Progress bar (hidden initially)
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.progress_frame.pack_forget()  # Hide initially
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text=self.app.get_translation("btn_cancel"),
            command=self.destroy,
            width=120,
            fg_color="gray"
        ).pack(side="right", padx=5)
        
        self.btn_generate = ctk.CTkButton(
            btn_frame,
            text=self.app.get_translation("pdf_btn_generate"),
            command=self._generate_report,
            width=150,
            fg_color="#2ecc71"
        )
        self.btn_generate.pack(side="right", padx=5)
        
        # Initialize
        self._on_type_change()
        self._on_preset_change()
    
    def _get_owners(self):
        """Lấy danh sách chủ hàng."""
        try:
            vehicles = self.app.vehicle_manager.get_all()
            owners = list(set(v.get('owner', '') for v in vehicles if v.get('owner')))
            return sorted(owners)
        except:
            return []
    
    def _on_type_change(self):
        """Xử lý khi thay đổi loại báo cáo."""
        report_type = self.report_type.get()
        # Show/hide date range based on report type
        if report_type == "full_inventory":
            self.date_frame.pack_forget()
        else:
            if not self.date_frame.winfo_manager():  # Only pack if not already packed
                self.date_frame.pack(fill="x", padx=20, pady=10)
    
    def _on_preset_change(self):
        """Xử lý khi thay đổi preset ngày."""
        preset = self.date_preset.get()
        today = datetime.now()
        
        if preset == "today":
            from_date = today
            to_date = today
        elif preset == "week":
            from_date = today - timedelta(days=7)
            to_date = today
        elif preset == "month":
            from_date = today - timedelta(days=30)
            to_date = today
        else:  # custom
            return
        
        self.entry_from.delete(0, "end")
        self.entry_from.insert(0, from_date.strftime("%d/%m/%Y"))
        self.entry_to.delete(0, "end")
        self.entry_to.insert(0, to_date.strftime("%d/%m/%Y"))
    
    def _parse_date(self, date_str):
        """Parse date string to datetime."""
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        return None
    
    def _generate_report(self):
        """Tạo báo cáo PDF."""
        # Get parameters
        report_type = self.report_type.get()
        owner_filter = self.owner_combo.get()
        if owner_filter == self.app.get_translation("all_owners"):
            owner_filter = None
        
        # Parse dates
        from_date = self._parse_date(self.entry_from.get()) if self.entry_from.get() else datetime.now() - timedelta(days=30)
        to_date = self._parse_date(self.entry_to.get()) if self.entry_to.get() else datetime.now()
        
        if not from_date or not to_date:
            messagebox.showerror(
                self.app.get_translation("error_title"),
                self.app.get_translation("pdf_error_invalid_date")
            )
            return
        
        # Ask for save location
        default_name = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title=self.app.get_translation("pdf_save_dialog_title")
        )
        
        if not file_path:
            return
        
        # Show progress
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        self.progress_label.configure(text=self.app.get_translation("pdf_generating"))
        self.progress_bar.set(0)
        self.btn_generate.configure(state="disabled")
        
        # Generate in background
        def generate():
            try:
                self.after(100, lambda: self.progress_bar.set(0.2))
                
                # Collect data based on report type
                data = self._collect_report_data(report_type, from_date, to_date, owner_filter)
                
                self.after(200, lambda: self.progress_bar.set(0.5))
                
                # Generate PDF
                result = self._create_pdf(file_path, report_type, data, from_date, to_date)
                
                self.after(300, lambda: self.progress_bar.set(1.0))
                
                if result["success"]:
                    self.after(400, lambda: self._on_success(file_path))
                else:
                    self.after(400, lambda: self._on_error(result["message"]))
                    
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))
        
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def _collect_report_data(self, report_type, from_date, to_date, owner_filter):
        """Thu thập dữ liệu cho báo cáo."""
        from database.audit_repository import get_audit_repository
        
        if report_type == "stock_summary":
            # Báo cáo tồn kho theo chủ hàng
            vehicles = self.app.vehicle_manager.get_all()
            if owner_filter:
                vehicles = [v for v in vehicles if v.get('owner') == owner_filter]
            
            # Group by owner
            summary = {}
            for v in vehicles:
                owner = v.get('owner', 'Unknown')
                if owner not in summary:
                    summary[owner] = {'count': 0, 'vehicles': []}
                summary[owner]['count'] += 1
                summary[owner]['vehicles'].append(v)
            
            return {'type': 'stock_summary', 'summary': summary, 'total': len(vehicles)}
        
        elif report_type == "inbound_outbound":
            # Báo cáo nhập xuất
            audit_repo = get_audit_repository()
            entries = audit_repo.get_all(limit=10000)
            
            # Filter by date
            filtered = []
            for e in entries:
                if from_date <= e.timestamp <= to_date + timedelta(days=1):
                    if e.action.value in ['INBOUND', 'OUTBOUND', 'CREATE', 'DELETE']:
                        filtered.append(e)
            
            return {'type': 'inbound_outbound', 'entries': filtered}
        
        elif report_type == "shipped_vehicles":
            # Báo cáo xe đã xuất
            vehicles = self.app.vehicle_manager.get_shipped(from_date, to_date)
            if owner_filter:
                vehicles = [v for v in vehicles if v.get('owner') == owner_filter]
            return {'type': 'shipped_vehicles', 'vehicles': vehicles}
        
        elif report_type == "full_inventory":
            # Báo cáo chi tiết toàn bộ
            vehicles = self.app.vehicle_manager.get_all()
            if owner_filter:
                vehicles = [v for v in vehicles if v.get('owner') == owner_filter]
            return {'type': 'full_inventory', 'vehicles': vehicles}
        
        return {}
    
    def _create_pdf(self, file_path, report_type, data, from_date, to_date):
        """Tạo file PDF."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import cm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os
            import sys
            
            # Register fonts
            def get_app_root():
                if getattr(sys, 'frozen', False):
                    return os.path.dirname(sys.executable)
                return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            
            APP_ROOT = get_app_root()
            FONT_NAME, FONT_BOLD = "Helvetica", "Helvetica-Bold"
            
            font_path = os.path.join(APP_ROOT, "assets", "Arial.ttf")
            font_bold_path = os.path.join(APP_ROOT, "assets", "Arialbd.ttf")
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                FONT_NAME = "Arial"
            if os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
                FONT_BOLD = "Arial-Bold"
            
            # Create document
            doc = SimpleDocTemplate(
                file_path,
                pagesize=landscape(A4) if report_type != "stock_summary" else A4,
                leftMargin=1*cm,
                rightMargin=1*cm,
                topMargin=1*cm,
                bottomMargin=1*cm
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            style_title = ParagraphStyle(
                name='Title',
                fontName=FONT_BOLD,
                fontSize=16,
                alignment=1,
                spaceAfter=20
            )
            style_subtitle = ParagraphStyle(
                name='Subtitle',
                fontName=FONT_NAME,
                fontSize=11,
                alignment=1,
                spaceAfter=10
            )
            style_normal = ParagraphStyle(
                name='Normal',
                fontName=FONT_NAME,
                fontSize=10
            )
            
            # Title based on report type
            titles = {
                'stock_summary': self.app.get_translation("pdf_title_stock_summary"),
                'inbound_outbound': self.app.get_translation("pdf_title_inbound_outbound"),
                'shipped_vehicles': self.app.get_translation("pdf_title_shipped"),
                'full_inventory': self.app.get_translation("pdf_title_full_inventory"),
            }
            
            elements.append(Paragraph(titles.get(report_type, "Report"), style_title))
            elements.append(Paragraph(
                f"{self.app.get_translation('pdf_date_range_label')}: {from_date.strftime('%d/%m/%Y')} - {to_date.strftime('%d/%m/%Y')}",
                style_subtitle
            ))
            elements.append(Paragraph(
                f"{self.app.get_translation('pdf_generated_at')}: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                style_subtitle
            ))
            elements.append(Spacer(1, 20))
            
            # Content based on report type
            if report_type == "stock_summary" and 'summary' in data:
                # Stock summary table
                table_data = [[
                    self.app.get_translation("tree_owner"),
                    self.app.get_translation("pdf_col_count"),
                ]]
                
                total = 0
                for owner, info in sorted(data['summary'].items()):
                    table_data.append([owner, str(info['count'])])
                    total += info['count']
                
                table_data.append([self.app.get_translation("pdf_total_row"), str(total)])
                
                table = Table(table_data, colWidths=[12*cm, 4*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                    ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#D9E1F2")),
                    ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
                ]))
                elements.append(table)
            
            elif report_type == "shipped_vehicles" and 'vehicles' in data:
                # Shipped vehicles table
                table_data = [[
                    "STT",
                    self.app.get_translation("tree_vin"),
                    self.app.get_translation("tree_owner"),
                    self.app.get_translation("tree_type"),
                    self.app.get_translation("tree_date_out"),
                ]]
                
                for idx, v in enumerate(data['vehicles'], 1):
                    table_data.append([
                        str(idx),
                        v.get('vin', ''),
                        v.get('owner', ''),
                        v.get('vehicle_type', ''),
                        v.get('date_out', '')[:10] if v.get('date_out') else '',
                    ])
                
                if len(table_data) > 1:
                    table = Table(table_data, colWidths=[1.5*cm, 6*cm, 5*cm, 4*cm, 3*cm])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ]))
                    elements.append(table)
                else:
                    elements.append(Paragraph(self.app.get_translation("pdf_no_data"), style_normal))
            
            elif report_type == "full_inventory" and 'vehicles' in data:
                # Full inventory table
                table_data = [[
                    "STT",
                    self.app.get_translation("tree_vin"),
                    self.app.get_translation("tree_owner"),
                    self.app.get_translation("tree_type"),
                    self.app.get_translation("tree_location"),
                    self.app.get_translation("tree_date_in"),
                ]]
                
                for idx, v in enumerate(data['vehicles'], 1):
                    table_data.append([
                        str(idx),
                        v.get('vin', ''),
                        v.get('owner', ''),
                        v.get('vehicle_type', ''),
                        v.get('full_location_name', ''),
                        v.get('date_in', '')[:10] if v.get('date_in') else '',
                    ])
                
                if len(table_data) > 1:
                    table = Table(table_data, colWidths=[1.2*cm, 5*cm, 4*cm, 3.5*cm, 4*cm, 2.8*cm])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(table)
                else:
                    elements.append(Paragraph(self.app.get_translation("pdf_no_data"), style_normal))
            
            elif report_type == "inbound_outbound" and 'entries' in data:
                # Activity log
                elements.append(Paragraph(
                    f"{self.app.get_translation('pdf_total_activities')}: {len(data['entries'])}",
                    style_normal
                ))
                elements.append(Spacer(1, 10))
                
                # Count by action
                action_counts = {}
                for e in data['entries']:
                    action = e.action.value
                    action_counts[action] = action_counts.get(action, 0) + 1
                
                summary_data = [[self.app.get_translation("pdf_col_action"), self.app.get_translation("pdf_col_count")]]
                for action, count in sorted(action_counts.items()):
                    summary_data.append([action, str(count)])
                
                if len(summary_data) > 1:
                    table = Table(summary_data, colWidths=[8*cm, 4*cm])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                        ('FONTNAME', (0, 1), (-1, -1), FONT_NAME),
                        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(table)
            
            doc.build(elements)
            return {"success": True, "message": "OK"}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}
    
    def _on_success(self, file_path):
        """Xử lý khi tạo PDF thành công."""
        self.progress_label.configure(text=self.app.get_translation("pdf_success"))
        self.btn_generate.configure(state="normal")
        
        result = messagebox.askyesno(
            self.app.get_translation("success_title"),
            self.app.get_translation("pdf_success_open").format(path=file_path),
            parent=self
        )
        
        if result:
            os.startfile(file_path)
        
        self.destroy()
    
    def _on_error(self, error_msg):
        """Xử lý khi có lỗi."""
        self.progress_frame.pack_forget()
        self.btn_generate.configure(state="normal")
        messagebox.showerror(
            self.app.get_translation("error_title"),
            f"{self.app.get_translation('pdf_error')}: {error_msg}",
            parent=self
        )
