# ui/dashboard_tab.py
import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import logging
import os
import threading
import struct

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from io import BytesIO
import utils
from report_generators import pdf_generator # Cập nhật import

class DashboardTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance
        self.api_client = self.app.api_client
        self.current_dashboard_figure = None
        self.current_data = None
        self._auto_refresh_job = None

        filter_dash = ctk.CTkFrame(self.parent)
        filter_dash.pack(fill="x", pady=5, padx=5)
        
        self.dash_lbl_from = ctk.CTkLabel(filter_dash, text="", font=self.app.font_normal)
        self.dash_lbl_from.pack(side="left", padx=5, pady=10)
        self.dash_from = DateEntry(filter_dash, width=12, date_pattern="dd/mm/yyyy", font=("Arial", 12))
        self.dash_from.pack(side="left", padx=5, pady=10)
        
        self.dash_lbl_to = ctk.CTkLabel(filter_dash, text="", font=self.app.font_normal)
        self.dash_lbl_to.pack(side="left", padx=5, pady=10)
        self.dash_to = DateEntry(filter_dash, width=12, date_pattern="dd/mm/yyyy", font=("Arial", 12))
        self.dash_to.pack(side="left", padx=5, pady=10)
        
        self.btn_update_dash = ctk.CTkButton(filter_dash, text="", command=self.update_dashboard, font=self.app.font_normal)
        self.btn_update_dash.pack(side="left", padx=10, pady=10)
        
        self.btn_export_png = ctk.CTkButton(filter_dash, text="", command=self.export_dashboard_png, font=self.app.font_normal)
        self.btn_export_png.pack(side="left", padx=5, pady=10)
        
        self.btn_export_pdf = ctk.CTkButton(filter_dash, text="", command=self.export_dashboard_pdf, font=self.app.font_normal)
        self.btn_export_pdf.pack(side="left", padx=5, pady=10)

        auto_refresh_frame = ctk.CTkFrame(filter_dash, fg_color="transparent")
        auto_refresh_frame.pack(side="right", padx=10, pady=10)

        self.auto_refresh_var = ctk.BooleanVar()
        self.auto_refresh_check = ctk.CTkCheckBox(auto_refresh_frame, variable=self.auto_refresh_var, command=self._toggle_auto_refresh, font=self.app.font_normal)
        self.auto_refresh_check.pack(side="left")

        self.refresh_interval_entry = ctk.CTkEntry(auto_refresh_frame, width=40, font=self.app.font_normal)
        self.refresh_interval_entry.insert(0, "5")
        self.refresh_interval_entry.pack(side="left", padx=5)

        self.lbl_minutes = ctk.CTkLabel(auto_refresh_frame, text="", font=self.app.font_normal)
        self.lbl_minutes.pack(side="left")
        
        self.dashboard_chart_frame = ctk.CTkFrame(self.parent)
        self.dashboard_chart_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.update_language()

    def update_language(self):
        self.dash_lbl_from.configure(text=self.app.get_translation("lbl_from_date"))
        self.dash_lbl_to.configure(text=self.app.get_translation("lbl_to_date"))
        self.btn_update_dash.configure(text=self.app.get_translation("btn_update_dashboard"))
        self.btn_export_png.configure(text=self.app.get_translation("btn_export_png"))
        self.btn_export_pdf.configure(text=self.app.get_translation("btn_export_pdf"))
        self.auto_refresh_check.configure(text=self.app.get_translation("cbx_auto_refresh"))
        self.lbl_minutes.configure(text=self.app.get_translation("lbl_minutes"))

        if self.current_dashboard_figure:
            self.update_dashboard()

    def _toggle_auto_refresh(self):
        if self.auto_refresh_var.get():
            try:
                interval_minutes = int(self.refresh_interval_entry.get())
                if interval_minutes <= 0: raise ValueError
                self.app.show_toast(f"Đã bật tự động làm mới sau mỗi {interval_minutes} phút.")
                self._schedule_next_refresh(interval_minutes)
            except ValueError:
                messagebox.showwarning("Lỗi", "Vui lòng nhập một số nguyên dương cho khoảng thời gian.", parent=self.app)
                self.auto_refresh_var.set(False)
        else:
            if self._auto_refresh_job:
                self.parent.after_cancel(self._auto_refresh_job)
                self._auto_refresh_job = None
                self.app.show_toast("Đã tắt tự động làm mới.")

    def _schedule_next_refresh(self, interval_minutes):
        if self._auto_refresh_job:
            self.parent.after_cancel(self._auto_refresh_job)
        interval_ms = interval_minutes * 60 * 1000
        self._auto_refresh_job = self.parent.after(interval_ms, self.update_dashboard)

    def _create_summary_figure(self, report_data, start_dt, end_dt):
        sns.set_theme(style="whitegrid", font="Arial")
        plt.clf(); plt.cla()
        
        owners_list = [item['owner'] for item in report_data]
        nhap = [item['total_in'] for item in report_data]
        xuat = [item['total_out'] for item in report_data]
        ton = [item['stock'] for item in report_data]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.subplots_adjust(left=0.1, right=0.95, wspace=0.3, bottom=0.2)
        
        width = 0.25
        x = range(len(owners_list))
        
        ax1.bar([i - width for i in x], nhap, width=width, label=self.app.get_translation("db_bar_label_in"))
        ax1.bar(x, xuat, width=width, label=self.app.get_translation("db_bar_label_out"))
        ax1.bar([i + width for i in x], ton, width=width, label=self.app.get_translation("db_bar_label_stock"))
        ax1.set_xticks(x)
        ax1.set_xticklabels(owners_list, rotation=45, ha="right")
        ax1.set_title(self.app.get_translation("db_bar_chart_title"), fontsize=14, weight='bold')
        ax1.legend()
        
        pie_data = [(t, o) for t, o in zip(ton, owners_list) if t > 0]
        if pie_data:
            pie_ton, pie_labels = zip(*pie_data)
            colors = sns.color_palette('pastel')[0:len(pie_ton)]
            ax2.pie(pie_ton, labels=pie_labels, autopct='%1.1f%%', startangle=90, colors=colors)
        
        ax2.set_title(self.app.get_translation("db_pie_chart_title"), fontsize=14, weight='bold')
        ax2.set_aspect('equal')
        
        fig.suptitle(self.app.get_translation("db_main_title").format(start=start_dt.strftime('%d/%m/%Y'), end=end_dt.strftime('%d/%m/%Y')), fontsize=16, weight='bold')
        
        return fig

    def update_dashboard(self):
        if self.auto_refresh_var.get():
            try:
                interval_minutes = int(self.refresh_interval_entry.get())
                self._schedule_next_refresh(interval_minutes)
            except ValueError:
                self.auto_refresh_var.set(False)
                self._toggle_auto_refresh()
                return

        # Giải phóng memory từ các figures cũ trước khi tạo mới
        plt.close('all')
        if self.current_dashboard_figure:
            plt.close(self.current_dashboard_figure)
            self.current_dashboard_figure = None
        
        for widget in self.dashboard_chart_frame.winfo_children(): widget.destroy()
        loading_label = ctk.CTkLabel(self.dashboard_chart_frame, text=self.app.get_translation("status_loading"), font=self.app.font_small_italic)
        loading_label.pack(pady=20)
        self.app.status_var.set(self.app.get_translation("status_loading"))
        self.parent.update_idletasks()

        threading.Thread(target=self._load_dashboard_data_in_background, args=(loading_label,), daemon=True).start()

    def _load_dashboard_data_in_background(self, loading_label):
        start_dt = datetime.combine(self.dash_from.get_date(), datetime.min.time())
        end_dt = datetime.combine(self.dash_to.get_date(), datetime.max.time())
        
        try:
            report_data = self.api_client.get_export_summary(start_dt, end_dt)
            if self.parent.winfo_exists():
                self.app.after(0, self._draw_dashboard, report_data, start_dt, end_dt, loading_label)
        except Exception as e:
            if self.parent.winfo_exists():
                self.app.after(0, self._show_dashboard_error, e, loading_label)

    def _draw_dashboard(self, report_data, start_dt, end_dt, loading_label):
        if not self.parent.winfo_exists(): return
        
        loading_label.pack_forget()
        self.current_data = report_data
        
        if not self.current_data:
            messagebox.showinfo(self.app.get_translation("info_no_data_in_range"), self.app.get_translation("info_no_data_in_range_msg"))
            self.app.status_var.set(self.app.get_translation("status_ready"))
            return

        try:
            self.current_dashboard_figure = self._create_summary_figure(self.current_data, start_dt, end_dt)
            canvas = FigureCanvasTkAgg(self.current_dashboard_figure, master=self.dashboard_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(self.current_dashboard_figure)
            self.app.status_var.set(self.app.get_translation("status_ready"))
        except Exception as e:
            self._show_dashboard_error(e, loading_label)

    def _show_dashboard_error(self, error, loading_label):
        if not self.parent.winfo_exists(): return
        loading_label.pack_forget()
        messagebox.showerror(
            self.app.get_translation("dialog_error_title"), 
            self.app.get_translation("err_load_dashboard").format(error=error)
        )
        self.app.status_var.set(self.app.get_translation("status_error"))

    def export_dashboard_png(self):
        if not self.current_dashboard_figure:
            messagebox.showinfo(
                self.app.get_translation("warn_no_chart_title"), 
                self.app.get_translation("warn_no_chart_msg")
            )
            return
        
        default_name = utils.get_default_filename(self.app.get_translation("tab_dashboard"), ".png")
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")], initialfile=default_name)
        if not path: return
        
        try:
            self.current_dashboard_figure.savefig(path, bbox_inches="tight", dpi=150)
            self.app.show_toast(self.app.get_translation("toast_export_success"))
        except Exception as e:
            logging.exception("Lỗi khi xuất ảnh PNG")
            messagebox.showerror("Lỗi", f"Không thể lưu file ảnh: {e}")

    def export_dashboard_pdf(self):
        if not self.current_data:
            messagebox.showinfo("Chưa có dữ liệu", "Vui lòng cập nhật dashboard trước khi xuất báo cáo.")
            return

        default_name = utils.get_default_filename(self.app.get_translation("pdf_report_title"), ".pdf")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialfile=default_name)
        if not path: return
        
        start_dt = datetime.combine(self.dash_from.get_date(), datetime.min.time())
        end_dt = datetime.combine(self.dash_to.get_date(), datetime.max.time())

        result = pdf_generator.generate_dashboard_pdf(
            path=path,
            report_data=self.current_data,
            start_dt=start_dt,
            end_dt=end_dt,
            get_translation_func=self.app.get_translation
        )

        if result["success"]:
            self.app.show_toast(self.app.get_translation("toast_export_success"))
        else:
            messagebox.showerror("Lỗi Xuất PDF", result["message"])