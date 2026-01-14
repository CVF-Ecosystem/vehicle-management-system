"""
Generate Report Dialog (Phase 3.4) - tkinter version

Allows users to generate HQ reports with various options.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import threading
from datetime import datetime, timedelta
import os
import logging

import config
from translations import translations

# Font definitions
FONT_NORMAL = ("Segoe UI", 13)
FONT_SMALL = ("Segoe UI", 11)


def get_text(key, lang="vi", **kwargs):
    """Get translated text."""
    text = translations.get(key, {}).get(lang, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


logger = logging.getLogger(__name__)


class GenerateReportDialog(ctk.CTkToplevel):
    """Dialog for generating HQ reports."""

    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.lang = getattr(self.app, "current_language", "vi")
        self.title(get_text("dlg_generate_report_title", self.lang))
        self.geometry("500x500")
        self.output_folder = None

        self.setup_ui()
        self.grab_set()

    def setup_ui(self):
        """Setup dialog UI."""
        lang = self.lang
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Period selection
        period_label = ctk.CTkLabel(main_frame, text=get_text("dlg_period", lang), font=FONT_NORMAL)
        period_label.grid(row=0, column=0, sticky="w", pady=5)

        period_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        period_frame.grid(row=1, column=0, sticky="ew", pady=5)

        ctk.CTkLabel(period_frame, text=get_text("dlg_from", lang), font=FONT_SMALL).pack(side="left", padx=5)
        self.from_date = ctk.CTkEntry(period_frame, width=120, font=FONT_SMALL)
        self.from_date.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.from_date.pack(side="left", padx=5)

        ctk.CTkLabel(period_frame, text=get_text("dlg_to", lang), font=FONT_SMALL).pack(side="left", padx=5)
        self.to_date = ctk.CTkEntry(period_frame, width=120, font=FONT_SMALL)
        self.to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.to_date.pack(side="left", padx=5)

        # Report type selection
        report_label = ctk.CTkLabel(main_frame, text=get_text("dlg_report_type", lang), font=FONT_NORMAL)
        report_label.grid(row=2, column=0, sticky="w", pady=10)

        self.report_type = ctk.StringVar(value="consolidated")

        report_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        report_frame.grid(row=3, column=0, sticky="w", padx=20, pady=5)

        ctk.CTkRadioButton(
            report_frame,
            text=get_text("dlg_report_vehicle_movements", lang),
            variable=self.report_type,
            value="vehicle_movements",
            font=FONT_SMALL,
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            report_frame,
            text=get_text("dlg_report_site_summary", lang),
            variable=self.report_type,
            value="site_summary",
            font=FONT_SMALL,
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            report_frame,
            text=get_text("dlg_report_transfer_reconciliation", lang),
            variable=self.report_type,
            value="transfer_reconciliation",
            font=FONT_SMALL,
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            report_frame,
            text=get_text("dlg_report_consolidated", lang),
            variable=self.report_type,
            value="consolidated",
            font=FONT_SMALL,
        ).pack(anchor="w", pady=2)

        # Options
        options_label = ctk.CTkLabel(main_frame, text=get_text("dlg_options", lang), font=FONT_NORMAL)
        options_label.grid(row=4, column=0, sticky="w", pady=10)

        self.dedup_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            main_frame,
            text=get_text("dlg_enable_dedup", lang),
            variable=self.dedup_var,
            font=FONT_SMALL,
        ).grid(row=5, column=0, sticky="w", padx=20, pady=2)

        # Output selection
        output_label = ctk.CTkLabel(main_frame, text=get_text("dlg_save_to", lang), font=FONT_NORMAL)
        output_label.grid(row=6, column=0, sticky="w", pady=10)

        output_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        output_frame.grid(row=7, column=0, sticky="ew", pady=5)

        self.output_label = ctk.CTkLabel(
            output_frame, text=get_text("dlg_select_location", lang), font=FONT_SMALL, text_color="gray"
        )
        self.output_label.pack(side="left", fill="x", expand=True)

        browse_btn = ctk.CTkButton(
            output_frame, text=get_text("dlg_browse", lang), command=self.select_output_folder, font=FONT_SMALL, width=80
        )
        browse_btn.pack(side="left", padx=5)

        # Progress bar
        self.progress_label = ctk.CTkLabel(main_frame, text="", font=FONT_SMALL)
        self.progress_label.grid(row=8, column=0, sticky="w", pady=5)

        self.progress_bar = ttk.Progressbar(main_frame, mode="determinate", length=400)
        self.progress_bar.grid(row=9, column=0, sticky="ew", pady=5)

        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="", font=FONT_SMALL, text_color="gray")
        self.status_label.grid(row=10, column=0, sticky="w", pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=11, column=0, sticky="e", pady=10)

        self.generate_btn = ctk.CTkButton(
            button_frame, text=get_text("dlg_generate", lang), command=self.generate_report, font=FONT_NORMAL
        )
        self.generate_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            button_frame, text=get_text("btn_cancel", lang), command=self.destroy, font=FONT_NORMAL
        )
        cancel_btn.pack(side="left", padx=5)

    def select_output_folder(self):
        """Select output folder."""
        folder = filedialog.askdirectory(
            title=get_text("dlg_select_output_folder", self.lang), initialdir=getattr(config, "DEFAULT_EXPORT_FOLDER", "")
        )
        if folder:
            self.output_folder = folder
            self.output_label.configure(text=folder, text_color="white")

    def generate_report(self):
        """Start report generation."""
        if not self.output_folder:
            messagebox.showwarning(get_text("error_title", self.lang), get_text("dlg_error_select_folder", self.lang))
            return

        self.generate_btn.configure(state="disabled")
        self.progress_bar.configure(value=0)
        self.progress_label.configure(text=get_text("dlg_generating", self.lang))
        self.status_label.configure(text="")

        # Run report generation in background thread
        thread = threading.Thread(target=self._do_generate)
        thread.daemon = True
        thread.start()

    def _do_generate(self):
        """Execute report generation in background."""
        try:
            from reporting.central_report_dedup import CentralReportGenerator

            period_from = self.from_date.get()
            period_to = self.to_date.get()
            report_type = self.report_type.get()
            enable_dedup = self.dedup_var.get()

            self.progress_bar.configure(value=20)
            self.status_label.configure(text=get_text("dlg_loading_data", self.lang))
            self.update()

            central_db = getattr(config, "CENTRAL_DB_PATH", "data/central_report.db")
            security_db = getattr(config, "SECURITY_DB_PATH", "data/security.db")

            gen = CentralReportGenerator(central_db, security_db, enable_dedup=enable_dedup)

            self.progress_bar.configure(value=40)

            # Generate based on type
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if report_type == "vehicle_movements":
                self.status_label.configure(text=get_text("dlg_generating_vehicle_movements", self.lang))
                output_file = os.path.join(self.output_folder, f"vehicle_movements_{timestamp}.csv")
                gen.export_vehicle_movement_csv(period_from, period_to, output_file)

            elif report_type == "site_summary":
                self.status_label.configure(text=get_text("dlg_generating_site_summary", self.lang))
                output_file = os.path.join(self.output_folder, f"site_summary_{timestamp}.csv")
                gen.export_site_summary_csv(period_from, period_to, output_file)

            elif report_type == "transfer_reconciliation":
                self.status_label.configure(text=get_text("dlg_generating_transfer_reconciliation", self.lang))
                output_file = os.path.join(
                    self.output_folder, f"transfer_reconciliation_{timestamp}.csv"
                )
                gen.export_transfer_summary_csv(period_from, period_to, output_file)

            elif report_type == "consolidated":
                self.status_label.configure(text=get_text("dlg_generating_consolidated", self.lang))
                output_file = os.path.join(
                    self.output_folder, f"hq_report_consolidated_{timestamp}.csv"
                )
                gen.export_consolidated_report(period_from, period_to, output_file)

            self.progress_bar.configure(value=90)
            self.status_label.configure(text=get_text("dlg_finalizing", self.lang))
            self.update()

            self.progress_bar.configure(value=100)
            self.progress_label.configure(text=get_text("dlg_report_generated", self.lang))

            reply = messagebox.askyesno(
                get_text("dlg_report_success_title", self.lang),
                get_text("dlg_report_success_msg", self.lang, path=output_file),
            )

            if reply:
                import subprocess
                import platform

                if platform.system() == "Windows":
                    subprocess.Popen(f'explorer /select,"{output_file}"')
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", "-R", output_file])
                else:
                    subprocess.Popen(["xdg-open", os.path.dirname(output_file)])

            self.destroy()

        except Exception as e:
            logger.error(f"Report generation error: {e}", exc_info=True)
            messagebox.showerror(get_text("error_title", self.lang), get_text("dlg_report_failed", self.lang, error=str(e)))
            self.generate_btn.configure(state="normal")
            self.progress_label.configure(text="")
