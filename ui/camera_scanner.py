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
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.app = parent
        self.title(self.app.get_translation("camera_scanner_title"))
        self.geometry("660x520")
        self.result = None

        self.cap = None
        self.is_running = False
        self.thread = None
        
        # Khởi tạo bộ nhận diện QR code của OpenCV
        self.qr_decoder = cv2.QRCodeDetector()

        self.label_info = ctk.CTkLabel(self, text=self.app.get_translation("camera_scanner_instruction"), font=ctk.CTkFont(weight="bold"))
        self.label_info.pack(pady=10)

        self.canvas = ctk.CTkCanvas(self, width=640, height=480, highlightthickness=0)
        self.canvas.pack()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # Bắt đầu camera sau một khoảng trễ nhỏ để cửa sổ kịp hiển thị
        self.after(100, self.start_camera)

        self.grab_set()
        self.wait_window()

    def start_camera(self):
        """Khởi tạo và bắt đầu luồng video từ webcam."""
        try:
            # Thử mở webcam mặc định (index 0)
            self.cap = cv2.VideoCapture(0)
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
                
                current_time = time.time()
                # Giới hạn tần suất quét để tiết kiệm CPU (ví dụ: 2 lần/giây)
                if current_time - last_scan_time > 0.5:
                    data, _, _ = self.qr_decoder.detectAndDecode(frame)
                    
                    if data:
                        self.result = data
                        # Lên lịch gọi hàm thành công trên luồng chính
                        self.app.after(0, self.on_scan_success)
                        return # Thoát khỏi vòng lặp
                    
                    last_scan_time = current_time

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