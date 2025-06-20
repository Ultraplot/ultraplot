"""
Progress tracking module for matplotlib test execution.

This module provides real-time progress bars and visual feedback for matplotlib
image comparison tests, including success/failure counters and completion percentages.
"""

import threading


class ProgressTracker:
    """Manages progress tracking and visual feedback for matplotlib tests."""

    def __init__(self):
        self.total_tests = 0
        self.processed_tests = 0
        self.failed_tests = 0
        self.lock = threading.Lock()

    def set_total_tests(self, total):
        """Set the total number of matplotlib tests expected."""
        with self.lock:
            self.total_tests = total

    def increment_processed(self, failed=False):
        """Increment the processed test counter."""
        with self.lock:
            self.processed_tests += 1
            if failed:
                self.failed_tests += 1
            self._update_progress_bar()

    def _update_progress_bar(self):
        """Update the progress bar with current test status."""
        if self.total_tests == 0:
            return

        percentage = int((self.processed_tests / self.total_tests) * 100)
        success_count = self.processed_tests - self.failed_tests

        # Create progress bar: [=========>    ] 67% (45/67) | ✓32 ✗13
        bar_width = 20
        filled_width = int((percentage / 100) * bar_width)
        bar = (
            "=" * filled_width
            + (">" if filled_width < bar_width else "")
            + " " * (bar_width - filled_width - (1 if filled_width < bar_width else 0))
        )

        progress_line = f"\rMPL Tests: [{bar}] {percentage:3d}% ({self.processed_tests}/{self.total_tests}) | ✓{success_count} ✗{self.failed_tests}"
        print(progress_line, end="", flush=True)

    def finalize_progress(self):
        """Finalize the progress bar and show summary."""
        print()  # New line after progress bar
        success_count = self.processed_tests - self.failed_tests

        if self.failed_tests > 0:
            print(f"📊 MPL Summary: {success_count} passed, {self.failed_tests} failed")
        else:
            print(f"📊 MPL Summary: All {success_count} tests passed!")

    def get_stats(self):
        """Get current test statistics."""
        with self.lock:
            return {
                "total": self.total_tests,
                "processed": self.processed_tests,
                "failed": self.failed_tests,
                "passed": self.processed_tests - self.failed_tests,
            }


# Global progress tracker instance
progress_tracker = ProgressTracker()


def get_progress_tracker():
    """Get the global progress tracker instance."""
    return progress_tracker
