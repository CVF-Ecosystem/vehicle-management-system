"""
Tests for HQ Automation (Phase 3.3)
"""

import pytest
import os
import tempfile
import zipfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import shutil

from reporting.hq_automation import FolderMonitor


@pytest.fixture
def temp_folders():
    """Create temporary folders for testing."""
    tmpdir = tempfile.mkdtemp()
    monitor_folder = os.path.join(tmpdir, "monitor")
    import_folder = os.path.join(tmpdir, "imports")
    log_folder = os.path.join(tmpdir, "logs")

    Path(monitor_folder).mkdir(parents=True, exist_ok=True)
    Path(import_folder).mkdir(parents=True, exist_ok=True)
    Path(log_folder).mkdir(parents=True, exist_ok=True)

    yield monitor_folder, import_folder, log_folder

    # Cleanup
    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass


def _create_test_bundle(folder: str, file_name: str = "test_bundle.zip") -> str:
    """Create a test bundle file."""
    file_path = os.path.join(folder, file_name)
    with zipfile.ZipFile(file_path, "w") as z:
        z.writestr("test.txt", "test data")
    return file_path


class TestFolderMonitorBasics:
    """Test basic folder monitor functionality."""

    def test_initialization(self, temp_folders):
        """Test FolderMonitor initialization."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        assert os.path.exists(monitor.monitor_folder)
        assert os.path.exists(monitor.import_folder)
        assert os.path.exists(monitor.log_folder)
        assert os.path.exists(monitor.error_folder)

    def test_scan_empty_folder(self, temp_folders):
        """Test scanning empty folder."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        new_files = monitor.scan_folder()
        assert new_files == []

    def test_scan_detects_new_bundle(self, temp_folders):
        """Test scanning detects new bundle file."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create test bundle
        _create_test_bundle(monitor_folder)

        new_files = monitor.scan_folder()
        assert len(new_files) == 1
        assert new_files[0][2] == "test_bundle.zip"

    def test_scan_ignores_non_zip_files(self, temp_folders):
        """Test that non-zip files are ignored."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create non-zip file
        test_file = os.path.join(monitor_folder, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        new_files = monitor.scan_folder()
        assert new_files == []

    def test_scan_ignores_system_folders(self, temp_folders):
        """Test that system folders (_errors, etc) are ignored."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create file in error folder
        _create_test_bundle(monitor.error_folder, "_error_bundle.zip")

        new_files = monitor.scan_folder()
        assert new_files == []


class TestFileHashTracking:
    """Test file hash tracking for deduplication."""

    def test_hash_calculation(self, temp_folders):
        """Test MD5 hash calculation."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        file_path = _create_test_bundle(monitor_folder)
        file_hash = monitor._get_file_hash(file_path)

        # Hash should be consistent
        file_hash2 = monitor._get_file_hash(file_path)
        assert file_hash == file_hash2
        assert len(file_hash) == 32  # MD5 is 32 hex chars

    def test_save_and_load_processed_hashes(self, temp_folders):
        """Test saving and loading processed file hashes."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Save some hashes
        monitor._save_processed_hash("hash1", "file1.zip")
        monitor._save_processed_hash("hash2", "file2.zip")

        # Load them back
        loaded_hashes = monitor._load_processed_hashes()
        assert "hash1" in loaded_hashes
        assert "hash2" in loaded_hashes

    def test_duplicate_detection(self, temp_folders):
        """Test that duplicate files are detected."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create and process a bundle
        file_path = _create_test_bundle(monitor_folder, "bundle1.zip")
        file_hash = monitor._get_file_hash(file_path)
        monitor._save_processed_hash(file_hash, "bundle1.zip")

        # Create identical bundle (same content)
        file_path2 = _create_test_bundle(monitor_folder, "bundle2.zip")
        file_hash2 = monitor._get_file_hash(file_path2)

        # Hashes should match
        assert file_hash == file_hash2

        # Should detect as duplicate
        new_files = monitor.scan_folder()
        assert len(new_files) == 0  # Both are identical, one already processed

    def test_different_files_not_duplicate(self, temp_folders):
        """Test that files with different content are not duplicates."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create first bundle
        file_path1 = os.path.join(monitor_folder, "bundle1.zip")
        with zipfile.ZipFile(file_path1, "w") as z:
            z.writestr("data.txt", "content1")

        hash1 = monitor._get_file_hash(file_path1)
        monitor._save_processed_hash(hash1, "bundle1.zip")

        # Create second bundle with different content
        file_path2 = os.path.join(monitor_folder, "bundle2.zip")
        with zipfile.ZipFile(file_path2, "w") as z:
            z.writestr("data.txt", "content2")

        # Should detect bundle2 as new
        new_files = monitor.scan_folder()
        assert len(new_files) == 1
        assert new_files[0][2] == "bundle2.zip"


class TestProcessBundle:
    """Test bundle processing logic."""

    def test_process_bundle_success(self, temp_folders):
        """Test successful bundle processing."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Mock import callback
        import_callback = Mock(return_value={"success": True, "summary": "Imported 10 events"})
        monitor.import_callback = import_callback

        file_path = _create_test_bundle(monitor_folder)
        file_hash = monitor._get_file_hash(file_path)

        result = monitor.process_bundle(file_path, file_hash, "test_bundle.zip")

        assert result is True
        # File should be moved to import folder
        assert os.path.exists(os.path.join(import_folder, "test_bundle.zip"))
        assert not os.path.exists(file_path)
        # Hash should be tracked as processed
        assert file_hash in monitor._load_processed_hashes()

    def test_process_bundle_failure_moves_to_error(self, temp_folders):
        """Test that failed bundle is moved to error folder."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Mock import callback with failure
        import_callback = Mock(
            return_value={"success": False, "error": "Invalid format"}
        )
        monitor.import_callback = import_callback

        file_path = _create_test_bundle(monitor_folder)
        file_hash = monitor._get_file_hash(file_path)

        result = monitor.process_bundle(file_path, file_hash, "test_bundle.zip")

        assert result is False
        # File should be moved to error folder
        assert os.path.exists(os.path.join(monitor.error_folder, "test_bundle.zip"))
        assert not os.path.exists(file_path)

    def test_process_bundle_logs_result(self, temp_folders):
        """Test that import results are logged."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Mock successful import
        import_callback = Mock(return_value={"success": True, "summary": "Imported 5 events"})
        monitor.import_callback = import_callback

        file_path = _create_test_bundle(monitor_folder)
        file_hash = monitor._get_file_hash(file_path)

        monitor.process_bundle(file_path, file_hash, "test_bundle.zip")

        # Check that log file was created
        log_file = os.path.join(log_folder, "automation.log")
        assert os.path.exists(log_file)

        with open(log_file, "r") as f:
            content = f.read()
            assert "test_bundle.zip" in content
            assert "SUCCESS" in content


class TestBatchImport:
    """Test batch import functionality."""

    def test_batch_import_multiple_files(self, temp_folders):
        """Test batch importing multiple files."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create test bundles
        _create_test_bundle(monitor_folder, "bundle1.zip")
        _create_test_bundle(monitor_folder, "bundle2.zip")
        _create_test_bundle(monitor_folder, "bundle3.zip")

        # Mock import callback
        import_callback = Mock(return_value={"success": True})
        monitor.import_callback = import_callback

        summary = monitor.run_batch_import()

        assert summary["total_files"] == 3
        assert summary["successful"] == 3
        assert summary["failed"] == 0
        assert len(os.listdir(import_folder)) == 3

    def test_batch_import_mixed_results(self, temp_folders):
        """Test batch import with some successes and failures."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create test bundles
        _create_test_bundle(monitor_folder, "bundle1.zip")
        _create_test_bundle(monitor_folder, "bundle2.zip")

        # Mock import callback - fail on second call
        results = [
            {"success": True},
            {"success": False, "error": "Checksum failed"},
        ]
        import_callback = Mock(side_effect=results)
        monitor.import_callback = import_callback

        summary = monitor.run_batch_import()

        assert summary["total_files"] == 2
        assert summary["successful"] == 1
        assert summary["failed"] == 1
        # One in imports, one in errors
        assert len(os.listdir(import_folder)) == 1
        assert len(os.listdir(monitor.error_folder)) == 1


class TestIntegration:
    """Integration tests for full workflow."""

    def test_full_workflow_new_file(self, temp_folders):
        """Test complete workflow: detect new file and import it."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Mock import callback
        import_callback = Mock(
            return_value={"success": True, "summary": "Imported 42 events"}
        )
        monitor.import_callback = import_callback

        # Create bundle
        _create_test_bundle(monitor_folder)

        # Scan should detect it
        new_files = monitor.scan_folder()
        assert len(new_files) == 1

        # Process it
        file_path, file_hash, file_name = new_files[0]
        monitor.process_bundle(file_path, file_hash, file_name)

        # Should be moved and tracked
        assert os.path.exists(os.path.join(import_folder, file_name))
        assert file_hash in monitor._load_processed_hashes()

        # Next scan should not find it
        new_files = monitor.scan_folder()
        assert len(new_files) == 0

    def test_skip_in_progress_files(self, temp_folders):
        """Test that files being written are skipped."""
        monitor_folder, import_folder, log_folder = temp_folders
        monitor = FolderMonitor(monitor_folder, import_folder, log_folder)

        # Create a file with .tmp extension (being written)
        tmp_file = os.path.join(monitor_folder, "bundle.zip.tmp")
        with open(tmp_file, "w") as f:
            f.write("incomplete")

        # Should be skipped
        new_files = monitor.scan_folder()
        assert len(new_files) == 0
