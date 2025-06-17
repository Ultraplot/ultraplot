import os, shutil, pytest, re, numpy as np, ultraplot as uplt
from pathlib import Path
import warnings, logging
from datetime import datetime
import threading


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


# Global set to track directories scheduled for cleanup
_pending_cleanups = set()
_cleanup_lock = threading.Lock()


class StoreFailedMplPlugin:
    def __init__(self, config):
        self.config = config

        # Get base directories as Path objects
        self.result_dir = Path(config.getoption("--mpl-results-path", "./results"))
        self.baseline_dir = Path(config.getoption("--mpl-baseline-path", "./baseline"))

        # Track failed mpl tests for HTML report generation
        self.failed_mpl_tests = set()

        print(f"Store Failed MPL Plugin initialized")
        print(f"Result dir: {self.result_dir}")

    def _has_mpl_marker(self, report: pytest.TestReport):
        """Check if the test has the mpl_image_compare marker."""
        return report.keywords.get("mpl_image_compare", False)

    def _remove_success(self, report: pytest.TestReport):
        """Mark successful test images for deferred cleanup to eliminate blocking."""

        pattern = r"(?P<sep>::|/)|\[|\]|\.py"
        name = re.sub(
            pattern,
            lambda m: "." if m.group("sep") else "_" if m.group(0) == "[" else "",
            report.nodeid,
        )
        target = (self.result_dir / name).absolute()

        # Use hybrid approach: track for cleanup but don't block workers
        global _pending_cleanups
        with _cleanup_lock:
            if target.exists() and target.is_dir():
                _pending_cleanups.add(target)
                print(f"Marked for cleanup: {target}")

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        """Hook that processes each test report."""
        # Track failed mpl tests and queue successful ones for cleanup
        if report.when == "call" and self._has_mpl_marker(report):
            try:
                if report.outcome == "failed":
                    self.failed_mpl_tests.add(report.nodeid)
                    print(f"Tracking failed mpl test: {report.nodeid}")
                else:
                    # Mark successful tests for cleanup to reduce artifact size
                    self._remove_success(report)
            except Exception as e:
                # Log but don't fail on cleanup errors
                print(f"Warning: Error during test processing for {report.nodeid}: {e}")


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


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate HTML report after all tests have completed"""
    # Skip on workers, only run on the main process (improved xdist detection)
    if hasattr(config, "workerinput"):
        return

    # Check if we should generate the report
    if not _should_generate_html_report(config):
        return

    print("\nGenerating HTML report for image comparison tests...")
    print(
        "Note: When using --store-failed-only, only failed tests will be included in the report"
    )

    # Perform deferred cleanup now that all tests are done
    _perform_deferred_cleanup()

    # Get the results directory - handle both pytest-mpl options
    results_dir = _get_results_directory(config)

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

        # Handle pytest-mpl directory structure where images are in test-specific subdirectories
        if parent_dir:
            # The parent directory name is the test identifier
            test_name = str(parent_dir)

            # Initialize test result entry if it doesn't exist
            if test_name not in test_results:
                test_results[test_name] = {
                    "baseline": None,
                    "result": None,
                    "diff": None,
                    "path": parent_dir,
                }

            # Categorize files based on pytest-mpl naming convention
            if filename == "baseline.png":
                test_results[test_name]["baseline"] = image_file
            elif filename == "result.png":
                test_results[test_name]["result"] = image_file
            elif filename == "result-failed-diff.png":
                test_results[test_name]["diff"] = image_file
        else:
            # Fallback for files in root directory (legacy naming)
            test_id = image_file.stem
            test_name = _extract_test_name_from_filename(filename, test_id)
            image_type = _categorize_image_file(filename, test_id)

            # Initialize test result entry if it doesn't exist
            if test_name not in test_results:
                test_results[test_name] = {
                    "baseline": None,
                    "result": None,
                    "diff": None,
                    "path": parent_dir,
                }

            # Store the image file in the appropriate category
            if image_type == "baseline":
                test_results[test_name]["baseline"] = image_file
            elif image_type == "diff":
                test_results[test_name]["diff"] = image_file
            elif image_type == "result":
                # Only set result if not already set (prefer more specific naming)
                if not test_results[test_name]["result"]:
                    test_results[test_name]["result"] = image_file

    # Get failed test nodeids from the plugin
    failed_tests = _get_failed_mpl_tests(config)

    # Generate a better display name for each test
    for test_name, data in test_results.items():
        # For pytest-mpl, the test_name is already the full path, so use it directly
        # but clean it up to avoid duplication
        if data["path"]:
            # The test_name already contains the full path, so just use it
            data["display_name"] = test_name.replace("/", ".").replace("\\", ".")
        else:
            data["display_name"] = test_name

        # Mark as failed if we tracked it as failed during test execution
        # Convert test_name to match nodeid format for comparison
        test_nodeid_patterns = [
            test_name.replace(".", "::"),
            test_name.replace("ultraplot.tests.", "ultraplot/tests/").replace(
                ".", "::"
            ),
            f"ultraplot/tests/{test_name.split('.')[-2]}.py::{test_name.split('.')[-1]}",
        ]

        data["test_failed"] = any(
            any(pattern in nodeid for pattern in test_nodeid_patterns)
            for nodeid in failed_tests
        )

    # Generate the HTML
    html_output = generate_html_report(results_dir, test_results)

    # Write the HTML report
    report_path = results_dir / "mpl_comparison_report.html"
    with open(report_path, "w") as f:
        f.write(html_output)

    print(f"HTML report generated at: {report_path}")


def _should_generate_html_report(config):
    """Determine if HTML report should be generated."""
    # Check if matplotlib comparison tests are being used
    if hasattr(config.option, "mpl_results_path"):
        return True
    if hasattr(config, "_mpl_results_path"):
        return True
    # Check if any mpl_image_compare markers were collected
    if hasattr(config, "_mpl_image_compare_found"):
        return True
    return False


def _get_failed_mpl_tests(config):
    """Get set of failed mpl test nodeids from the plugin."""
    # Look for our plugin instance
    for plugin in config.pluginmanager.get_plugins():
        if isinstance(plugin, StoreFailedMplPlugin):
            return plugin.failed_mpl_tests
    return set()


def _get_results_directory(config):
    """Get the results directory path from config."""
    results_path = (
        getattr(config.option, "mpl_results_path", None)
        or getattr(config, "_mpl_results_path", None)
        or "./mpl-results"
    )
    return Path(results_path)


def _perform_deferred_cleanup():
    """Perform cleanup of successful test directories after all tests complete."""
    global _pending_cleanups

    with _cleanup_lock:
        cleanup_list = list(_pending_cleanups)
        _pending_cleanups.clear()

    if cleanup_list:
        print(f"Performing deferred cleanup of {len(cleanup_list)} directories...")
        for target in cleanup_list:
            try:
                if target.exists() and target.is_dir():
                    print(f"Removing successful test images: {target}")
                    shutil.rmtree(target)
            except (FileNotFoundError, OSError, PermissionError):
                # Directory might have been removed already - that's fine
                pass
            except Exception as e:
                print(f"Warning: Error during cleanup of {target}: {e}")
        print("Deferred cleanup completed")
    else:
        print("No directories to clean up")


def _extract_test_name_from_filename(filename, test_id):
    """Extract test name from various pytest-mpl filename patterns."""
    # Handle different pytest-mpl filename patterns
    if filename.endswith("-expected.png"):
        return test_id.replace("-expected", "")
    elif filename.endswith("-failed-diff.png"):
        return test_id.replace("-failed-diff", "")
    elif filename.endswith("-result.png"):
        return test_id.replace("-result", "")
    elif filename.endswith("-actual.png"):
        return test_id.replace("-actual", "")
    else:
        # Remove common result suffixes if present
        possible_test_name = test_id
        for suffix in ["-result", "-actual", "-diff"]:
            if possible_test_name.endswith(suffix):
                possible_test_name = possible_test_name.replace(suffix, "")
        return possible_test_name


def _categorize_image_file(filename, test_id):
    """Categorize an image file based on its filename pattern."""
    if filename.endswith("-expected.png"):
        return "baseline"
    elif filename.endswith("-failed-diff.png"):
        return "diff"
    elif filename.endswith("-result.png") or filename.endswith("-actual.png"):
        return "result"
    else:
        # Default assumption for uncategorized files
        return "result"


def generate_html_report(results_dir, test_results):
    """Generate an HTML report for matplotlib comparison test results."""

    # Start building the HTML
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "    <meta charset='UTF-8'>",
        "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "    <title>Matplotlib Image Comparison Report</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
        "        .container { max-width: 1200px; margin: 0 auto; }",
        "        h1 { color: #333; text-align: center; margin-bottom: 30px; }",
        "        .summary { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "        .test-case { background: white; margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "        .test-header { background: #f8f9fa; padding: 15px; border-bottom: 1px solid #dee2e6; }",
        "        .test-name { font-size: 18px; font-weight: bold; color: #333; }",
        "        .test-status { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; margin-left: 10px; }",
        "        .status-passed { background-color: #28a745; }",
        "        .status-failed { background-color: #dc3545; }",
        "        .status-unknown { background-color: #6c757d; }",
        "        .images-container { padding: 20px; }",
        "        .image-row { display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start; }",
        "        .image-column { flex: 1; min-width: 300px; }",
        "        .image-column h4 { margin-top: 0; color: #555; text-align: center; }",
        "        .image-column img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }",
        "        .no-image { text-align: center; color: #999; font-style: italic; padding: 20px; background: #f8f9fa; border-radius: 4px; }",
        "        .stats { display: flex; gap: 20px; }",
        "        .stat-item { flex: 1; text-align: center; padding: 10px; background: #e9ecef; border-radius: 4px; }",
        "        .stat-number { font-size: 24px; font-weight: bold; color: #333; }",
        "        .stat-label { font-size: 14px; color: #666; }",
        "        .timestamp { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }",
        "        .filter-controls { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }",
        "        .filter-btn { display: inline-block; padding: 8px 16px; margin: 0 5px; border: 2px solid #007bff; border-radius: 4px; background: white; color: #007bff; cursor: pointer; text-decoration: none; font-weight: bold; }",
        "        .filter-btn:hover { background: #007bff; color: white; }",
        "        .filter-btn.active { background: #007bff; color: white; }",
        "        .hidden { display: none !important; }",
        "        @media (max-width: 768px) {",
        "            .image-row { flex-direction: column; }",
        "            .stats { flex-direction: column; }",
        "            .filter-btn { display: block; margin: 5px auto; width: 150px; }",
        "        }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class='container'>",
        "        <h1>Matplotlib Image Comparison Report</h1>",
        "        <div class='filter-controls'>",
        "            <button class='filter-btn active' onclick='filterTests(\"all\")'>Show All</button>",
        "            <button class='filter-btn' onclick='filterTests(\"failed\")'>Failed Only</button>",
        "            <button class='filter-btn' onclick='filterTests(\"passed\")'>Passed Only</button>",
        "            <button class='filter-btn' onclick='filterTests(\"unknown\")'>Unknown</button>",
        "        </div>",
    ]

    # Calculate statistics - when using --store-failed-only,
    # we primarily focus on failed tests since passed ones are cleaned up
    total_tests = len(test_results)
    failed_tests = 0
    passed_tests = 0
    unknown_tests = 0

    for data in test_results.values():
        if data.get("test_failed", False) or data.get("diff"):
            failed_tests += 1
        elif (
            data.get("baseline")
            and data.get("result")
            and not data.get("test_failed", False)
        ):
            passed_tests += 1
        else:
            unknown_tests += 1

    # Add summary section with note about artifact reduction
    summary_note = ""
    if failed_tests > 0 and passed_tests == 0:
        summary_note = "<p><em>Note: Only failed tests are shown. Passed tests were cleaned up to reduce artifact size.</em></p>"

    html_parts.extend(
        [
            "        <div class='summary'>",
            "            <h2>Summary</h2>",
            f"            {summary_note}",
            "            <div class='stats'>",
            f"                <div class='stat-item'><div class='stat-number'>{total_tests}</div><div class='stat-label'>Tests with Images</div></div>",
            f"                <div class='stat-item'><div class='stat-number'>{passed_tests}</div><div class='stat-label'>Passed</div></div>",
            f"                <div class='stat-item'><div class='stat-number'>{failed_tests}</div><div class='stat-label'>Failed</div></div>",
            "            </div>",
            "        </div>",
        ]
    )

    # Sort test results by name for consistent display
    sorted_tests = sorted(
        test_results.items(), key=lambda x: x[1].get("display_name", x[0])
    )

    # Generate test case sections
    for test_name, data in sorted_tests:
        display_name = data.get("display_name", test_name)

        # Determine test status using tracked test results and file presence
        if data.get("test_failed", False) or data.get("diff"):
            # If we tracked it as failed or there's a diff image, the test failed
            status = "failed"
            status_class = "status-failed"
            status_text = "FAILED"
        elif (
            data.get("baseline")
            and data.get("result")
            and not data.get("test_failed", False)
        ):
            # If there's baseline and result and we didn't track it as failed, test passed
            status = "passed"
            status_class = "status-passed"
            status_text = "PASSED"
        elif data.get("result") and not data.get("baseline"):
            # If there's only result but no baseline, it's a new test (unknown)
            status = "unknown"
            status_class = "status-unknown"
            status_text = "UNKNOWN"
        else:
            # Any other case is unknown
            status = "unknown"
            status_class = "status-unknown"
            status_text = "UNKNOWN"

        html_parts.extend(
            [
                f"        <div class='test-case' data-status='{status}'>",
                "            <div class='test-header'>",
                f"                <span class='test-name'>{display_name}</span>",
                f"                <span class='test-status {status_class}'>{status_text}</span>",
                "            </div>",
                "            <div class='images-container'>",
                "                <div class='image-row'>",
            ]
        )

        # Add baseline image column
        html_parts.append("                    <div class='image-column'>")
        html_parts.append("                        <h4>Baseline (Expected)</h4>")
        if data.get("baseline"):
            rel_path = data["baseline"].relative_to(results_dir)
            html_parts.append(
                f"                        <img src='{rel_path}' alt='Baseline image for {display_name}'>"
            )
        else:
            html_parts.append(
                "                        <div class='no-image'>No baseline image</div>"
            )
        html_parts.append("                    </div>")

        # Add result image column
        html_parts.append("                    <div class='image-column'>")
        html_parts.append("                        <h4>Result (Actual)</h4>")
        if data.get("result"):
            rel_path = data["result"].relative_to(results_dir)
            html_parts.append(
                f"                        <img src='{rel_path}' alt='Result image for {display_name}'>"
            )
        else:
            html_parts.append(
                "                        <div class='no-image'>No result image</div>"
            )
        html_parts.append("                    </div>")

        # Add diff image column (only if it exists)
        if data.get("diff"):
            html_parts.append("                    <div class='image-column'>")
            html_parts.append("                        <h4>Difference</h4>")
            rel_path = data["diff"].relative_to(results_dir)
            html_parts.append(
                f"                        <img src='{rel_path}' alt='Difference image for {display_name}'>"
            )
            html_parts.append("                    </div>")

        html_parts.extend(
            [
                "                </div>",
                "            </div>",
                "        </div>",
            ]
        )

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_parts.append(
        f"        <div class='timestamp'>Report generated on {timestamp}</div>"
    )

    # Add JavaScript for filtering functionality
    html_parts.extend(
        [
            "    </div>",
            "    <script>",
            "        function filterTests(filterType) {",
            "            const testCases = document.querySelectorAll('.test-case');",
            "            const filterBtns = document.querySelectorAll('.filter-btn');",
            "            ",
            "            // Remove active class from all buttons",
            "            filterBtns.forEach(btn => btn.classList.remove('active'));",
            "            ",
            "            // Add active class to clicked button",
            "            event.target.classList.add('active');",
            "            ",
            "            // Filter test cases",
            "            testCases.forEach(testCase => {",
            "                const status = testCase.getAttribute('data-status');",
            "                if (filterType === 'all') {",
            "                    testCase.classList.remove('hidden');",
            "                } else if (filterType === 'failed' && status === 'failed') {",
            "                    testCase.classList.remove('hidden');",
            "                } else if (filterType === 'passed' && status === 'passed') {",
            "                    testCase.classList.remove('hidden');",
            "                } else if (filterType === 'unknown' && status === 'unknown') {",
            "                    testCase.classList.remove('hidden');",
            "                } else {",
            "                    testCase.classList.add('hidden');",
            "                }",
            "            });",
            "        }",
            "    </script>",
            "</body>",
            "</html>",
        ]
    )

    return "\n".join(html_parts)


# Register the plugin if the option is used
def pytest_configure(config):
    # Surpress ultraplot config loading which mpl does not recognize
    logging.getLogger("matplotlib").setLevel(logging.ERROR)
    logging.getLogger("ultraplot").setLevel(logging.WARNING)
    try:
        if config.getoption("--store-failed-only", False):
            config.pluginmanager.register(StoreFailedMplPlugin(config))
    except Exception as e:
        print(f"Error during plugin configuration: {e}")
