import shutil
import pytest
import re
import numpy as np
import ultraplot as uplt
from pathlib import Path
import logging
from pytest_mpl.summary.html import generate_summary_html


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
    # Surpress ultraplot config loading which mpl does not recognize
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("ultraplot").setLevel(logging.WARNING)
    # try:
    #     if config.getoption("--store-failed-only", False):
    #         config.pluginmanager.register(StoreFailedMplPlugin(config))
    # except Exception as e:
    #     print(f"Error during plugin configuration: {e}")


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate HTML report after all tests have completed"""
    # Skip on workers, only run on the main process
    if hasattr(config, "workerinput"):
        return

    # skip if not doing mpl
    if not hasattr(config.option, "mpl") or not config.option.mpl:
        return

    print("\nGenerating HTML report for image comparison tests...")

    # Get the results directory
    results_dir = Path(getattr(config.option, "mpl_results_path", "./mpl-results"))
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return

    # Collect all image files and organize by test
    test_results = {}

    # Recursively search for all PNG files
    for image_file in results_dir.rglob("*.png"):
        # Get path relative to results directory for storing in dict
        rel_path = image_file.relative_to(results_dir)
        parent_dir = rel_path.parent if rel_path.parent != Path(".") else None

        filename = image_file.name

        # Skip hash files
        if "hash" in filename:
            continue

        # Generate a more unique test identifier that includes parent directory if available
        test_id = str(parent_dir / image_file.stem) if parent_dir else image_file.stem

        # Handle different pytest-mpl filename patterns, preserving directory structure
        if filename.endswith("-expected.png"):
            # This is a baseline image
            test_name = test_id.replace("-expected", "")
            if test_name not in test_results:
                test_results[test_name] = {
                    "baseline": None,
                    "result": None,
                    "diff": None,
                    "path": parent_dir,
                }
            test_results[test_name]["baseline"] = image_file

        elif filename.endswith("-failed-diff.png"):
            # This is a diff image for a failed test
            test_name = test_id.replace("-failed-diff", "")
            if test_name not in test_results:
                test_results[test_name] = {
                    "baseline": None,
                    "result": None,
                    "diff": None,
                    "path": parent_dir,
                }
            test_results[test_name]["diff"] = image_file

        else:
            # Try to extract test name and check if it corresponds to a real test result
            # Deal with various possible naming conventions
            possible_test_name = test_id

            # Remove common result suffixes if present
            for suffix in ["-result", "-actual", "-diff"]:
                if possible_test_name.endswith(suffix):
                    possible_test_name = possible_test_name.replace(suffix, "")

            if possible_test_name not in test_results:
                test_results[possible_test_name] = {
                    "baseline": None,
                    "result": None,
                    "diff": None,
                    "path": parent_dir,
                }

            # Assume it's a result image if not obviously something else
            if not test_results[possible_test_name]["result"]:
                test_results[possible_test_name]["result"] = image_file

    # Generate a better display name for each test
    for test_name, data in test_results.items():
        # Use directory structure to create more descriptive names
        if data["path"]:
            # Convert path to a more readable format, replacing / with .
            module_path = str(data["path"]).replace("/", ".").replace("\\", ".")
            data["display_name"] = f"{module_path}.{Path(test_name).name}"
        else:
            data["display_name"] = test_name

    # Generate the HTML
    html_output = generate_summary_html(results_dir, test_results)

    # Write the HTML report
    report_path = results_dir / "mpl_comparison_report.html"
    with open(report_path, "w") as f:
        f.write(html_output)

    print(f"HTML report generated at: {report_path}")
