import os, shutil, pytest, re, numpy as np, ultraplot as uplt
from pathlib import Path
import warnings, logging


@pytest.fixture(autouse=True)
def _reset_numpy_seed():
    """
    Ensure all tests start with the same rng
    """
    seed = 51423
    np.random.seed(seed)


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
        else:
            print(f"Did not find {report.nodeid}")

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        """Hook that processes each test report."""
        if report.when == "call":
            # Delete successfull tests
            if report.failed == False:
                if self._has_mpl_marker(report):
                    self._remove_success(report)
            else:
                print(f"{report.failed=}")
                print(f"Test {report.nodeid} failed!")


# Register the plugin if the option is used
def pytest_configure(config):
    print("Configuring StoreFailedMplPlugin")
    # Surpress ultraplot config loading which mpl does not recognize
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("ultraplot").setLevel(logging.WARNING)
    if rc_file := config.getoption("--mpl-default-style", None):
        warnings.filterwarnings(
            "ignore",
            message=rf"Bad key .* in file .*" + rc_file,
            category=UserWarning,
            module="matplotlib",
        )
    try:
        if config.getoption("--store-failed-only", False):
            print("Registering StoreFailedMplPlugin")
            config.pluginmanager.register(StoreFailedMplPlugin(config))
    except Exception as e:
        print(f"Error during plugin configuration: {e}")
