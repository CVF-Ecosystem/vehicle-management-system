import os
from typing import Dict, List

import pandas as pd

from report_generators.excel_generator import _format_excel_sheet


def generate_central_excel_report(
    path: str,
    period_from: str,
    period_to: str,
    overall: Dict,
    per_site_rows: List[Dict],
    per_owner_rows: List[Dict],
):
    """Generate multi-sheet Excel report from central merged DB data."""

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    df_overall = pd.DataFrame(
        [
            {
                "Từ ngày": period_from,
                "Đến ngày": period_to,
                "Tổng Nhập": int(overall.get("total_in", 0)),
                "Tổng Xuất": int(overall.get("total_out", 0)),
                "Tồn cuối kỳ": int(overall.get("stock_end", 0)),
                "Số bundle": int(overall.get("bundles_count", 0)),
            }
        ]
    )

    df_site = pd.DataFrame(per_site_rows or [])
    if not df_site.empty:
        df_site = df_site.rename(
            columns={
                "site_code": "Mã bãi",
                "total_in": "Nhập",
                "total_out": "Xuất",
                "stock_end": "Tồn cuối kỳ",
                "bundles_count": "Số bundle",
                "last_period_to": "Kỳ cuối (đến ngày)",
            }
        )

    df_owner = pd.DataFrame(per_owner_rows or [])
    if not df_owner.empty:
        df_owner = df_owner.rename(
            columns={
                "owner": "Chủ hàng/Đại lý",
                "total_in": "Nhập",
                "total_out": "Xuất",
                "stock_end": "Tồn cuối kỳ",
            }
        )

    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df_overall.to_excel(writer, index=False, sheet_name="Tổng kỳ")
            ws = writer.sheets["Tổng kỳ"]
            _format_excel_sheet(ws, has_total_row=False)

            df_site.to_excel(writer, index=False, sheet_name="Theo bãi")
            ws = writer.sheets["Theo bãi"]
            _format_excel_sheet(ws, has_total_row=False)

            df_owner.to_excel(writer, index=False, sheet_name="Theo chủ hàng")
            ws = writer.sheets["Theo chủ hàng"]
            _format_excel_sheet(ws, has_total_row=False)

        return {"success": True, "message": "Xuất báo cáo tổng hợp thành công."}

    except IOError:
        return {
            "success": False,
            "message": f"Không thể ghi file. Vui lòng đảm bảo file '{os.path.basename(path)}' không đang được mở.",
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
