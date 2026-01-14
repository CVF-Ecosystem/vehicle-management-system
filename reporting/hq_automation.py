"""
HQ Automation: Folder Monitor & Auto-Import (Phase 3.3)

Provides automated folder monitoring and scheduled batch imports for HQ operations.
"""

import os
import hashlib
import sqlite3
import logging
from pathlib import Path
from typing import Set, Optional, Dict
from datetime import datetime
import time
import json

import config


logger = logging.getLogger(__name__)


class FolderMonitor:
    """Monitor folder for new bundle files and auto-import them."""

    def __init__(
        self,
        monitor_folder: str,
        import_folder: str,
        log_folder: str,
        import_callback=None,
    ):
        """
        Initialize folder monitor.

        Args:
            monitor_folder: Folder to watch for new bundles
            import_folder: Folder where bundles will be moved after processing
            log_folder: Folder for monitor logs
            import_callback: Function to call for importing bundles
        """
        self.monitor_folder = monitor_folder
        self.import_folder = import_folder
        self.log_folder = log_folder
        self.import_callback = import_callback
        self.processed_files: Set[str] = set()
        self.error_folder = os.path.join(monitor_folder, "_errors")

        # Create folders if they don't exist
        Path(monitor_folder).mkdir(parents=True, exist_ok=True)
        Path(import_folder).mkdir(parents=True, exist_ok=True)
        Path(log_folder).mkdir(parents=True, exist_ok=True)
        Path(self.error_folder).mkdir(parents=True, exist_ok=True)

    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _load_processed_hashes(self) -> Set[str]:
        """Load set of processed file hashes from tracking file."""
        tracking_file = os.path.join(self.log_folder, ".processed_hashes.json")
        if os.path.exists(tracking_file):
            try:
                with open(tracking_file, "r") as f:
                    data = json.load(f)
                    return set(data.get("hashes", []))
            except Exception as e:
                logger.warning(f"Could not load processed hashes: {e}")
        return set()

    def _save_processed_hash(self, file_hash: str, file_name: str):
        """Save processed file hash to tracking file."""
        tracking_file = os.path.join(self.log_folder, ".processed_hashes.json")
        try:
            hashes = self._load_processed_hashes()
            hashes.add(file_hash)
            with open(tracking_file, "w") as f:
                json.dump({"hashes": list(hashes), "updated_at": datetime.now().isoformat()}, f)
        except Exception as e:
            logger.error(f"Could not save processed hash: {e}")

    def scan_folder(self) -> list:
        """Scan monitor folder for new bundle files."""
        if not os.path.exists(self.monitor_folder):
            return []

        processed_hashes = self._load_processed_hashes()
        new_files = []

        try:
            for file_name in os.listdir(self.monitor_folder):
                if file_name.startswith("_"):  # Skip system folders
                    continue

                file_path = os.path.join(self.monitor_folder, file_name)

                # Skip folders and non-zip files
                if not os.path.isfile(file_path) or not file_name.endswith(".zip"):
                    continue

                # Skip lock files (still being written)
                if file_name.endswith(".tmp"):
                    continue

                try:
                    # Check if file is locked (still being written)
                    if self._is_file_locked(file_path):
                        logger.debug(f"File still being written: {file_name}")
                        continue

                    file_hash = self._get_file_hash(file_path)

                    # Skip if already processed
                    if file_hash in processed_hashes:
                        logger.debug(f"File already processed: {file_name}")
                        continue

                    new_files.append((file_path, file_hash, file_name))

                except Exception as e:
                    logger.error(f"Error checking file {file_name}: {e}")

        except Exception as e:
            logger.error(f"Error scanning folder {self.monitor_folder}: {e}")

        return new_files

    def _is_file_locked(self, file_path: str) -> bool:
        """Check if file is still being written (locked)."""
        try:
            # Try to open file for exclusive access
            import msvcrt
            handle = open(file_path, "rb")
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                handle.close()
                return False
            except OSError:
                handle.close()
                return True
        except Exception:
            # On non-Windows or if locking check fails, assume not locked
            return False

    def process_bundle(self, file_path: str, file_hash: str, file_name: str) -> bool:
        """
        Process a bundle file (import and move).

        Args:
            file_path: Full path to bundle file
            file_hash: MD5 hash of file
            file_name: Name of file

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing bundle: {file_name}")

        try:
            if not self.import_callback:
                logger.warning("No import callback configured")
                return False

            # Call import callback
            result = self.import_callback(file_path)

            if result.get("success", False):
                # Move file to import folder
                dest_path = os.path.join(self.import_folder, file_name)
                try:
                    os.rename(file_path, dest_path)
                    logger.info(f"Moved to import folder: {file_name}")
                except Exception as e:
                    logger.warning(f"Could not move file to import folder: {e}")

                # Track as processed
                self._save_processed_hash(file_hash, file_name)

                # Log import result
                self._log_import_result(
                    file_name,
                    "SUCCESS",
                    result.get("summary", "Import completed"),
                )

                return True
            else:
                # Move to error folder
                error_path = os.path.join(self.error_folder, file_name)
                try:
                    os.rename(file_path, error_path)
                    logger.warning(f"Moved to error folder: {file_name}")
                except Exception:
                    pass

                self._log_import_result(
                    file_name, "ERROR", result.get("error", "Import failed")
                )

                return False

        except Exception as e:
            logger.error(f"Error processing bundle {file_name}: {e}")
            self._log_import_result(file_name, "ERROR", str(e))
            return False

    def _log_import_result(self, file_name: str, status: str, message: str):
        """Log import result to file."""
        log_file = os.path.join(self.log_folder, "automation.log")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] [{status:7}] {file_name}: {message}\n")
        except Exception as e:
            logger.error(f"Could not write to log file: {e}")

    def start(self, interval_seconds: int = 60, max_iterations: int = None):
        """
        Start monitoring folder (blocking).

        Args:
            interval_seconds: Seconds between scans (default 60)
            max_iterations: Max scans before stopping (for testing)
        """
        logger.info(f"Starting folder monitor - watching {self.monitor_folder}")
        iteration = 0

        try:
            while True:
                iteration += 1

                # Scan for new files
                new_files = self.scan_folder()

                if new_files:
                    logger.info(f"Found {len(new_files)} new bundle(s)")
                    for file_path, file_hash, file_name in new_files:
                        self.process_bundle(file_path, file_hash, file_name)

                # For testing: stop after max iterations
                if max_iterations and iteration >= max_iterations:
                    logger.info(f"Stopping after {iteration} iterations (testing)")
                    break

                # Wait before next scan
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Folder monitor stopped by user")
        except Exception as e:
            logger.error(f"Folder monitor error: {e}", exc_info=True)

    def run_batch_import(self) -> Dict:
        """
        Run one-time batch import of all unprocessed files.

        Returns:
            Summary dict with counts
        """
        logger.info("Starting batch import")
        processed_hashes = self._load_processed_hashes()

        summary = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
        }

        new_files = self.scan_folder()

        for file_path, file_hash, file_name in new_files:
            summary["total_files"] += 1
            if self.process_bundle(file_path, file_hash, file_name):
                summary["successful"] += 1
            else:
                summary["failed"] += 1

        logger.info(
            f"Batch import complete: {summary['successful']} success, {summary['failed']} failed"
        )

        return summary
