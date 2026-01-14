"""
Import Bundles Dialog (Phase 3.4) - tkinter version

Allows users to select and import bundle files.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import threading
import os
import logging
from typing import List

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


class ImportBundlesDialog(ctk.CTkToplevel):
    """Dialog for importing bundle files."""

    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.lang = getattr(self.app, "current_language", "vi")
        self.title(get_text("dlg_import_bundles_title", self.lang))
        self.geometry("600x450")
        self.selected_files: List[str] = []

        self.setup_ui()
        self.grab_set()

    def setup_ui(self):
        """Setup dialog UI."""
        lang = self.lang
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # File selection
        file_label = ctk.CTkLabel(main_frame, text=get_text("dlg_bundle_files", lang), font=FONT_NORMAL)
        file_label.grid(row=0, column=0, sticky="w", pady=5)

        file_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        file_frame.grid(row=0, column=1, sticky="e", pady=5)

        add_btn = ctk.CTkButton(
            file_frame, text=get_text("dlg_add_files", lang), command=self.select_files, font=FONT_SMALL, width=80
        )
        add_btn.pack(side="left", padx=5)

        # File list
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
        main_frame.grid_rowconfigure(1, weight=1)

        self.file_listbox = ctk.CTkTextbox(list_frame, height=200, font=FONT_SMALL)
        self.file_listbox.pack(fill="both", expand=True)
        self.file_listbox.configure(state="disabled")

        # Progress bar
        self.progress_label = ctk.CTkLabel(main_frame, text="", font=FONT_SMALL)
        self.progress_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        self.progress_bar = ttk.Progressbar(main_frame, mode="determinate", length=400)
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text="", font=FONT_SMALL, text_color="gray")
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

        # Results label
        self.results_label = ctk.CTkLabel(main_frame, text="", font=FONT_SMALL)
        self.results_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=10)

        self.import_btn = ctk.CTkButton(
            button_frame, text=get_text("dlg_import", lang), command=self.import_bundles, font=FONT_NORMAL, state="disabled"
        )
        self.import_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            button_frame, text=get_text("dlg_clear", lang), command=self.clear_files, font=FONT_NORMAL
        )
        clear_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(
            button_frame, text=get_text("dlg_close", lang), command=self.destroy, font=FONT_NORMAL
        )
        close_btn.pack(side="left", padx=5)

    def select_files(self):
        """Select bundle files to import."""
        file_paths = filedialog.askopenfilenames(
            title=get_text("dlg_select_bundle_files", self.lang), filetypes=[("ZIP Files", "*.zip")], initialdir=getattr(config, "DEFAULT_IMPORT_FOLDER", "")
        )

        if file_paths:
            self.selected_files.extend(file_paths)
            self.update_file_list()

    def update_file_list(self):
        """Update file list display."""
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("0.0", "end")

        total_size = 0
        for file_path in self.selected_files:
            try:
                size = os.path.getsize(file_path)
                total_size += size
                size_mb = size / (1024 * 1024)
                file_name = os.path.basename(file_path)
                self.file_listbox.insert("end", f"{file_name} ({size_mb:.1f} MB)\n")
            except Exception:
                pass

        self.file_listbox.configure(state="disabled")

        self.import_btn.configure(state="normal" if len(self.selected_files) > 0 else "disabled")

        # Show total size
        if self.selected_files:
            total_mb = total_size / (1024 * 1024)
            self.status_label.configure(
                text=get_text("dlg_total_files", self.lang, count=len(self.selected_files), size=f"{total_mb:.1f}")
            )

    def clear_files(self):
        """Clear selected files."""
        self.selected_files.clear()
        self.update_file_list()
        self.results_label.configure(text="")

    def import_bundles(self):
        """Start import process."""
        if not self.selected_files:
            messagebox.showwarning(get_text("error_title", self.lang), get_text("dlg_error_select_files", self.lang))
            return

        self.import_btn.configure(state="disabled")
        self.progress_bar.configure(value=0)
        self.progress_label.configure(text=get_text("dlg_importing", self.lang))
        self.status_label.configure(text="")

        # Run import in background thread
        thread = threading.Thread(target=self._do_import)
        thread.daemon = True
        thread.start()

    def _do_import(self):
        """Execute import in background."""
        try:
            from tools.import_bundles import run_import_bundles

            total_files = len(self.selected_files)
            successful = 0
            failed = 0
            total_events = 0

            for idx, file_path in enumerate(self.selected_files):
                progress = int((idx / total_files) * 100)
                self.progress_bar.configure(value=progress)
                self.status_label.configure(text=get_text("dlg_importing_file", self.lang, filename=os.path.basename(file_path)))
                self.update()

                try:
                    result = run_import_bundles(file_path, auto_import=True)
                    if result.get("success"):
                        successful += 1
                        total_events += result.get("event_count", 0)
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Error importing {file_path}: {e}")
                    failed += 1

            self.progress_bar.configure(value=100)
            self.progress_label.configure(text=get_text("dlg_import_completed", self.lang))

            if failed == 0:
                self.results_label.configure(
                    text=get_text("dlg_import_success_all", self.lang, files=successful, events=total_events),
                    text_color="green"
                )
                messagebox.showinfo(
                    get_text("dlg_import_success_title", self.lang),
                    get_text("dlg_import_success_msg", self.lang, files=successful, events=total_events),
                )
            else:
                self.results_label.configure(
                    text=get_text("dlg_import_success_partial", self.lang, success=successful, failed=failed),
                    text_color="orange"
                )
                messagebox.showwarning(
                    get_text("dlg_import_partial_title", self.lang),
                    get_text("dlg_import_partial_msg", self.lang, success=successful, failed=failed, events=total_events),
                )

            self.import_btn.configure(state="normal")

        except Exception as e:
            logger.error(f"Import error: {e}", exc_info=True)
            self.results_label.configure(text=get_text("dlg_import_failed", self.lang, error=str(e)), text_color="red")
            messagebox.showerror(get_text("error_title", self.lang), get_text("dlg_import_failed", self.lang, error=str(e)))
            self.import_btn.configure(state="normal")


import config
