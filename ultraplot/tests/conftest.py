import os, shutil, pytest, re, numpy as np, ultraplot as uplt
from pathlib import Path
import warnings, logging, sys


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

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        """Hook that processes each test report."""
        # Delete successfull tests
        if not report.failed:
            if self._has_mpl_marker(report):
                self._remove_success(report)


class SkipMissingBaseline:
    def __init__(self, config):
        self.config = config
        baseline_path = config.getoption("--mpl-baseline-path", default=None)
        self.baseline_dir = None
        if baseline_path:
            self.baseline_dir = Path(baseline_path)

        # Don't run if we are generating baselines
        self.run = False
        if config.getoption("--mpl-generate-path", default=None):
            self.run = False
        if self.run:
            print(f"Skipping baseline images that don't exist")

    def baseline_exists(self, item):
        name = item.originalname
        print(f"Checking for baseline at: {self.baseline_dir / f'{name}.png'}")
        return Path(self.baseline_dir / f"{name}.png").exists()

    def skip_baseline_if_not_exists(self, item):
        if self.run == False or self.baseline_dir is None:
            return
        for mark in item.own_markers:
            if mark.name == "mpl_image_compare":
                if not self.baseline_exists(item):
                    pytest.skip(f"Baseline image does not exist")


def pytest_collection_modifyitems(config, items):
    helper = SkipMissingBaseline(config)
    for item in items:
        helper.skip_baseline_if_not_exists(item)


# Register the plugin if the option is used
def pytest_configure(config):
    print("Configuring StoreFailedMplPlugin")
    # Surpress ultraplot config loading which mpl does not recognize
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("ultraplot").setLevel(logging.WARNING)
    try:
        if config.getoption("--store-failed-only", False):
            print("Registering StoreFailedMplPlugin")
            config.pluginmanager.register(StoreFailedMplPlugin(config))
    except Exception as e:
        print(f"Error during plugin configuration: {e}")
