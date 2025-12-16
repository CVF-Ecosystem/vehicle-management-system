# voucher_generator.py
import pandas as pd
import qrcode
from docxtpl import DocxTemplate, InlineImage, RichText
from docx.shared import Cm
import logging
import os
from datetime import datetime
from data_normalizer import normalizer

def create_vouchers_from_excel(excel_path, template_path, output_path, log_callback):
    """
    Một hàm độc lập, chịu trách nhiệm cho toàn bộ quy trình tạo phiếu vận chuyển.
    """
    temp_qr_files = []
    try:
        # --- 1. Đọc và Chuẩn hóa Dữ liệu Excel ---
        log_callback("Bắt đầu đọc file Excel...")
        df = pd.read_excel(excel_path, dtype=str).fillna('')
        log_callback(f"Đã đọc {len(df)} dòng từ file Excel.")
        
        df.columns = [c.strip().lower() for c in df.columns]
        rename_map = {
            'so khung': 'vin', 'chu hang': 'owner', 'loai xe': 'vehicle_type',
            'so cont': 'so_cont', 'ngay cb': 'ngay_cb', 'tau': 'tau',
            'chuyen': 'chuyen', 'so kg': 'so_kg'
        }
        df = df.rename(columns=rename_map)

        vehicle_data_list = df.to_dict('records')
        
        # --- 2. Chuẩn bị Context cho Template Word ---
        log_callback("Đang chuẩn bị dữ liệu và tạo mã QR...")
        doc = DocxTemplate(template_path)
        items_context = []
        now = datetime.now()
        
        rt_date = RichText(font='Times New Roman', size=24)
        rt_date.add(f"Ngày {str(now.day).zfill(2)} tháng {str(now.month).zfill(2)} năm {str(now.year)}")
        
        for i, vehicle in enumerate(vehicle_data_list, 1):
            vin = str(vehicle.get('vin', '')).strip().upper()
            if not vin: continue

            qr_img = qrcode.make(vin, error_correction=qrcode.constants.ERROR_CORRECT_L)
            qr_path = f"temp_qr_{vin}.png"
            qr_img.save(qr_path)
            temp_qr_files.append(qr_path)
            
            qr_image = InlineImage(doc, qr_path, width=Cm(3))
            
            # Định dạng lại ngày tháng
            ngay_cb_raw = vehicle.get('ngay_cb')
            ngay_cb_formatted = ngay_cb_raw
            if ngay_cb_raw:
                try:
                    dt_obj = pd.to_datetime(ngay_cb_raw)
                    ngay_cb_formatted = dt_obj.strftime('%d/%m/%Y')
                except ValueError:
                    pass

            items_context.append({
                'phieu_so': str(i).zfill(3),
                'phieu_so_footer': str(i),
                'ngay_thang_nam': rt_date,
                'ten_tau': vehicle.get('tau', 'N/A'),
                'ngay_cb': ngay_cb_formatted,
                'chuyen': vehicle.get('chuyen', 'N/A'),
                'chu_hang': normalizer.normalize_owner(str(vehicle.get('owner', ''))),
                'so_cont': vehicle.get('so_cont', 'N/A'),
                'loai_xe': normalizer.normalize_vehicle_type(str(vehicle.get('vehicle_type', ''))),
                'so_khung': vin,
                'so_kg': vehicle.get('so_kg', 'N/A'),
                'qr_code': qr_image
            })

        # --- 3. Render và Lưu file Word ---
        log_callback("Bắt đầu tạo file Word...")
        context = {'items': items_context}
        doc.render(context)
        doc.save(output_path)

        logging.info(f"Đã tạo thành công file phiếu vận chuyển tại: {output_path}")
        return {"success": True, "message": "Tạo file thành công."}

    except Exception as e:
        logging.exception("Lỗi khi tạo phiếu vận chuyển từ Excel")
        return {"success": False, "message": str(e)}
    
    finally:
        for qr_file in temp_qr_files:
            if os.path.exists(qr_file):
                os.remove(qr_file)
        if temp_qr_files:
            logging.info(f"Đã dọn dẹp {len(temp_qr_files)} file QR tạm.")