# ui/tab_manager.py
"""
TabManager — quản lý tab switching, lazy refresh và data-change propagation.

Được tạo ra bằng cách tách logic tab khỏi InventoryApp (CQ-05).
InventoryApp tạo và inject TabManager; các tab object được register sau khi build.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    import customtkinter as ctk
    from ui.inbound_tab import InboundTab
    from ui.outbound_tab import OutboundTab
    from ui.stock_tab import StockTab
    from ui.dispatch_tab import DispatchTab
    from ui.search_tab import SearchTab
    from ui.yard_map_tab import YardMapTab
    from ui.dashboard_tab import DashboardTab
    from ui.log_tab import LogTab

logger = logging.getLogger(__name__)


class TabManager:
    """
    Quản lý toàn bộ vòng đời của các tab trong InventoryApp:
    - Lazy-load khi tab được chọn
    - Propagate data-change events
    - Delegate keyboard shortcuts liên quan đến tab
    """

    def __init__(self, app: Any) -> None:
        """
        Args:
            app: InventoryApp instance (ctk.CTk subclass).
                 Cần có: app.tabs (CTkTabview), app.get_translation(), app.auth_manager.
        """
        self._app = app

        # Tab objects — được gán sau khi _build_tabs() hoàn thành
        self.inbound_tab: Optional[Any] = None
        self.dispatch_tab: Optional[Any] = None
        self.outbound_tab: Optional[Any] = None
        self.stock_tab: Optional[Any] = None
        self.search_tab: Optional[Any] = None
        self.yard_map_tab: Optional[Any] = None
        self.dashboard_tab: Optional[Any] = None
        self.log_tab: Optional[Any] = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_tabs(
        self,
        inbound_tab: Any,
        dispatch_tab: Any,
        outbound_tab: Any,
        stock_tab: Any,
        search_tab: Any,
        yard_map_tab: Any,
        dashboard_tab: Any,
        log_tab: Any,
    ) -> None:
        """Gán tất cả tab objects sau khi chúng được khởi tạo."""
        self.inbound_tab = inbound_tab
        self.dispatch_tab = dispatch_tab
        self.outbound_tab = outbound_tab
        self.stock_tab = stock_tab
        self.search_tab = search_tab
        self.yard_map_tab = yard_map_tab
        self.dashboard_tab = dashboard_tab
        self.log_tab = log_tab

    # ------------------------------------------------------------------
    # Translation helper (delegates to app)
    # ------------------------------------------------------------------

    def _t(self, key: str) -> str:
        return self._app.get_translation(key)

    # ------------------------------------------------------------------
    # Tab switching / lazy loading
    # ------------------------------------------------------------------

    def on_tab_change(self) -> None:
        """Gọi khi người dùng chuyển tab (từ CTkTabview command callback)."""
        if hasattr(self._app, "auth_manager"):
            self._app.auth_manager.refresh_session()

        selected = self._app.tabs.get()

        if selected == self._t("tab_stock") and self.stock_tab:
            self.stock_tab.refresh_all()
        elif selected == self._t("tab_dispatch") and self.dispatch_tab:
            self.dispatch_tab.update_dropdowns()
            self.dispatch_tab.load_open_dispatch()
        elif selected == self._t("tab_inbound") and self.inbound_tab:
            self.inbound_tab.update_dropdowns()
        elif selected == self._t("tab_outbound") and self.outbound_tab:
            self.outbound_tab.update_dropdowns()

    def on_data_changed(self) -> None:
        """
        Propagate data-change event sang các tab cần thiết.
        Chỉ refresh tab đang active để tránh lãng phí tài nguyên.
        """
        logger.info("Phát hiện thay đổi dữ liệu, đang làm mới tab hiện tại.")
        if hasattr(self._app, "auth_manager"):
            self._app.auth_manager.refresh_session()

        # Luôn cập nhật dropdowns nhẹ (không query nhiều)
        for tab in (self.inbound_tab, self.outbound_tab, self.dispatch_tab):
            if tab and hasattr(tab, "update_dropdowns"):
                tab.update_dropdowns()

        # Chỉ refresh stock_tab nếu đang active
        if hasattr(self._app, "tabs") and self.stock_tab:
            try:
                if self._app.tabs.get() == self._t("tab_stock"):
                    self.stock_tab.refresh_all()
            except Exception:
                self.stock_tab.refresh_all()

    # ------------------------------------------------------------------
    # Shortcut helpers
    # ------------------------------------------------------------------

    def refresh_active_tab(self) -> None:
        """F5 — Làm mới tab đang hiển thị."""
        selected = self._app.tabs.get()

        if selected == self._t("tab_stock") and self.stock_tab:
            self.stock_tab.refresh_all()
        elif selected == self._t("tab_inbound") and self.inbound_tab:
            self.inbound_tab.update_dropdowns()
        elif selected == self._t("tab_dispatch") and self.dispatch_tab:
            self.dispatch_tab.update_dropdowns()
            self.dispatch_tab.load_open_dispatch()
        elif selected == self._t("tab_outbound") and self.outbound_tab:
            self.outbound_tab.update_dropdowns()
        elif selected == self._t("tab_search") and self.search_tab:
            if hasattr(self.search_tab, "perform_search"):
                self.search_tab.perform_search()
        elif selected == self._t("tab_yard_map") and self.yard_map_tab:
            if hasattr(self.yard_map_tab, "refresh_data"):
                self.yard_map_tab.refresh_data()
        elif selected == self._t("tab_dashboard") and self.dashboard_tab:
            if hasattr(self.dashboard_tab, "update_dashboard"):
                self.dashboard_tab.update_dashboard()

    def switch_to(self, tab_key: str, focus_attr: Optional[str] = None) -> None:
        """
        Chuyển sang tab theo translation key.

        Args:
            tab_key: key translation, ví dụ "tab_inbound"
            focus_attr: attribute name trên tab object để focus sau 100ms
        """
        tab_name = self._t(tab_key)
        self._app.tabs.set(tab_name)

        if focus_attr:
            tab_obj = getattr(self, tab_key.replace("tab_", "") + "_tab", None)
            if tab_obj and hasattr(tab_obj, focus_attr):
                self._app.after(100, lambda: getattr(tab_obj, focus_attr).focus_set())

    def update_all_languages(self) -> None:
        """Cập nhật ngôn ngữ cho tất cả tab."""
        for tab in (
            self.inbound_tab, self.dispatch_tab, self.outbound_tab, self.stock_tab,
            self.search_tab, self.yard_map_tab, self.dashboard_tab,
        ):
            if tab and hasattr(tab, "update_language"):
                tab.update_language()
