# api_client.py
import logging

class ApiClient:
    """
    Lớp này đóng vai trò là một tầng giao tiếp dữ liệu (Data Access Layer).
    Ở Giai đoạn 2, nó gọi trực tiếp các manager CSDL.
    Trong Giai đoạn 3, nó sẽ được sửa đổi để gọi các API endpoint
    của một backend server qua mạng, mà không làm ảnh hưởng đến lớp UI.
    """
    def __init__(self, vehicle_manager, entity_manager, shipment_manager):
        """
        Khởi tạo ApiClient với các đối tượng manager CSDL.
        """
        self.vehicle_manager = vehicle_manager
        self.entity_manager = entity_manager
        self.shipment_manager = shipment_manager
        logging.info("ApiClient đã được khởi tạo ở chế độ Local Database.")

    def get_export_summary(self, start_date=None, end_date=None):
        """
        Lấy dữ liệu báo cáo tổng hợp.
        
        Giai đoạn 2: Gọi trực tiếp vehicle_manager.
        Giai đoạn 3: Sẽ gọi đến endpoint: GET /api/reports/summary
        """
        logging.info(f"ApiClient: Lấy dữ liệu báo cáo tổng hợp từ {start_date} đến {end_date}")
        try:
            # Trong tương lai, dòng này sẽ được thay thế bằng một cuộc gọi API
            # return httpx.get(f"http://127.0.0.1:8000/api/reports/summary", params={...}).json()
            return self.vehicle_manager.get_summary_report_data(start_date, end_date)
        except Exception as e:
            logging.error(f"Lỗi khi lấy dữ liệu báo cáo tổng hợp: {e}")
            return []

    # Trong tương lai, chúng ta có thể thêm các phương thức khác ở đây, ví dụ:
    #
    # def get_all_vehicles_in_stock(self):
    #     """
    #     Giai đoạn 3: Sẽ gọi đến endpoint: GET /api/vehicles/in-stock
    #     """
    #     # return httpx.get("http://127.0.0.1:8000/api/vehicles/in-stock").json()
    #     pass
    #
    # def add_new_vehicle(self, vehicle_data):
    #     """
    #     Giai đoạn 3: Sẽ gọi đến endpoint: POST /api/vehicles
    #     """
    #     # return httpx.post("http://127.0.0.1:8000/api/vehicles", json=vehicle_data).json()
    #     pass