# ui/voucher_creation_dialog.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from datetime import datetime
import os
import voucher_generator
from ui.components import add_right_click_menu # === BỔ SUNG MỚI ===
from utils import save_config # === BỔ SUNG MỚI ===

class VoucherCreationDialog(ctk.CTkToplevel):
    def __init__(self, parent, default_output_filename=""):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.title(self.app.get_translation("dialog_create_vouchers_title"))
        self.geometry("700x500")

        # === TÍNH NĂNG MỚI: Đọc các đường dẫn đã lưu ===
        saved_template_path = self.app.config.get("Paths", "last_voucher_template", fallback="")
        saved_excel_path = self.app.config.get("Paths", "last_data_excel", fallback="")
        # =============================================

        self.excel_path = ctk.StringVar()
        self.template_path = ctk.StringVar(value=saved_template_path)
        self.output_path = ctk.StringVar(value=default_output_filename)

        data_frame = ctk.CTkFrame(self)
        data_frame.pack(pady=10, padx=10, fill="x")
        data_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(data_frame, text=self.app.get_translation("lbl_excel_file_path"), font=self.app.font_normal).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        excel_entry = ctk.CTkEntry(data_frame, textvariable=self.excel_path, font=self.app.font_normal)
        excel_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, excel_entry) # === BỔ SUNG MỚI ===
        ctk.CTkButton(data_frame, text=self.app.get_translation("btn_select_file"), font=self.app.font_normal, command=lambda: self.excel_path.set(filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")]))).grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(data_frame, text=self.app.get_translation("lbl_word_template_path"), font=self.app.font_normal).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        template_entry = ctk.CTkEntry(data_frame, textvariable=self.template_path, font=self.app.font_normal)
        template_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, template_entry) # === BỔ SUNG MỚI ===
        ctk.CTkButton(data_frame, text=self.app.get_translation("btn_select_template"), font=self.app.font_normal, command=lambda: self.template_path.set(filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")]))).grid(row=1, column=2, padx=5, pady=5)

        ctk.CTkLabel(data_frame, text=self.app.get_translation("lbl_output_file_path"), font=self.app.font_normal).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        output_entry = ctk.CTkEntry(data_frame, textvariable=self.output_path, font=self.app.font_normal)
        output_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        add_right_click_menu(self.app, output_entry) # === BỔ SUNG MỚI ===
        ctk.CTkButton(data_frame, text=self.app.get_translation("btn_save_as"), font=self.app.font_normal, command=lambda: self.output_path.set(filedialog.asksaveasfilename(defaultextension=".docx", initialfile=self.output_path.get(), filetypes=[("Word Documents", "*.docx")]))).grid(row=2, column=2, padx=5, pady=5)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkButton(action_frame, text=self.app.get_translation("btn_create_vouchers"), command=self.create_vouchers, font=self.app.font_bold, height=40).pack(fill="x")

        log_frame = ctk.CTkFrame(self)
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.log_text = ctk.CTkTextbox(log_frame, wrap="word", font=("Courier New", 12))
        self.log_text.pack(fill="both", expand=True)
        add_right_click_menu(self.app, self.log_text) # === BỔ SUNG MỚI ===
        self.log(self.app.get_translation("log_ready"))

        self.grab_set()
        self.wait_window()

    def log(self, message):
        if self.winfo_exists():
            self.log_text.insert("end", f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.log_text.see("end")

    def create_vouchers(self):
        excel_file = self.excel_path.get()
        template_file = self.template_path.get()
        output_file = self.output_path.get()

        if not all([excel_file, template_file, output_file]):
            messagebox.showerror("Lỗi", self.app.get_translation("msgbox_fill_all_paths"), parent=self)
            return
        # === TÍNH NĂNG MỚI: Lưu lại các đường dẫn vừa sử dụng ===
        self.app.config.set("Paths", "last_voucher_template", template_file)
        self.app.config.set("Paths", "last_data_excel", excel_file)
        save_config(self.app.config) # Gọi hàm save_config từ utils
        # =====================================================

        def worker():
            result = voucher_generator.create_vouchers_from_excel(
                excel_path=excel_file,
                template_path=template_file,
                output_path=output_file,
                log_callback=self.log
            )
            
            if self.winfo_exists():
                if result["success"]:
                    self.log(self.app.get_translation("log_success").format(path=output_file))
                    if messagebox.askyesno(self.app.get_translation("msgbox_creation_complete_title"), self.app.get_translation("msgbox_creation_complete_prompt"), parent=self):
                        try:
                            os.startfile(output_file)
                        except Exception as e:
                            messagebox.showerror("Lỗi", f"Không thể tự động mở file:\n{e}", parent=self)
                else:
                    error_msg = result["message"]
                    self.log(self.app.get_translation("log_critical_error").format(error=error_msg))
                    messagebox.showerror("Lỗi", f"Đã xảy ra lỗi không xác định:\n{error_msg}", parent=self)

        threading.Thread(target=worker, daemon=True).start()