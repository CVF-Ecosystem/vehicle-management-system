# core/update_checker.py
"""
Update Checker — Kiểm tra phiên bản mới của ứng dụng (7.6-DEPLOY-1).

Kiểm tra GitHub Releases API để phát hiện phiên bản mới.
Chạy trong background thread để không block UI.
"""

import logging
import threading
from typing import Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# GitHub repository info — thay đổi theo repo thực tế
GITHUB_OWNER = "Blackbird081"
GITHUB_REPO = "vehicle-management-system"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Kiểm tra tối đa 1 lần mỗi 24 giờ
CHECK_INTERVAL_HOURS = 24


class UpdateChecker:
    """
    Kiểm tra phiên bản mới từ GitHub Releases.
    
    Usage:
        checker = UpdateChecker(current_version="1.0.0")
        checker.check_async(callback=lambda info: print(info))
    """

    def __init__(self, current_version: str):
        """
        Args:
            current_version: Phiên bản hiện tại (SemVer, ví dụ: "1.0.0")
        """
        self.current_version = current_version
        self._last_check: Optional[datetime] = None
        self._latest_info: Optional[dict] = None

    def check_async(
        self,
        callback: Optional[Callable[[Optional[dict]], None]] = None,
        force: bool = False
    ) -> None:
        """
        Kiểm tra phiên bản mới trong background thread.
        
        Args:
            callback: Hàm được gọi với kết quả. Nhận dict hoặc None.
                      dict có keys: version, url, release_notes, is_newer
            force: Bỏ qua cache và kiểm tra ngay
        """
        if not force and self._last_check:
            elapsed = datetime.now() - self._last_check
            if elapsed < timedelta(hours=CHECK_INTERVAL_HOURS):
                if callback and self._latest_info:
                    callback(self._latest_info)
                return

        thread = threading.Thread(
            target=self._check_worker,
            args=(callback,),
            daemon=True,
            name="UpdateChecker"
        )
        thread.start()

    def _check_worker(self, callback: Optional[Callable]) -> None:
        """Worker thread để kiểm tra update."""
        try:
            import urllib.request
            import json

            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"VehicleManagementSystem/{self.current_version}",
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            latest_version = data.get("tag_name", "").lstrip("v")
            release_url = data.get("html_url", "")
            release_notes = data.get("body", "")[:500]  # Giới hạn 500 ký tự

            is_newer = self._is_newer_version(latest_version, self.current_version)

            result = {
                "version": latest_version,
                "url": release_url,
                "release_notes": release_notes,
                "is_newer": is_newer,
                "checked_at": datetime.now().isoformat(),
            }

            self._latest_info = result
            self._last_check = datetime.now()

            if is_newer:
                logger.info(f"Phiên bản mới: {latest_version} (hiện tại: {self.current_version})")
            else:
                logger.debug(f"Đang dùng phiên bản mới nhất: {self.current_version}")

            if callback:
                callback(result)

        except Exception as e:
            logger.debug(f"Không thể kiểm tra update (có thể offline): {e}")
            if callback:
                callback(None)

    @staticmethod
    def _is_newer_version(latest: str, current: str) -> bool:
        """
        So sánh 2 phiên bản SemVer.
        
        Returns:
            True nếu latest > current
        """
        try:
            def parse(v: str) -> tuple:
                parts = v.strip().split(".")
                return tuple(int(p) for p in parts[:3])

            return parse(latest) > parse(current)
        except (ValueError, AttributeError):
            return False


def check_for_updates(
    current_version: str,
    callback: Optional[Callable[[Optional[dict]], None]] = None
) -> UpdateChecker:
    """
    Shortcut function để kiểm tra update.
    
    Args:
        current_version: Phiên bản hiện tại
        callback: Callback nhận kết quả
    
    Returns:
        UpdateChecker instance
    """
    checker = UpdateChecker(current_version)
    checker.check_async(callback=callback)
    return checker
