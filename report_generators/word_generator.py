# report_generators/word_generator.py
import qrcode
from docxtpl import DocxTemplate, InlineImage, RichText
from docx.shared import Cm
import logging
import os
from datetime import datetime

def generate_transport_vouchers_word(template_path, output_path, vehicle_data_list):
    """
    Tạo hàng loạt phiếu vận chuyển từ một template Word (định dạng Jinja2),
    bao gồm cả việc chèn ảnh QR Code một cách hiệu quả.
    """
    temp_qr_files = []
    try:
        doc = DocxTemplate(template_path)
        
        items_context = []
        now = datetime.now()
        
        # Tạo đối tượng RichText để kiểm soát font và size cho ngày tháng
        rt_date = RichText(font='Times New Roman', size=24) # size=24 tương đương 12pt
        rt_date.add(f"Ngày {str(now.day).zfill(2)} tháng {str(now.month).zfill(2)} năm {str(now.year)}")
        
        for i, vehicle in enumerate(vehicle_data_list, 1):
            vin = vehicle.get('vin', 'N/A')
            
            # Tạo ảnh QR và lưu vào file tạm
            qr_img = qrcode.make(vin, error_correction=qrcode.constants.ERROR_CORRECT_L)
            qr_path = f"temp_qr_{vin}.png"
            qr_img.save(qr_path)
            temp_qr_files.append(qr_path)
            
            # Tạo đối tượng InlineImage cho docxtpl
            qr_image = InlineImage(doc, qr_path, width=Cm(3))
            
            items_context.append({
                'phieu_so': str(i).zfill(3),
                'phieu_so_footer': str(i),
                'ngay_thang_nam': rt_date,
                'ten_tau': vehicle.get('tau', 'N/A'),
                'ngay_cb': vehicle.get('ngay_cb', 'N/A'),
                'chuyen': vehicle.get('chuyen', 'N/A'),
                'chu_hang': vehicle.get('owner', 'N/A'),
                'so_cont': vehicle.get('so_cont', 'N/A'),
                'loai_xe': vehicle.get('vehicle_type', 'N/A'),
                'so_khung': vin,
                'so_kg': vehicle.get('so_kg', 'N/A'),
                'qr_code': qr_image
            })

        context = {
            'items': items_context
        }
        doc.render(context)
        doc.save(output_path)

        logging.info(f"Đã tạo thành công file phiếu vận chuyển tại: {output_path}")
        return {"success": True, "message": "Tạo file thành công."}

    except Exception as e:
        logging.exception("Lỗi khi tạo phiếu vận chuyển Word bằng docxtpl")
        return {"success": False, "message": str(e)}
    
    finally:
        # Dọn dẹp các file ảnh QR tạm
        for qr_file in temp_qr_files:
            if os.path.exists(qr_file):
                os.remove(qr_file)
        if temp_qr_files:
            logging.info(f"Đã dọn dẹp {len(temp_qr_files)} file QR tạm.")