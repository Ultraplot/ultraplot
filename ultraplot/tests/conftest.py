"""
Conftest.py for UltraPlot testing with modular MPL plugin architecture.

This file provides essential test fixtures and integrates the enhanced matplotlib
testing functionality through a clean, modular plugin system.

Thread-Safe Random Number Generation:
- Provides explicit RNG fixtures for test functions that need random numbers
- Each thread gets independent, deterministic RNG instances
- Compatible with pytest-xdist parallel execution
- Clean separation of concerns - tests explicitly declare RNG dependencies

Matplotlib rcParams Safety:
- Automatic rcParams isolation for all tests prevents interference
- Tests that modify matplotlib settings are automatically isolated
- Dedicated rcparams_isolation fixture for explicit isolation needs
- Thread-safe for parallel execution with pytest-xdist
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
def reset_rc_and_close_figures():
    """Reset rc to full ultraplot defaults and close figures for each test."""
    # Force complete ultraplot initialization for this thread
    _ensure_ultraplot_defaults()

    yield

    # Clean up after test
    uplt.close("all")

    # Reset to clean state for next test
    _ensure_ultraplot_defaults()


def _ensure_ultraplot_defaults():
    """Ensure current thread has complete ultraplot configuration."""
    from ultraplot.internals import rcsetup
    from ultraplot.config import _get_style_dict

    # Clear thread-local storage to force reinitialization
    if hasattr(uplt.rc, "_local_props"):
        if hasattr(uplt.rc._local_props, "rc_ultraplot"):
            delattr(uplt.rc._local_props, "rc_ultraplot")
        if hasattr(uplt.rc._local_props, "rc_matplotlib"):
            delattr(uplt.rc._local_props, "rc_matplotlib")

    # Force thread-local dicts to exist
    _ = uplt.rc._rc_ultraplot
    _ = uplt.rc._rc_matplotlib

    # Apply complete ultraplot initialization sequence
    uplt.rc._rc_matplotlib.update(_get_style_dict("original", filter=False))
    uplt.rc._rc_matplotlib.update(rcsetup._rc_matplotlib_default)
    uplt.rc._rc_ultraplot.update(rcsetup._rc_ultraplot_default)

    # Apply ultraplot->matplotlib translations in correct order
    ultraplot_items = list(uplt.rc._rc_ultraplot.items())
    grid_items = [(k, v) for k, v in ultraplot_items if k in ("grid", "gridminor")]
    other_items = [(k, v) for k, v in ultraplot_items if k not in ("grid", "gridminor")]

    # Process gridminor before grid to avoid conflicts
    grid_items.sort(key=lambda x: 0 if x[0] == "gridminor" else 1)

    # Apply all ultraplot settings to matplotlib
    for key, value in other_items + grid_items:
        try:
            kw_ultraplot, kw_matplotlib = uplt.rc._get_item_dicts(
                key, value, skip_cycle=True
            )
            uplt.rc._rc_matplotlib.update(kw_matplotlib)
            uplt.rc._rc_ultraplot.update(kw_ultraplot)
        except:
            # Skip any problematic settings during test setup
            continue


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
    - Configures process-specific temporary directories for parallel testing
    """
    # Suppress ultraplot config loading which mpl does not recognize
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("ultraplot").setLevel(logging.WARNING)

    # Configure process-specific results directory for parallel testing
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    if (
        not hasattr(config.option, "mpl_results_path")
        or not config.option.mpl_results_path
    ):
        config.option.mpl_results_path = f"./mpl-results-{worker_id}"

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
