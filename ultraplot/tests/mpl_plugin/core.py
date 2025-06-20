"""
Core plugin module for enhanced matplotlib testing.

This module contains the main StoreFailedMplPlugin class that coordinates
all matplotlib test functionality including progress tracking, cleanup management,
and HTML report generation.
"""

import re
import pytest
from pathlib import Path

from .progress import get_progress_tracker
from .cleanup import get_cleanup_manager
from .utils import create_nodeid_to_path_mapping, validate_config_paths


class StoreFailedMplPlugin:
    """
    Main plugin class for enhanced matplotlib image comparison testing.

    This plugin provides:
    - Real-time progress tracking with visual progress bars
    - Deferred cleanup to eliminate race conditions
    - Thread-safe artifact optimization
    - Failed test tracking for HTML report generation
    """

    def __init__(self, config):
        self.config = config

        # Validate and set up paths
        paths = validate_config_paths(config)
        self.result_dir = paths["results"]
        self.baseline_dir = paths["baseline"]

        # Track failed mpl tests for HTML report generation
        self.failed_mpl_tests = set()

        # Get global managers
        self.progress_tracker = get_progress_tracker()
        self.cleanup_manager = get_cleanup_manager()

        # Only show initialization message if MPL tests will be run
        if any("--mpl" in str(arg) for arg in getattr(config, "args", [])):
            print(f"Store Failed MPL Plugin initialized")
            print(f"Result dir: {self.result_dir}")

    def _has_mpl_marker(self, report: pytest.TestReport):
        """Check if the test has the mpl_image_compare marker."""
        return report.keywords.get("mpl_image_compare", False)

    def _remove_success(self, report: pytest.TestReport):
        """Mark successful test images for deferred cleanup to eliminate blocking."""

        # Only perform cleanup if --store-failed-only is enabled
        if not self.config.getoption("--store-failed-only", False):
            return

        # Convert nodeid to filesystem path
        name = create_nodeid_to_path_mapping(report.nodeid)
        target = (self.result_dir / name).absolute()

        # Mark for deferred cleanup (non-blocking)
        if self.cleanup_manager.mark_for_cleanup(target):
            print(".", end="", flush=True)

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        """Hook that processes each test report."""
        # Track failed mpl tests and handle successful ones
        if report.when == "call" and self._has_mpl_marker(report):
            try:
                # Update progress tracking
                if report.outcome == "failed":
                    self.failed_mpl_tests.add(report.nodeid)
                    self.progress_tracker.increment_processed(failed=True)
                else:
                    self.progress_tracker.increment_processed(failed=False)
                    # Mark successful tests for cleanup (if enabled)
                    self._remove_success(report)

            except Exception as e:
                # Log but don't fail on processing errors
                print(f"Warning: Error during test processing for {report.nodeid}: {e}")

    def get_failed_tests(self):
        """Get the set of failed test nodeids."""
        return self.failed_mpl_tests.copy()

    def get_stats(self):
        """Get current test statistics."""
        return self.progress_tracker.get_stats()

    def finalize(self):
        """Finalize progress tracking and perform cleanup."""
        self.progress_tracker.finalize_progress()
        store_failed_only = self.config.getoption("--store-failed-only", False)
        self.cleanup_manager.perform_cleanup(store_failed_only)
