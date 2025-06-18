"""
Cleanup management module for matplotlib test artifacts.

This module provides deferred cleanup functionality to optimize artifact sizes
and eliminate race conditions in parallel test execution.
"""

import shutil
import threading
from pathlib import Path


class CleanupManager:
    """Manages deferred cleanup of successful test artifacts."""

    def __init__(self):
        self.pending_cleanups = set()
        self.lock = threading.Lock()

    def mark_for_cleanup(self, target_path):
        """Mark a directory for cleanup without blocking the worker."""
        with self.lock:
            if target_path.exists() and target_path.is_dir():
                self.pending_cleanups.add(target_path)
                return True
        return False

    def perform_cleanup(self, store_failed_only=False):
        """Perform deferred cleanup of all marked directories."""
        if not store_failed_only:
            self._handle_no_cleanup()
            return

        with self.lock:
            cleanup_list = list(self.pending_cleanups)
            self.pending_cleanups.clear()

        if cleanup_list:
            self._cleanup_directories(cleanup_list)
        else:
            print("💾 Perfect optimization: No cleanup needed (all tests failed)")

    def _handle_no_cleanup(self):
        """Handle case where cleanup optimization is disabled."""
        with self.lock:
            total_items = len(self.pending_cleanups)
            self.pending_cleanups.clear()

        if total_items > 0:
            print(f"💾 All {total_items} test images preserved for review")
            print("   💡 Use --store-failed-only to enable artifact size optimization")

    def _cleanup_directories(self, cleanup_list):
        """Clean up the list of directories with progress tracking."""
        print(
            f"🧹 Cleaning up {len(cleanup_list)} successful test directories (--store-failed-only enabled)..."
        )
        success_count = 0

        for i, target in enumerate(cleanup_list, 1):
            # Update cleanup progress bar
            percentage = int((i / len(cleanup_list)) * 100)
            bar_width = 20
            filled_width = int((percentage / 100) * bar_width)
            bar = (
                "=" * filled_width
                + (">" if filled_width < bar_width else "")
                + " "
                * (bar_width - filled_width - (1 if filled_width < bar_width else 0))
            )

            try:
                if target.exists() and target.is_dir():
                    shutil.rmtree(target)
                    success_count += 1
                    status = "✓"
                else:
                    status = "~"
            except (FileNotFoundError, OSError, PermissionError):
                status = "~"
            except Exception as e:
                status = "✗"

            cleanup_line = f"\rCleanup: [{bar}] {percentage:3d}% ({i}/{len(cleanup_list)}) {status}"
            print(cleanup_line, end="", flush=True)

        print()  # New line after progress bar
        print(
            f"✅ Cleanup completed: {success_count}/{len(cleanup_list)} directories removed"
        )
        if success_count < len(cleanup_list):
            print(
                f"   Note: {len(cleanup_list) - success_count} directories were already removed or inaccessible"
            )
        print("💾 Artifact optimization: Only failed tests preserved for debugging")

    def get_pending_count(self):
        """Get the number of directories pending cleanup."""
        with self.lock:
            return len(self.pending_cleanups)


# Global cleanup manager instance
cleanup_manager = CleanupManager()


def get_cleanup_manager():
    """Get the global cleanup manager instance."""
    return cleanup_manager
