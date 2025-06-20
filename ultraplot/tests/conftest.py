import os, shutil, pytest, re, numpy as np, ultraplot as uplt
from pathlib import Path
import warnings, logging

SEED = 51423


@pytest.fixture
def rng():
    """
    Ensure all tests start with the same rng
    """
    return np.random.default_rng(SEED)


@pytest.fixture(autouse=True)
def isolate_mpl_testing():
    """
    Isolate matplotlib testing for parallel execution.

    This prevents race conditions in parallel testing (pytest-xdist) where
    multiple processes can interfere with each other's image comparison tests.
    The main issue is that pytest-mpl uses shared temporary directories that
    can conflict between processes.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import tempfile
    import os

    # Store original backend and ensure consistent state
    original_backend = mpl.get_backend()
    if original_backend != "Agg":
        mpl.use("Agg", force=True)

    # Clear any existing figures
    plt.close("all")

    # Create process-specific temporary directory for mpl results
    # This prevents file conflicts between parallel processes
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    with tempfile.TemporaryDirectory(prefix=f"mpl_test_{worker_id}_") as temp_dir:
        os.environ["MPL_TEST_TEMP_DIR"] = temp_dir

        yield

    # Clean up after test
    plt.close("all")
    uplt.close("all")

    # Remove environment variable
    if "MPL_TEST_TEMP_DIR" in os.environ:
        del os.environ["MPL_TEST_TEMP_DIR"]

    # Restore original backend
    if original_backend != "Agg":
        mpl.use(original_backend, force=True)


@pytest.fixture(autouse=True)
def close_figures_after_test():
    yield
    uplt.close("all")


# Define command line option
def pytest_addoption(parser):
    parser.addoption(
        "--store-failed-only",
        action="store_true",
        help="Store only failed matplotlib comparison images",
    )


class StoreFailedMplPlugin:
    def __init__(self, config):
        self.config = config

        # Get base directories as Path objects
        self.result_dir = Path(config.getoption("--mpl-results-path", "./results"))
        self.baseline_dir = Path(config.getoption("--mpl-baseline-path", "./baseline"))

        print(f"Store Failed MPL Plugin initialized")
        print(f"Result dir: {self.result_dir}")

    def _has_mpl_marker(self, report: pytest.TestReport):
        """Check if the test has the mpl_image_compare marker."""
        return report.keywords.get("mpl_image_compare", False)

    def _remove_success(self, report: pytest.TestReport):
        """Remove successful test images."""

        pattern = r"(?P<sep>::|/)|\[|\]|\.py"
        name = re.sub(
            pattern,
            lambda m: "." if m.group("sep") else "_" if m.group(0) == "[" else "",
            report.nodeid,
        )
        target = (self.result_dir / name).absolute()
        if target.is_dir():
            shutil.rmtree(target)

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        """Hook that processes each test report."""
        # Delete successfull tests
        if report.when == "call" and report.failed == False:
            if self._has_mpl_marker(report):
                self._remove_success(report)


def pytest_collection_modifyitems(config, items):
    for item in items:
        for mark in item.own_markers:
            if base_dir := config.getoption("--mpl-baseline-path", default=None):
                if mark.name == "mpl_image_compare":
                    name = item.name
                    if not (Path(base_dir) / f"{name}.png").exists():
                        item.add_marker(
                            pytest.mark.skip(reason="Baseline image does not exist")
                        )


# Register the plugin if the option is used
def pytest_configure(config):
<<<<<<< HEAD
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

=======
    # Surpress ultraplot config loading which mpl does not recognize
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("ultraplot").setLevel(logging.WARNING)
>>>>>>> parent of 500e45b1 (Add xdist to image compare (#266))
    try:
        if config.getoption("--store-failed-only", False):
            config.pluginmanager.register(StoreFailedMplPlugin(config))
    except Exception as e:
        print(f"Error during plugin configuration: {e}")
