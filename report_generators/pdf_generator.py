# report_generators/pdf_generator.py
import logging
import os
import sys
from datetime import datetime
from io import BytesIO
import qrcode

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from reportlab.lib import colors # Import module colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import utils

def _get_app_root():
    """
    Lấy đường dẫn thư mục gốc của ứng dụng một cách đáng tin cậy.
    Sửa lại để trỏ ra ngoài thư mục report_generators.
    """
    if getattr(sys, 'frozen', False):
        # Nếu là file .exe, thư mục gốc là nơi chứa file .exe
        return os.path.dirname(sys.executable)
    else:
        # Nếu chạy từ source code, đi lùi lại một cấp từ thư mục hiện tại (__file__)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def generate_vehicle_tag_pdf(file_path, vehicle_info):
    """Tạo một file PDF chứa QR code cho một chiếc xe."""
    try:
        APP_ROOT = _get_app_root()
        FONT_NAME, FONT_BOLD = "Helvetica", "Helvetica-Bold"
        font_path = os.path.join(APP_ROOT, "assets", "Arial.ttf")
        font_bold_path = os.path.join(APP_ROOT, "assets", "Arialbd.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Arial', font_path))
            FONT_NAME = "Arial"
        if os.path.exists(font_bold_path):
            pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
            FONT_BOLD = "Arial-Bold"
        else:
            FONT_BOLD = FONT_NAME

        qr_data = vehicle_info.get('vin', '')
        if not qr_data:
            return {"success": False, "message": "Không có số VIN để tạo mã QR."}
            
        qr_img = qrcode.make(qr_data, error_correction=qrcode.constants.ERROR_CORRECT_L, border=1)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        # === TỐI ƯU HÓA KÍCH THƯỚC ===
        # Kích thước trang: 7cm rộng, 4cm cao
        page_width, page_height = (8*cm, 4.5*cm)
        # Giảm lề xuống mức tối thiểu
        margin = 0.2 * cm
        doc = SimpleDocTemplate(
        file_path,
        pagesize=(page_width, page_height),
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
)
        
        # Giảm kích thước font và khoảng cách dòng
        style_normal = ParagraphStyle(name='Normal', fontName=FONT_NAME, fontSize=7, leading=8)
        style_bold_vin = ParagraphStyle(name='Bold', fontName=FONT_BOLD, fontSize=7, leading=9)
        
        elements = []

        vin = vehicle_info.get('vin', 'N/A')
        owner = vehicle_info.get('owner', 'N/A')
        location = vehicle_info.get('full_location_name', 'N/A')
        date_in = utils.format_datetime_for_display(vehicle_info.get('date_in', ''))

        # Giảm kích thước ảnh QR một chút
        qr_image = Image(qr_buffer, width=2.2*cm, height=2.2*cm)

        data = [
            [Paragraph('<b>SỐ KHUNG:</b>', style_normal), Paragraph(vin, style_bold_vin)],
            [Paragraph('<b>CHỦ HÀNG:</b>', style_normal), Paragraph(owner, style_normal)],
            [Paragraph('<b>VỊ TRÍ:</b>', style_normal), Paragraph(location, style_normal)],
            [Paragraph('<b>NGÀY VÀO:</b>', style_normal), Paragraph(date_in, style_normal)],
        ]
        
        info_table = Table(data)
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Tính toán độ rộng các cột chính một cách chính xác
        qr_col_width = 2.5 * cm
        # Không gian còn lại cho bảng thông tin = (Tổng rộng - 2*lề) - rộng cột QR
        info_col_width = (page_width - 2*margin) - qr_col_width
        
        main_table = Table([[qr_image, info_table]], colWidths=[2.3*cm, info_col_width]) 
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        # =================================

        elements.append(main_table)
        doc.build(elements)
        
        logging.info(f"Đã tạo QR code PDF thành công cho xe {vin} tại {file_path}")
        return {"success": True, "message": "Tạo QR code thành công."}

    except Exception as e:
        logging.exception("Lỗi khi tạo QR code PDF")
        return {"success": False, "message": str(e)}

def generate_dashboard_pdf(path, report_data, start_dt, end_dt, get_translation_func):
    """Tạo báo cáo PDF cho dashboard thống kê với font chữ tiếng Việt chính xác."""
    try:
        APP_ROOT = _get_app_root()
        FONT_NAME = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"
        
        font_path = os.path.join(APP_ROOT, "assets", "Arial.ttf")
        font_bold_path = os.path.join(APP_ROOT, "assets", "Arialbd.ttf")

        logging.debug(f"PDF font search path: {font_path}")

        try:
            if os.path.exists(font_path) and os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                pdfmetrics.registerFont(TTFont('Arial-Bold', font_bold_path))
                pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold')
                FONT_NAME = "Arial"
                FONT_BOLD = "Arial-Bold"
                logging.debug("PDF font Arial registered successfully.")
            else:
                logging.warning("Không tìm thấy file Arial.ttf hoặc Arialbd.ttf trong thư mục /assets. Sử dụng font Helvetica mặc định.")
        except Exception as e:
            logging.warning(f"Lỗi khi đăng ký font Arial: {e}. Sử dụng font Helvetica mặc định.")

        # --- Vẽ biểu đồ ---
        sns.set_theme(style="whitegrid", font="Arial")
        plt.clf(); plt.cla()
        
        owners_list = [item['owner'] for item in report_data]
        nhap = [item['total_in'] for item in report_data]
        xuat = [item['total_out'] for item in report_data]
        ton = [item['stock'] for item in report_data]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.subplots_adjust(left=0.1, right=0.95, wspace=0.3, bottom=0.2)
        
        width = 0.25; x = range(len(owners_list))
        
        ax1.bar([i - width for i in x], nhap, width=width, label=get_translation_func("db_bar_label_in"))
        ax1.bar(x, xuat, width=width, label=get_translation_func("db_bar_label_out"))
        ax1.bar([i + width for i in x], ton, width=width, label=get_translation_func("db_bar_label_stock"))
        ax1.set_xticks(x); ax1.set_xticklabels(owners_list, rotation=45, ha="right")
        ax1.set_title(get_translation_func("db_bar_chart_title"), fontsize=14, weight='bold')
        ax1.legend()
        
        pie_data = [(t, o) for t, o in zip(ton, owners_list) if t > 0]
        if pie_data:
            pie_ton, pie_labels = zip(*pie_data)
            # === SỬA LỖI: Đổi tên biến để tránh xung đột ===
            pie_colors = sns.color_palette('pastel')[0:len(pie_ton)]
            ax2.pie(pie_ton, labels=pie_labels, autopct='%1.1f%%', startangle=90, colors=pie_colors)
            # ============================================
        
        ax2.set_title(get_translation_func("db_pie_chart_title"), fontsize=14, weight='bold')
        ax2.set_aspect('equal')
        
        fig.suptitle(get_translation_func("db_main_title").format(start=start_dt.strftime('%d/%m/%Y'), end=end_dt.strftime('%d/%m/%Y')), fontsize=16, weight='bold')
        
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)
        chart_image = Image(buf, width=24*cm, height=9*cm)

        # --- Xây dựng tài liệu PDF ---
        styles = getSampleStyleSheet()
        style_center = ParagraphStyle(name="Center", alignment=1, fontSize=11, fontName=FONT_NAME, allow_tags=1)
        style_h1_center = ParagraphStyle(name="H1Center", alignment=1, fontSize=16, fontName=FONT_BOLD)
        
        now = datetime.now()
        shift = get_translation_func("pdf_shift_day") if 6 <= now.hour < 18 else get_translation_func("pdf_shift_night")

        header_texts = [
            Paragraph(get_translation_func("pdf_report_title"), style_h1_center),
            Spacer(1, 0.2*cm),
            Paragraph(get_translation_func("pdf_shift").format(shift=shift), style_center),
            Paragraph(get_translation_func("pdf_date_range").format(start=start_dt.strftime('%d/%m/%Y'), end=end_dt.strftime('%d/%m/%Y')), style_center),
            Paragraph(get_translation_func("pdf_report_date").format(date=now.strftime("%d/%m/%Y %H:%M")), style_center),
        ]
        logo_path = os.path.join(APP_ROOT, "assets", "Logo.jpg")
        logo = Image(logo_path, width=2*cm, height=2*cm) if os.path.exists(logo_path) else Spacer(0,0)
        header_table = Table([[header_texts, logo]], colWidths=['*', 2.5*cm])
        header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

        data_rows = []
        total_nhap, total_xuat, total_ton = 0, 0, 0
        for idx, item in enumerate(report_data, 1):
            nhap, xuat, ton = item['total_in'], item['total_out'], item['stock']
            total_nhap += nhap; total_xuat += xuat; total_ton += ton
            data_rows.append([idx, item['owner'], nhap, xuat, ton])
        table_data = [[get_translation_func("tree_stt"), get_translation_func("tree_owner"), get_translation_func("pdf_col_total_in"), get_translation_func("pdf_col_total_out"), get_translation_func("pdf_col_stock")]] + data_rows
        table_data.append(["", get_translation_func('pdf_total_row'), total_nhap, total_xuat, total_ton])
        
        summary_table = Table(table_data, colWidths=[1.5*cm, 7*cm, 4*cm, 4*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD), ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.grey), ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#D9E1F2")),
            ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD), ('FONTNAME', (0, 1), (-1, -2), FONT_NAME),
        ]))

        main_layout_table = Table([[header_table], [summary_table], [chart_image]], rowHeights=[3.5*cm, None, 9.5*cm])
        
        doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
        doc.build([main_layout_table])
        
        return {"success": True, "message": "Tạo báo cáo PDF thành công."}
    except Exception as e:
        logging.exception("Lỗi khi xuất báo cáo PDF")
        return {"success": False, "message": str(e)}