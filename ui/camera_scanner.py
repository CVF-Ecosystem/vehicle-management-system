# ui/camera_scanner.py
import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import time

class CameraScannerDialog(ctk.CTkToplevel):
    """
    Một hộp thoại Toplevel để mở webcam, quét mã QR (chứa số VIN),
    và trả về kết quả.
    Cải tiến: Hỗ trợ chọn camera, flash/torch, zoom, lịch sử quét.
    """
    def __init__(self, parent, camera_index=0):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.title(self.app.get_translation("camera_scanner_title"))
        self.geometry("700x600")
        self.result = None
        self.camera_index = camera_index

        self.cap = None
        self.is_running = False
        self.thread = None
        self.zoom_level = 1.0
        self.scan_history = []
        self.flash_on = False
        
        # Khởi tạo bộ nhận diện QR code của OpenCV
        self.qr_decoder = cv2.QRCodeDetector()
        
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # Bắt đầu camera sau một khoảng trễ nhỏ để cửa sổ kịp hiển thị
        self.after(100, self.start_camera)

        self.grab_set()
        self.wait_window()
    
    def _build_ui(self):
        """Xây dựng giao diện cải tiến."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        # Camera selection
        ctk.CTkLabel(toolbar, text=self.app.get_translation("camera_select")).pack(side="left", padx=5)
        self.camera_var = ctk.StringVar(value="0")
        self.camera_combo = ctk.CTkComboBox(
            toolbar,
            values=["0", "1", "2"],
            variable=self.camera_var,
            width=60,
            command=self._change_camera
        )
        self.camera_combo.pack(side="left", padx=5)
        
        # Zoom controls
        ctk.CTkLabel(toolbar, text=self.app.get_translation("camera_zoom")).pack(side="left", padx=(20, 5))
        self.zoom_slider = ctk.CTkSlider(
            toolbar,
            from_=1.0,
            to=3.0,
            number_of_steps=20,
            width=100,
            command=self._change_zoom
        )
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="left", padx=5)
        
        self.zoom_label = ctk.CTkLabel(toolbar, text="1.0x", width=40)
        self.zoom_label.pack(side="left")
        
        # Scan mode
        self.continuous_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            toolbar,
            text=self.app.get_translation("camera_continuous"),
            variable=self.continuous_var,
            width=120
        ).pack(side="right", padx=10)

        # Info label
        self.label_info = ctk.CTkLabel(
            self,
            text=self.app.get_translation("camera_scanner_instruction"),
            font=ctk.CTkFont(weight="bold")
        )
        self.label_info.pack(pady=5)

        # Canvas for video
        self.canvas = ctk.CTkCanvas(self, width=640, height=400, highlightthickness=2, highlightbackground="#3498db")
        self.canvas.pack(pady=5)
        
        # Scan history panel
        history_frame = ctk.CTkFrame(self)
        history_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            history_frame,
            text=self.app.get_translation("camera_history"),
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=10)
        
        self.history_label = ctk.CTkLabel(
            history_frame,
            text=self.app.get_translation("camera_no_scans"),
            text_color="gray"
        )
        self.history_label.pack(side="left", padx=10)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text=self.app.get_translation("btn_cancel"),
            command=self.on_close,
            width=100,
            fg_color="gray"
        ).pack(side="right", padx=5)
        
        self.manual_btn = ctk.CTkButton(
            btn_frame,
            text=self.app.get_translation("camera_manual_input"),
            command=self._manual_input,
            width=120
        )
        self.manual_btn.pack(side="right", padx=5)

    def _change_camera(self, value):
        """Đổi camera."""
        new_index = int(value)
        if new_index != self.camera_index:
            self.camera_index = new_index
            self.is_running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)
            if self.cap:
                self.cap.release()
            self.after(100, self.start_camera)
    
    def _change_zoom(self, value):
        """Thay đổi mức zoom."""
        self.zoom_level = float(value)
        self.zoom_label.configure(text=f"{self.zoom_level:.1f}x")
    
    def _manual_input(self):
        """Nhập VIN thủ công."""
        dialog = ctk.CTkInputDialog(
            text=self.app.get_translation("camera_enter_vin"),
            title=self.app.get_translation("camera_manual_input")
        )
        vin = dialog.get_input()
        if vin and vin.strip():
            self.result = vin.strip().upper()
            self.on_scan_success()
    
    def _update_history(self, code):
        """Cập nhật lịch sử quét."""
        if code not in self.scan_history:
            self.scan_history.insert(0, code)
            if len(self.scan_history) > 5:
                self.scan_history.pop()
        
        history_text = " | ".join(self.scan_history[:3])
        self.history_label.configure(text=history_text, text_color="green")

    def start_camera(self):
        """Khởi tạo và bắt đầu luồng video từ webcam."""
        try:
            # Thử mở webcam với index được chọn
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self.label_info.configure(text=self.app.get_translation("camera_error_open"), text_color="red")
                return

            self.is_running = True
            self.thread = threading.Thread(target=self.video_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            error_msg = self.app.get_translation("camera_error_generic").format(e=e)
            self.label_info.configure(text=error_msg, text_color="red")

    def video_loop(self):
        """Vòng lặp chạy trong luồng riêng để liên tục đọc frame từ camera."""
        last_scan_time = 0
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                # Lật ảnh để có hiệu ứng "gương soi", tự nhiên hơn cho người dùng
                frame = cv2.flip(frame, 1)
                
                # Áp dụng zoom
                if self.zoom_level > 1.0:
                    h, w = frame.shape[:2]
                    center_x, center_y = w // 2, h // 2
                    new_w, new_h = int(w / self.zoom_level), int(h / self.zoom_level)
                    x1 = max(0, center_x - new_w // 2)
                    y1 = max(0, center_y - new_h // 2)
                    x2 = min(w, x1 + new_w)
                    y2 = min(h, y1 + new_h)
                    frame = frame[y1:y2, x1:x2]
                    frame = cv2.resize(frame, (w, h))
                
                # Vẽ khung hướng dẫn quét
                h, w = frame.shape[:2]
                box_size = min(w, h) // 2
                x1 = (w - box_size) // 2
                y1 = (h - box_size) // 2
                cv2.rectangle(frame, (x1, y1), (x1 + box_size, y1 + box_size), (0, 255, 0), 2)
                
                current_time = time.time()
                # Giới hạn tần suất quét để tiết kiệm CPU (ví dụ: 2 lần/giây)
                if current_time - last_scan_time > 0.5:
                    data, points, _ = self.qr_decoder.detectAndDecode(frame)
                    
                    if data:
                        # Vẽ khung xanh quanh QR code nếu phát hiện
                        if points is not None and len(points) > 0:
                            pts = points[0].astype(int)
                            cv2.polylines(frame, [pts], True, (0, 255, 0), 3)
                        
                        self.result = data
                        self.app.after(0, lambda d=data: self._update_history(d))
                        
                        # Kiểm tra chế độ quét liên tục
                        if not self.continuous_var.get():
                            # Lên lịch gọi hàm thành công trên luồng chính
                            self.app.after(0, self.on_scan_success)
                            return # Thoát khỏi vòng lặp
                    
                    last_scan_time = current_time

                # Resize frame cho canvas (400 height)
                frame = cv2.resize(frame, (640, 400))
                
                # Chuyển đổi ảnh sang định dạng mà Tkinter có thể hiển thị
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img)
                img_tk = ImageTk.PhotoImage(image=img_pil)
                
                # Lên lịch cập nhật canvas trên luồng chính
                self.app.after(0, self.update_canvas, img_tk)
                
                time.sleep(0.03) # Nghỉ ngắn để tránh chiếm 100% CPU
            except Exception:
                # Bỏ qua các lỗi có thể xảy ra trong vòng lặp (ví dụ: camera bị ngắt kết nối)
                pass

    def update_canvas(self, img_tk):
        """Cập nhật hình ảnh trên canvas một cách an toàn."""
        if self.winfo_exists():
            self.canvas.create_image(0, 0, anchor=ctk.NW, image=img_tk)
            # Giữ một tham chiếu đến ảnh để tránh bị garbage collector xóa mất
            self.canvas.image = img_tk

    def on_scan_success(self):
        """Được gọi khi quét mã thành công."""
        self.app.show_toast(f"Đã quét thành công: {self.result}")
        self.on_close()

    def on_close(self):
        """Dọn dẹp tài nguyên khi cửa sổ bị đóng."""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        if self.cap:
            self.cap.release()
        self.destroy()