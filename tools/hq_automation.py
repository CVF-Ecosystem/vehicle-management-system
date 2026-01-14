#!/usr/bin/env python3
"""
HQ Automation CLI Tool

Usage:
    python -m tools.hq_automation --monitor      # Start folder monitoring
    python -m tools.hq_automation --batch        # Run one-time batch import
    python -m tools.hq_automation --setup-task   # Setup Task Scheduler job
"""

import argparse
import logging
import sys
import os
from pathlib import Path

import config
from reporting.hq_automation import FolderMonitor
from tools.import_bundles import run_import_bundles


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_folders():
    """Ensure automation folders exist."""
    monitor_folder = getattr(config, "AUTOMATION_MONITOR_FOLDER", "data/monitor")
    import_folder = getattr(config, "AUTOMATION_IMPORT_FOLDER", "data/imports")
    log_folder = getattr(config, "AUTOMATION_LOG_FOLDER", "logs/automation")

    Path(monitor_folder).mkdir(parents=True, exist_ok=True)
    Path(import_folder).mkdir(parents=True, exist_ok=True)
    Path(log_folder).mkdir(parents=True, exist_ok=True)

    return monitor_folder, import_folder, log_folder


def create_import_callback():
    """Create callback function for importing bundles."""

    def callback(file_path: str):
        """Import a bundle file."""
        try:
            result = run_import_bundles(file_path, auto_import=True)
            return {
                "success": result.get("success", False),
                "summary": result.get("summary", ""),
                "error": result.get("error", ""),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    return callback


def run_monitor(interval: int = 60):
    """Start folder monitoring."""
    logger.info("HQ Automation: Starting folder monitor")

    monitor_folder, import_folder, log_folder = setup_folders()

    logger.info(f"  Monitor folder: {monitor_folder}")
    logger.info(f"  Import folder: {import_folder}")
    logger.info(f"  Log folder: {log_folder}")
    logger.info(f"  Scan interval: {interval} seconds")
    logger.info("  Press Ctrl+C to stop\n")

    monitor = FolderMonitor(
        monitor_folder=monitor_folder,
        import_folder=import_folder,
        log_folder=log_folder,
        import_callback=create_import_callback(),
    )

    try:
        monitor.start(interval_seconds=interval)
    except KeyboardInterrupt:
        logger.info("Folder monitor stopped")
        sys.exit(0)


def run_batch_import():
    """Run one-time batch import."""
    logger.info("HQ Automation: Running batch import")

    monitor_folder, import_folder, log_folder = setup_folders()

    monitor = FolderMonitor(
        monitor_folder=monitor_folder,
        import_folder=import_folder,
        log_folder=log_folder,
        import_callback=create_import_callback(),
    )

    summary = monitor.run_batch_import()

    logger.info(f"Batch import complete:")
    logger.info(f"  Total files: {summary['total_files']}")
    logger.info(f"  Successful: {summary['successful']}")
    logger.info(f"  Failed: {summary['failed']}")


def setup_task_scheduler():
    """Setup Windows Task Scheduler job (Windows only)."""
    import platform
    import subprocess

    if platform.system() != "Windows":
        logger.error("Task Scheduler setup is only available on Windows")
        sys.exit(1)

    logger.info("HQ Automation: Setting up Task Scheduler job")

    # Get script path
    script_path = os.path.abspath(__file__)
    python_path = sys.executable

    # Task details
    task_name = "HQ_AutoImport"
    task_time = getattr(config, "AUTOMATION_TASK_TIME", "02:00")  # 2 AM
    task_description = "Auto-import bundles for HQ vehicle management"

    # Create task command
    cmd = [
        "schtasks",
        "/create",
        "/tn",
        task_name,
        "/tr",
        f'"{python_path}" -m tools.hq_automation --batch',
        "/sc",
        "daily",
        "/st",
        task_time,
        "/f",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            logger.info(f"✓ Task created: {task_name}")
            logger.info(f"  Schedule: Daily at {task_time}")
            logger.info(f"  Action: Auto-import from monitor folder")
            logger.info(f"\nTo view the task:")
            logger.info(f"  schtasks /query /tn {task_name}")
            logger.info(f"\nTo delete the task:")
            logger.info(f"  schtasks /delete /tn {task_name} /f")
        else:
            logger.error(f"Failed to create task: {result.stderr}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error setting up task: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="HQ Automation - Folder monitoring and batch import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m tools.hq_automation --monitor          # Start folder monitoring (60s interval)
  python -m tools.hq_automation --monitor --interval 30   # Custom interval
  python -m tools.hq_automation --batch            # Run one-time batch import
  python -m tools.hq_automation --setup-task       # Setup Windows Task Scheduler
        """,
    )

    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Start folder monitoring",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Scan interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run one-time batch import",
    )
    parser.add_argument(
        "--setup-task",
        action="store_true",
        help="Setup Windows Task Scheduler job",
    )

    args = parser.parse_args()

    # If no arguments, show help
    if not any([args.monitor, args.batch, args.setup_task]):
        parser.print_help()
        sys.exit(1)

    try:
        if args.monitor:
            run_monitor(args.interval)
        elif args.batch:
            run_batch_import()
        elif args.setup_task:
            setup_task_scheduler()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
