# main.py
"""
Entry point for Vehicle Management System.
Application logic lives in ui/app_controller.py (CQ-05).
"""
from __future__ import annotations

import logging

from ui.app_controller import InventoryApp
from database.base_manager import BaseManager
from utils import setup_logging


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Khởi động ứng dụng Vehicle Management System.")
    try:
        app = InventoryApp()
        app.mainloop()
    finally:
        BaseManager.close_connection()
        logger.info("Ứng dụng đã đóng.")


if __name__ == "__main__":
    main()
