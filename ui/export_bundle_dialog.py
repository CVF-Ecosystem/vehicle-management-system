"""
Export Bundle Dialog (Phase 3.4) - tkinter version

Allows users to export site bundles with date range selection.
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


class ExportBundleDialog(ctk.CTkToplevel):
    """Dialog for exporting site bundles."""

    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.lang = getattr(self.app, "current_language", "vi")
        self.title(get_text("dlg_export_bundle_title", self.lang))
        self.geometry("500x350")
        self.output_folder = None
        self.result = None

        self.setup_ui()
        self.grab_set()

    def setup_ui(self):
        """Setup dialog UI."""
        lang = self.lang
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Period selection
        period_label = ctk.CTkLabel(main_frame, text=get_text("dlg_export_period", lang), font=FONT_NORMAL)
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

        # Options
        options_label = ctk.CTkLabel(main_frame, text=get_text("dlg_options", lang), font=FONT_NORMAL)
        options_label.grid(row=2, column=0, sticky="w", pady=10)

        self.include_transfers = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            main_frame, text=get_text("dlg_include_transfers", lang), variable=self.include_transfers, font=FONT_SMALL
        ).grid(row=3, column=0, sticky="w", padx=20, pady=2)

        self.include_dedup = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            main_frame, text=get_text("dlg_include_dedup", lang), variable=self.include_dedup, font=FONT_SMALL
        ).grid(row=4, column=0, sticky="w", padx=20, pady=2)

        # Output selection
        output_label = ctk.CTkLabel(main_frame, text=get_text("dlg_output_location", lang), font=FONT_NORMAL)
        output_label.grid(row=5, column=0, sticky="w", pady=10)

        output_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        output_frame.grid(row=6, column=0, sticky="ew", pady=5)

        self.output_label = ctk.CTkLabel(output_frame, text=get_text("dlg_select_location", lang), font=FONT_SMALL, text_color="gray")
        self.output_label.pack(side="left", fill="x", expand=True)

        browse_btn = ctk.CTkButton(
            output_frame, text=get_text("dlg_browse", lang), command=self.select_output_folder, font=FONT_SMALL, width=80
        )
        browse_btn.pack(side="left", padx=5)

        # Progress bar
        self.progress_label = ctk.CTkLabel(main_frame, text="", font=FONT_SMALL)
        self.progress_label.grid(row=7, column=0, sticky="w", pady=5)

        self.progress_bar = ttk.Progressbar(main_frame, mode="determinate", length=400)
        self.progress_bar.grid(row=8, column=0, sticky="ew", pady=5)

        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="", font=FONT_SMALL, text_color="gray")
        self.status_label.grid(row=9, column=0, sticky="w", pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=10, column=0, sticky="e", pady=10)

        self.export_btn = ctk.CTkButton(
            button_frame, text=get_text("dlg_export", lang), command=self.export, font=FONT_NORMAL
        )
        self.export_btn.pack(side="left", padx=5)

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

    def export(self):
        """Start export process."""
        if not self.output_folder:
            messagebox.showwarning(get_text("error_title", self.lang), get_text("dlg_error_select_folder", self.lang))
            return

        self.export_btn.configure(state="disabled")
        self.progress_bar.configure(value=0)
        self.progress_label.configure(text=get_text("dlg_exporting", self.lang))
        self.status_label.configure(text="")

        # Run export in background thread
        thread = threading.Thread(target=self._do_export)
        thread.daemon = True
        thread.start()

    def _do_export(self):
        """Execute export in background."""
        try:
            from tools.export_site_bundle import export_bundle

            period_from = self.from_date.get()
            period_to = self.to_date.get()

            self.progress_bar.configure(value=30)
            self.status_label.configure(text=get_text("dlg_exporting_events", self.lang))
            self.update()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"site_bundle_{timestamp}.zip"
            output_file = os.path.join(self.output_folder, file_name)

            result = export_bundle(
                period_from=period_from, period_to=period_to, output_path=output_file
            )

            self.progress_bar.configure(value=90)
            self.status_label.configure(text=get_text("dlg_finalizing", self.lang))
            self.update()

            if result.get("success"):
                self.progress_bar.configure(value=100)
                self.progress_label.configure(text=get_text("dlg_export_completed", self.lang))
                self.result = output_file

                reply = messagebox.askyesno(
                    get_text("dlg_export_success_title", self.lang),
                    get_text("dlg_export_success_msg", self.lang, path=output_file),
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
            else:
                messagebox.showerror(get_text("error_title", self.lang), get_text("dlg_export_failed", self.lang, error=result.get('error')))
                self.export_btn.configure(state="normal")
                self.progress_label.configure(text="")
                self.status_label.configure(text="")

        except Exception as e:
            logger.error(f"Export error: {e}", exc_info=True)
            messagebox.showerror(get_text("error_title", self.lang), get_text("dlg_export_failed", self.lang, error=str(e)))
            self.export_btn.configure(state="normal")
            self.progress_label.configure(text="")
