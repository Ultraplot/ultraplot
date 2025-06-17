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
        self.template_dir = Path(__file__).parent / "templates"
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

        # Copy template files to results directory
        self._copy_template_assets()

        # Generate HTML content
        html_content = self._generate_html_content(test_results)

        # Write the report
        report_path = self.results_dir / "index.html"
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

    def _copy_template_assets(self):
        """Copy CSS and JS files to results directory."""
        try:
            # Copy CSS file
            css_src = self.template_dir / "styles.css"
            css_dst = self.results_dir / "styles.css"
            if css_src.exists():
                shutil.copy2(css_src, css_dst)

            # Copy JS file
            js_src = self.template_dir / "scripts.js"
            js_dst = self.results_dir / "scripts.js"
            if js_src.exists():
                shutil.copy2(js_src, js_dst)
        except Exception as e:
            print(f"Warning: Could not copy template assets: {e}")

    def _load_template(self, template_name):
        """Load a template file."""
        template_path = self.template_dir / template_name
        try:
            with open(template_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Template {template_name} not found, using fallback")
            return None

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
        """Generate the complete HTML content using templates."""
        # Load main template
        template = self._load_template("report.html")
        if not template:
            return self._generate_fallback_html(test_results)

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
        unknown_tests = total_tests - failed_tests - passed_tests

        # Generate test cases HTML
        test_cases_html = self._generate_all_test_cases(test_results)

        # Replace placeholders in template
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = template.replace(
            "{{title}}", "UltraPlot Image Comparison Report"
        )
        html_content = html_content.replace("{{total_tests}}", str(total_tests))
        html_content = html_content.replace("{{failed_count}}", str(failed_tests))
        html_content = html_content.replace("{{passed_count}}", str(passed_tests))
        html_content = html_content.replace("{{unknown_count}}", str(unknown_tests))
        html_content = html_content.replace("{{test_cases}}", test_cases_html)
        html_content = html_content.replace("{{timestamp}}", timestamp)

        return html_content

    def _generate_all_test_cases(self, test_results):
        """Generate HTML for all test cases."""
        test_cases_html = []

        # Sort tests by display name
        sorted_tests = sorted(
            test_results.items(), key=lambda x: x[1].get("display_name", x[0])
        )

        for test_name, data in sorted_tests:
            test_case_html = self._generate_test_case_html(test_name, data)
            test_cases_html.append(test_case_html)

        return "\n".join(test_cases_html)

    def _generate_test_case_html(self, test_name, data):
        """Generate HTML for a single test case."""
        display_name = data.get("display_name", test_name)

        # Determine test status
        if data.get("test_failed", False) or data.get("diff"):
            status = "failed"
            status_text = "FAILED"
        elif (
            data.get("baseline")
            and data.get("result")
            and not data.get("test_failed", False)
        ):
            status = "passed"
            status_text = "PASSED"
        else:
            status = "unknown"
            status_text = "UNKNOWN"

        # Generate image columns
        image_columns = []

        # Add baseline image column
        if data.get("baseline"):
            rel_path = data["baseline"].relative_to(self.results_dir)
            image_columns.append(
                f"""
                <div class='image-column'>
                    <h4>Baseline (Expected)</h4>
                    <img src='{rel_path}' alt='Baseline image'>
                </div>"""
            )
        else:
            image_columns.append(
                """
                <div class='image-column'>
                    <h4>Baseline (Expected)</h4>
                    <div class='no-image'>No baseline image</div>
                </div>"""
            )

        # Add result image column
        if data.get("result"):
            rel_path = data["result"].relative_to(self.results_dir)
            image_columns.append(
                f"""
                <div class='image-column'>
                    <h4>Result (Actual)</h4>
                    <img src='{rel_path}' alt='Result image'>
                </div>"""
            )
        else:
            image_columns.append(
                """
                <div class='image-column'>
                    <h4>Result (Actual)</h4>
                    <div class='no-image'>No result image</div>
                </div>"""
            )

        # Add diff image column (only if it exists)
        if data.get("diff"):
            rel_path = data["diff"].relative_to(self.results_dir)
            image_columns.append(
                f"""
                <div class='image-column'>
                    <h4>Difference</h4>
                    <img src='{rel_path}' alt='Difference image'>
                </div>"""
            )

        image_columns_html = "\n".join(image_columns)

        return f"""
        <div class="test-case" data-status="{status}">
            <div class="test-header">
                <div class="test-name">{display_name}</div>
                <div class="status-badge {status}">{status_text}</div>
            </div>
            <div class="test-content">
                <div class="images-container">
                    {image_columns_html}
                </div>
            </div>
        </div>"""

    def _generate_fallback_html(self, test_results):
        """Generate fallback HTML if templates are not available."""
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
        unknown_tests = total_tests - failed_tests - passed_tests

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>UltraPlot Image Comparison Report</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
            "        .container { max-width: 1200px; margin: 0 auto; }",
            "        h1 { color: #333; text-align: center; margin-bottom: 30px; }",
            "        .summary { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }",
            "        .test-case { background: white; margin-bottom: 20px; border-radius: 8px; overflow: hidden; }",
            "        .test-header { background: #f8f9fa; padding: 15px; display: flex; justify-content: space-between; }",
            "        .test-name { font-size: 18px; font-weight: bold; }",
            "        .status-badge { padding: 5px 10px; border-radius: 15px; color: white; font-size: 12px; }",
            "        .status-badge.failed { background: #dc3545; }",
            "        .status-badge.passed { background: #28a745; }",
            "        .status-badge.unknown { background: #6c757d; }",
            "        .images-container { padding: 20px; display: flex; gap: 20px; flex-wrap: wrap; }",
            "        .image-column { flex: 1; min-width: 300px; }",
            "        .image-column h4 { margin-top: 0; color: #555; text-align: center; }",
            "        .image-column img { max-width: 100%; height: auto; border: 1px solid #ddd; }",
            "        .no-image { text-align: center; color: #999; font-style: italic; padding: 20px; background: #f8f9fa; }",
            "        .filter-btn { padding: 8px 16px; margin: 5px; border: 2px solid #007bff; background: white; color: #007bff; cursor: pointer; }",
            "        .filter-btn.active { background: #007bff; color: white; }",
            "        .hidden { display: none !important; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <div class='container'>",
            "        <h1>UltraPlot Image Comparison Report</h1>",
            "        <div class='summary'>",
            f"            <p>Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests} | Unknown: {unknown_tests}</p>",
            "        </div>",
            "        <div style='text-align: center; margin-bottom: 20px;'>",
            "            <button class='filter-btn' onclick='filterTests(\"all\")'>Show All</button>",
            "            <button class='filter-btn active' onclick='filterTests(\"failed\")'>Failed Only</button>",
            "            <button class='filter-btn' onclick='filterTests(\"passed\")'>Passed Only</button>",
            "            <button class='filter-btn' onclick='filterTests(\"unknown\")'>Unknown</button>",
            "        </div>",
        ]

        # Add test cases
        for test_name, data in sorted(test_results.items()):
            html_parts.append(self._generate_test_case_html(test_name, data))

        # Add footer with basic JavaScript
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_parts.extend(
            [
                f"        <div style='text-align: center; margin-top: 30px; color: #666;'>Report generated on {timestamp}</div>",
                "    </div>",
                "    <script>",
                "        function filterTests(filterType) {",
                "            const testCases = document.querySelectorAll('.test-case');",
                "            const filterBtns = document.querySelectorAll('.filter-btn');",
                "            filterBtns.forEach(btn => btn.classList.remove('active'));",
                "            if (event && event.target) event.target.classList.add('active');",
                "            testCases.forEach(testCase => {",
                "                const status = testCase.getAttribute('data-status');",
                "                if (filterType === 'all' || status === filterType) {",
                "                    testCase.classList.remove('hidden');",
                "                } else {",
                "                    testCase.classList.add('hidden');",
                "                }",
                "            });",
                "        }",
                "        document.addEventListener('DOMContentLoaded', function() {",
                "            filterTests('failed');",
                "        });",
                "    </script>",
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(html_parts)
