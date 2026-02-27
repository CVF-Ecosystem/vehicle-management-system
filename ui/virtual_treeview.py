# ui/virtual_treeview.py
"""
Virtual Treeview — Treeview với virtual scrolling cho hiệu suất cao (7.4-PERF-1).

Khi có >10.000 bản ghi, Treeview thông thường bị lag vì load toàn bộ vào memory.
Module này cung cấp:
1. VirtualTreeview: Chỉ render các row đang hiển thị
2. PaginatedTreeview: Phân trang với lazy loading

Usage:
    # Thay thế Treeview thông thường:
    tree = PaginatedTreeview(parent, columns=cols, page_size=100)
    tree.set_data_source(lambda offset, limit: vm.get_in_stock(offset=offset, limit=limit))
    tree.set_count_source(lambda: vm.get_in_stock_count())
    tree.load_page(0)
"""

import customtkinter as ctk
from tkinter import ttk
import logging
from typing import Callable, Optional, List, Any

logger = logging.getLogger(__name__)


class PaginatedTreeview:
    """
    Treeview với phân trang để xử lý dataset lớn hiệu quả.
    
    Thay vì load toàn bộ dữ liệu, chỉ load N rows mỗi trang.
    Giảm memory usage và tăng tốc độ render đáng kể.
    """

    DEFAULT_PAGE_SIZE = 100

    def __init__(
        self,
        parent,
        columns: dict,
        page_size: int = DEFAULT_PAGE_SIZE,
        **treeview_kwargs
    ):
        """
        Args:
            parent: Parent widget
            columns: Dict {column_id: display_name}
            page_size: Số rows mỗi trang
            **treeview_kwargs: Kwargs truyền vào ttk.Treeview
        """
        self.parent = parent
        self.columns = columns
        self.page_size = page_size
        self._current_page = 0
        self._total_count = 0
        self._data_source: Optional[Callable] = None
        self._count_source: Optional[Callable] = None

        self._build_ui(**treeview_kwargs)

    def _build_ui(self, **kwargs):
        """Xây dựng UI với Treeview và pagination controls."""
        # Main frame
        self.frame = ctk.CTkFrame(self.parent)

        # Treeview
        col_ids = list(self.columns.keys())
        self.tree = ttk.Treeview(
            self.frame,
            columns=col_ids,
            show="headings",
            **kwargs
        )

        # Configure columns
        for col_id, col_name in self.columns.items():
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=120, minwidth=60)

        # Scrollbars
        vsb = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Pagination controls
        self._build_pagination_controls()

    def _build_pagination_controls(self):
        """Xây dựng thanh điều hướng trang."""
        self.pagination_frame = ctk.CTkFrame(self.parent, height=35)

        self.btn_first = ctk.CTkButton(
            self.pagination_frame, text="⏮", width=35,
            command=lambda: self.load_page(0)
        )
        self.btn_prev = ctk.CTkButton(
            self.pagination_frame, text="◀", width=35,
            command=self._prev_page
        )
        self.page_label = ctk.CTkLabel(
            self.pagination_frame, text="Trang 1/1", width=120
        )
        self.btn_next = ctk.CTkButton(
            self.pagination_frame, text="▶", width=35,
            command=self._next_page
        )
        self.btn_last = ctk.CTkButton(
            self.pagination_frame, text="⏭", width=35,
            command=self._last_page
        )
        self.count_label = ctk.CTkLabel(
            self.pagination_frame, text="0 bản ghi", width=100
        )

        self.btn_first.pack(side="left", padx=2)
        self.btn_prev.pack(side="left", padx=2)
        self.page_label.pack(side="left", padx=5)
        self.btn_next.pack(side="left", padx=2)
        self.btn_last.pack(side="left", padx=2)
        self.count_label.pack(side="right", padx=10)

    def pack(self, **kwargs):
        """Pack the main frame."""
        self.frame.pack(**kwargs)
        self.pagination_frame.pack(fill="x", padx=5, pady=2)

    def grid(self, **kwargs):
        """Grid the main frame."""
        self.frame.grid(**kwargs)
        self.pagination_frame.grid(row=kwargs.get("row", 0) + 1, column=kwargs.get("column", 0))

    def set_data_source(self, func: Callable[[int, int], List[dict]]):
        """
        Đặt hàm lấy dữ liệu.
        
        Args:
            func: Callable(offset, limit) -> List[dict]
        """
        self._data_source = func

    def set_count_source(self, func: Callable[[], int]):
        """
        Đặt hàm đếm tổng số bản ghi.
        
        Args:
            func: Callable() -> int
        """
        self._count_source = func

    def load_page(self, page: int):
        """
        Load một trang dữ liệu.
        
        Args:
            page: Số trang (0-indexed)
        """
        if not self._data_source:
            return

        # Update total count
        if self._count_source:
            try:
                self._total_count = self._count_source()
            except Exception as e:
                logger.error(f"Error getting count: {e}")
                self._total_count = 0

        total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
        page = max(0, min(page, total_pages - 1))
        self._current_page = page

        offset = page * self.page_size

        try:
            data = self._data_source(offset, self.page_size)
        except Exception as e:
            logger.error(f"Error loading page {page}: {e}")
            data = []

        # Clear and repopulate
        self.tree.delete(*self.tree.get_children())
        for row in data:
            values = [row.get(col, "") for col in self.columns.keys()]
            self.tree.insert("", "end", values=values)

        # Update pagination UI
        self._update_pagination_ui(total_pages)

    def _update_pagination_ui(self, total_pages: int):
        """Cập nhật UI phân trang."""
        current = self._current_page + 1
        self.page_label.configure(text=f"Trang {current}/{total_pages}")
        self.count_label.configure(text=f"{self._total_count:,} bản ghi")

        self.btn_first.configure(state="normal" if self._current_page > 0 else "disabled")
        self.btn_prev.configure(state="normal" if self._current_page > 0 else "disabled")
        self.btn_next.configure(state="normal" if self._current_page < total_pages - 1 else "disabled")
        self.btn_last.configure(state="normal" if self._current_page < total_pages - 1 else "disabled")

    def _prev_page(self):
        if self._current_page > 0:
            self.load_page(self._current_page - 1)

    def _next_page(self):
        total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
        if self._current_page < total_pages - 1:
            self.load_page(self._current_page + 1)

    def _last_page(self):
        total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
        self.load_page(total_pages - 1)

    def refresh(self):
        """Reload trang hiện tại."""
        self.load_page(self._current_page)

    def get_selected_values(self) -> Optional[tuple]:
        """Lấy values của row đang được chọn."""
        selected = self.tree.selection()
        if selected:
            return self.tree.item(selected[0])["values"]
        return None
