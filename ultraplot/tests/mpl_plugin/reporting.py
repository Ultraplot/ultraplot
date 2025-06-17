"""
HTML reporting module for matplotlib test results.

This module provides comprehensive HTML report generation with interactive features,
including visual comparisons, filtering capabilities, and responsive design.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

from .utils import (
    extract_test_name_from_filename,
    categorize_image_file,
    get_results_directory,
)


class HTMLReportGenerator:
    """Generates interactive HTML reports for matplotlib test results."""

    def __init__(self, config):
        self.config = config
        self.results_dir = get_results_directory(config)

    def generate_report(self, failed_tests_set):
        """Generate the complete HTML report."""
        if not self._should_generate_report():
            return

        print("\nGenerating HTML report for image comparison tests...")
        print(
            "Note: When using --store-failed-only, only failed tests will be included in the report"
        )

        test_results = self._process_test_results()
        if not test_results:
            print("No test results found for HTML report generation")
            return

        # Generate display names and mark failed tests
        self._enhance_test_results(test_results, failed_tests_set)

        # Generate HTML content
        html_content = self._generate_html_content(test_results)

        # Write the report
        report_path = self.results_dir / "mpl_comparison_report.html"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            f.write(html_content)

        print(f"HTML report generated at: {report_path}")

    def _should_generate_report(self):
        """Check if HTML report should be generated."""
        if not self.results_dir.exists():
            print(f"Results directory not found: {self.results_dir}")
            return False
        return True

    def _process_test_results(self):
        """Process test result files and organize by test."""
        test_results = {}

        # Recursively search for all PNG files
        for image_file in self.results_dir.rglob("*.png"):
            rel_path = image_file.relative_to(self.results_dir)
            parent_dir = rel_path.parent if rel_path.parent != Path(".") else None
            filename = image_file.name

            # Skip hash files
            if "hash" in filename:
                continue

            # Handle pytest-mpl directory structure
            if parent_dir:
                test_name = str(parent_dir)

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
                test_name = extract_test_name_from_filename(filename, test_id)
                image_type = categorize_image_file(filename, test_id)

                if test_name not in test_results:
                    test_results[test_name] = {
                        "baseline": None,
                        "result": None,
                        "diff": None,
                        "path": parent_dir,
                    }

                if image_type == "baseline":
                    test_results[test_name]["baseline"] = image_file
                elif image_type == "diff":
                    test_results[test_name]["diff"] = image_file
                elif image_type == "result" and not test_results[test_name]["result"]:
                    test_results[test_name]["result"] = image_file

        return test_results

    def _enhance_test_results(self, test_results, failed_tests_set):
        """Add display names and test status to results."""
        for test_name, data in test_results.items():
            # Generate display name
            if data["path"]:
                data["display_name"] = test_name.replace("/", ".").replace("\\", ".")
            else:
                data["display_name"] = test_name

            # Mark as failed if tracked during test execution
            data["test_failed"] = any(
                any(
                    pattern in nodeid
                    for pattern in [
                        test_name.replace(".", "::"),
                        test_name.replace(
                            "ultraplot.tests.", "ultraplot/tests/"
                        ).replace(".", "::"),
                        f"ultraplot/tests/{test_name.split('.')[-2]}.py::{test_name.split('.')[-1]}",
                    ]
                )
                for nodeid in failed_tests_set
            )

    def _generate_html_content(self, test_results):
        """Generate the complete HTML content."""
        html_parts = self._get_html_header()

        # Calculate statistics
        total_tests = len(test_results)
        failed_tests = sum(
            1
            for data in test_results.values()
            if data.get("test_failed", False) or data.get("diff")
        )
        passed_tests = sum(
            1
            for data in test_results.values()
            if data.get("baseline")
            and data.get("result")
            and not data.get("test_failed", False)
        )

        # Add summary section
        html_parts.extend(
            self._generate_summary_section(total_tests, passed_tests, failed_tests)
        )

        # Generate test case sections
        sorted_tests = sorted(
            test_results.items(), key=lambda x: x[1].get("display_name", x[0])
        )

        for test_name, data in sorted_tests:
            html_parts.extend(self._generate_test_case_section(test_name, data))

        # Add footer and scripts
        html_parts.extend(self._get_html_footer())

        return "\n".join(html_parts)

    def _get_html_header(self):
        """Get HTML header with CSS styling."""
        return [
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

    def _generate_summary_section(self, total_tests, passed_tests, failed_tests):
        """Generate the summary statistics section."""
        summary_note = ""
        if failed_tests > 0 and passed_tests == 0:
            summary_note = "<p><em>Note: Only failed tests are shown. Passed tests were cleaned up to reduce artifact size.</em></p>"

        return [
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

    def _generate_test_case_section(self, test_name, data):
        """Generate HTML section for a single test case."""
        display_name = data.get("display_name", test_name)

        # Determine test status
        if data.get("test_failed", False) or data.get("diff"):
            status = "failed"
            status_class = "status-failed"
            status_text = "FAILED"
        elif (
            data.get("baseline")
            and data.get("result")
            and not data.get("test_failed", False)
        ):
            status = "passed"
            status_class = "status-passed"
            status_text = "PASSED"
        elif data.get("result") and not data.get("baseline"):
            status = "unknown"
            status_class = "status-unknown"
            status_text = "UNKNOWN"
        else:
            status = "unknown"
            status_class = "status-unknown"
            status_text = "UNKNOWN"

        html_parts = [
            f"        <div class='test-case' data-status='{status}'>",
            "            <div class='test-header'>",
            f"                <span class='test-name'>{display_name}</span>",
            f"                <span class='test-status {status_class}'>{status_text}</span>",
            "            </div>",
            "            <div class='images-container'>",
            "                <div class='image-row'>",
        ]

        # Add baseline image column
        html_parts.extend(
            self._generate_image_column("Baseline (Expected)", data.get("baseline"))
        )

        # Add result image column
        html_parts.extend(
            self._generate_image_column("Result (Actual)", data.get("result"))
        )

        # Add diff image column (only if it exists)
        if data.get("diff"):
            html_parts.extend(
                self._generate_image_column("Difference", data.get("diff"))
            )

        html_parts.extend(
            [
                "                </div>",
                "            </div>",
                "        </div>",
            ]
        )

        return html_parts

    def _generate_image_column(self, title, image_path):
        """Generate HTML for an image column."""
        html_parts = [
            "                    <div class='image-column'>",
            f"                        <h4>{title}</h4>",
        ]

        if image_path:
            rel_path = image_path.relative_to(self.results_dir)
            html_parts.append(
                f"                        <img src='{rel_path}' alt='{title} image'>"
            )
        else:
            html_parts.append(
                f"                        <div class='no-image'>No {title.lower()} image</div>"
            )

        html_parts.append("                    </div>")
        return html_parts

    def _get_html_footer(self):
        """Get HTML footer with JavaScript and timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return [
            f"        <div class='timestamp'>Report generated on {timestamp}</div>",
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
