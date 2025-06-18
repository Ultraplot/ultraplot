"""
Conftest.py for UltraPlot testing with modular MPL plugin architecture.

This file provides essential test fixtures and integrates the enhanced matplotlib
testing functionality through a clean, modular plugin system.

Thread-Safe Random Number Generation:
- Provides explicit RNG fixtures for test functions that need random numbers
- Each thread gets independent, deterministic RNG instances
- Compatible with pytest-xdist parallel execution
- Clean separation of concerns - tests explicitly declare RNG dependencies
"""

import threading, os, shutil, pytest, re
import numpy as np, ultraplot as uplt
import warnings, logging
from pathlib import Path
from datetime import datetime

# Import the modular MPL plugin components
from ultraplot.tests.mpl_plugin import (
    StoreFailedMplPlugin,
    ProgressTracker,
    CleanupManager,
    HTMLReportGenerator,
)
from ultraplot.tests.mpl_plugin.utils import (
    count_mpl_tests,
    should_generate_html_report,
    get_failed_mpl_tests,
)
from ultraplot.tests.mpl_plugin.progress import get_progress_tracker
from ultraplot.tests.mpl_plugin.cleanup import get_cleanup_manager

SEED = 51423


@pytest.fixture
def rng():
    """
    Fixture providing a numpy random generator for tests.

    This fixture provides a numpy.random.Generator instance that:
    - Uses the same seed (51423) for each test
    - Ensures reproducible results
    - Resets state for each test

    Usage in tests:
        def test_something(rng):
            random_data = rng.normal(0, 1, size=100)
            random_ints = rng.integers(0, 10, size=5)
    """
    # Each test gets the same seed for reproducibility
    return np.random.default_rng(seed=SEED)


@pytest.fixture(autouse=True)
def close_figures_after_test():
    """Automatically close all figures after each test."""
    yield
    uplt.close("all")


def pytest_addoption(parser):
    """Add command line options for enhanced matplotlib testing."""
    parser.addoption(
        "--store-failed-only",
        action="store_true",
        help="Store only failed matplotlib comparison images (enables artifact optimization)",
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection to set up MPL testing.

    This function:
    - Counts matplotlib image comparison tests
    - Sets up progress tracking
    - Skips tests with missing baseline images
    """
    # Count total mpl tests for progress tracking
    total_mpl_tests = count_mpl_tests(items)

    if total_mpl_tests > 0:
        print(f"📊 Detected {total_mpl_tests} matplotlib image comparison tests")
        # Initialize progress tracker with total count
        progress_tracker = get_progress_tracker()
        progress_tracker.set_total_tests(total_mpl_tests)

    # Skip tests that don't have baseline images
    for item in items:
        for mark in item.own_markers:
            if base_dir := config.getoption("--mpl-baseline-path", default=None):
                if mark.name == "mpl_image_compare":
                    name = item.name
                    if not (Path(base_dir) / f"{name}.png").exists():
                        item.add_marker(
                            pytest.mark.skip(reason="Baseline image does not exist")
                        )


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Generate enhanced summary and HTML reports after all tests complete.

    This function:
    - Finalizes progress tracking
    - Performs deferred cleanup
    - Generates interactive HTML reports
    - Only runs on the main process (not xdist workers)
    """
    # Skip on workers, only run on the main process
    if hasattr(config, "workerinput"):
        return

    # Check if we should generate reports
    if not should_generate_html_report(config):
        return

    # Get the plugin instance to finalize operations
    plugin = _get_plugin_instance(config)
    if plugin:
        # Finalize progress and cleanup
        plugin.finalize()

        # Generate HTML report
        html_generator = HTMLReportGenerator(config)
        failed_tests = plugin.get_failed_tests()
        html_generator.generate_report(failed_tests)


def pytest_configure(config):
    """
    Configure pytest with the enhanced MPL plugin.

    This function:
    - Suppresses verbose matplotlib logging
    - Registers the StoreFailedMplPlugin for enhanced functionality
    - Sets up the plugin regardless of cleanup options (HTML reports always available)
    """
    # Suppress ultraplot config loading which mpl does not recognize
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("ultraplot").setLevel(logging.WARNING)

    try:
        # Always register the plugin - it provides enhanced functionality beyond just cleanup
        config.pluginmanager.register(StoreFailedMplPlugin(config))
    except Exception as e:
        print(f"Error during MPL plugin configuration: {e}")


def _get_plugin_instance(config):
    """Get the StoreFailedMplPlugin instance from the plugin manager."""
    for plugin in config.pluginmanager.get_plugins():
        if isinstance(plugin, StoreFailedMplPlugin):
            return plugin
    return None


# Legacy support - these functions are kept for backward compatibility
# but now delegate to the modular plugin system


def _should_generate_html_report(config):
    """Legacy function - delegates to utils module."""
    return should_generate_html_report(config)


def _get_failed_mpl_tests(config):
    """Legacy function - delegates to utils module."""
    return get_failed_mpl_tests(config)


def _get_results_directory(config):
    """Legacy function - delegates to utils module."""
    from ultraplot.tests.mpl_plugin.utils import get_results_directory

    return get_results_directory(config)
