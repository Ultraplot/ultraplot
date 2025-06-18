"""
Utility functions for matplotlib test processing.

This module provides helper functions for file processing, test name extraction,
and other common operations used throughout the MPL plugin.
"""

import re
from pathlib import Path


def extract_test_name_from_filename(filename, test_id):
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


def categorize_image_file(filename, test_id):
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


def get_results_directory(config):
    """Get the results directory path from config."""
    results_path = (
        getattr(config.option, "mpl_results_path", None)
        or getattr(config, "_mpl_results_path", None)
        or "./mpl-results"
    )
    return Path(results_path)


def should_generate_html_report(config):
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


def get_failed_mpl_tests(config):
    """Get set of failed mpl test nodeids from the plugin."""
    # Look for our plugin instance
    for plugin in config.pluginmanager.get_plugins():
        if hasattr(plugin, "failed_mpl_tests"):
            return plugin.failed_mpl_tests
    return set()


def create_nodeid_to_path_mapping(nodeid):
    """Convert pytest nodeid to filesystem path pattern."""
    pattern = r"(?P<sep>::|/)|\[|\]|\.py"
    name = re.sub(
        pattern,
        lambda m: "." if m.group("sep") else "_" if m.group(0) == "[" else "",
        nodeid,
    )
    return name


def safe_path_conversion(path_input):
    """Safely convert path input to Path object, handling None values."""
    if path_input is None:
        return None
    return Path(path_input)


def count_mpl_tests(items):
    """Count the number of matplotlib image comparison tests in the item list."""
    return sum(
        1
        for item in items
        if any(mark.name == "mpl_image_compare" for mark in item.own_markers)
    )


def is_mpl_test(item):
    """Check if a test item is a matplotlib image comparison test."""
    return any(mark.name == "mpl_image_compare" for mark in item.own_markers)


def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 bytes"

    size_names = ["bytes", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def validate_config_paths(config):
    """Validate and normalize configuration paths."""
    results_path = config.getoption("--mpl-results-path", None) or "./results"
    baseline_path = config.getoption("--mpl-baseline-path", None) or "./baseline"

    return {
        "results": Path(results_path),
        "baseline": Path(baseline_path),
    }
