# ui/log_tab.py
import customtkinter as ctk
from utils import GUILoggingHandler, setup_logging

class LogTab:
    def __init__(self, parent_frame, app_instance):
        self.parent = parent_frame
        self.app = app_instance

        # === CẬP NHẬT: Thay đổi font chữ ===
        # Sử dụng font Arial, nhưng vẫn là mono-space nếu có thể (Courier New là tốt nhất cho log)
        # Nếu muốn đồng bộ hoàn toàn, dùng self.app.font_normal
        log_font = ctk.CTkFont(family="Arial", size=14)
        
        log_textbox = ctk.CTkTextbox(
            self.parent, 
            wrap="word", 
            state="disabled", 
            font=log_font
        )
        # ===================================
        
        log_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        gui_handler = GUILoggingHandler(log_textbox)
        setup_logging(gui_handler)
#(Lưu ý: Font `Arial` không phải là mono-space, log có thể sẽ không thẳng hàng đẹp như `Courier New`, nhưng nó sẽ đồng nhất với phần còn lại của ứng dụng.)*