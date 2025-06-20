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
        # Ensure template directory exists
        if not self.template_dir.exists():
            print(f"Warning: Template directory not found: {self.template_dir}")

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
        print(f"Template directory: {self.template_dir}")
        print(f"Results directory: {self.results_dir}")
        print("Open the report in a web browser to view the results.")

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
                print(f"Copied CSS to: {css_dst}")
            else:
                print(f"Warning: CSS template not found at: {css_src}")

            # Copy JS file
            js_src = self.template_dir / "scripts.js"
            js_dst = self.results_dir / "scripts.js"
            if js_src.exists():
                shutil.copy2(js_src, js_dst)
                print(f"Copied JS to: {js_dst}")
            else:
                print(f"Warning: JS template not found at: {js_src}")
        except Exception as e:
            print(f"Error copying template assets: {e}")

    def _load_template(self, template_name):
        """Load a template file."""
        template_path = self.template_dir / template_name
        print(f"Attempting to load template: {template_path}")
        print(f"Template exists: {template_path.exists()}")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
                print(
                    f"Successfully loaded template: {template_path} ({len(content)} chars)"
                )
                return content
        except FileNotFoundError:
            print(
                f"Warning: Template {template_name} not found at {template_path}, using fallback"
            )
            return None
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
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
        """Generate the complete HTML content with enhanced inline styling."""
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

        # Enhanced CSS styling
        css_content = """<style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: white; border-radius: 8px; padding: 30px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .header h1 { color: #2c3e50; margin-bottom: 20px; font-size: 2.5em; font-weight: 300; text-align: center; }
            .summary { display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; }
            .summary-item { background: #f8f9fa; border-radius: 6px; padding: 15px 20px; text-align: center; min-width: 120px; border-left: 4px solid #6c757d; }
            .summary-item.failed { border-left-color: #dc3545; background: #fff5f5; }
            .summary-item.passed { border-left-color: #28a745; background: #f0fff4; }
            .summary-item.unknown { border-left-color: #ffc107; background: #fffbf0; }
            .summary-item .count { display: block; font-size: 2em; font-weight: bold; color: #2c3e50; }
            .summary-item .label { font-size: 0.9em; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; }
            .filter-controls { margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
            .filter-btn { background: white; border: 2px solid #dee2e6; border-radius: 25px; padding: 10px 20px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.3s ease; color: #495057; }
            .filter-btn:hover { background: #f8f9fa; border-color: #adb5bd; }
            .filter-btn.active { background: #007bff; border-color: #007bff; color: white; }
            .test-results { display: flex; flex-direction: column; gap: 15px; }
            .test-case { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; transition: all 0.3s ease; }
            .test-case:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
            .test-case.hidden { display: none; }
            .test-header { padding: 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
            .test-name { font-weight: 600; font-size: 1.1em; color: #2c3e50; }
            .status-badge { padding: 5px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
            .status-badge.failed { background: #dc3545; color: white; }
            .status-badge.passed { background: #28a745; color: white; }
            .status-badge.unknown { background: #ffc107; color: #212529; }
            .test-content { padding: 20px; }
            .images-container { display: flex; gap: 20px; flex-wrap: wrap; }
            .image-column { flex: 1; min-width: 300px; max-width: 400px; }
            .image-column h4 { margin-bottom: 10px; color: #495057; font-size: 1em; font-weight: 600; text-align: center; padding: 10px; background: #f8f9fa; border-radius: 4px; }
            .image-column img { width: 100%; height: auto; border: 1px solid #dee2e6; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: zoom-in; }
            .no-image { padding: 40px 20px; text-align: center; color: #6c757d; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 4px; font-style: italic; }
            .timestamp { text-align: center; color: #6c757d; font-size: 0.9em; margin-top: 30px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            @media (max-width: 768px) { .container { padding: 10px; } .header { padding: 20px; } .header h1 { font-size: 2em; } .summary { justify-content: center; } .summary-item { min-width: 100px; } .test-header { flex-direction: column; align-items: flex-start; } .images-container { flex-direction: column; } .image-column { min-width: 100%; max-width: 100%; } .filter-controls { justify-content: center; } }
        </style>"""

        # Enhanced JavaScript
        js_content = """<script>
            function filterTests(filterType) {
                const testCases = document.querySelectorAll('.test-case');
                const filterBtns = document.querySelectorAll('.filter-btn');
                filterBtns.forEach(btn => btn.classList.remove('active'));
                if (event && event.target) {
                    event.target.classList.add('active');
                } else {
                    const targetBtn = Array.from(filterBtns).find(btn =>
                        btn.textContent.toLowerCase().includes(filterType === 'all' ? 'show all' : filterType)
                    );
                    if (targetBtn) targetBtn.classList.add('active');
                }
                testCases.forEach(testCase => {
                    const status = testCase.getAttribute('data-status');
                    if (filterType === 'all' || status === filterType) {
                        testCase.classList.remove('hidden');
                    } else {
                        testCase.classList.add('hidden');
                    }
                });
            }

            function setupImageZoom() {
                const images = document.querySelectorAll('.image-column img');
                images.forEach(img => {
                    img.addEventListener('click', function() {
                        if (this.style.position === 'fixed') {
                            this.style.position = '';
                            this.style.top = '';
                            this.style.left = '';
                            this.style.transform = '';
                            this.style.maxWidth = '100%';
                            this.style.maxHeight = '';
                            this.style.zIndex = '';
                            this.style.cursor = 'zoom-in';
                            document.body.style.overflow = '';
                            const backdrop = document.querySelector('.image-backdrop');
                            if (backdrop) backdrop.remove();
                        } else {
                            const backdrop = document.createElement('div');
                            backdrop.className = 'image-backdrop';
                            backdrop.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9998; cursor: zoom-out;';
                            backdrop.addEventListener('click', () => this.click());
                            document.body.appendChild(backdrop);
                            this.style.position = 'fixed';
                            this.style.top = '50%';
                            this.style.left = '50%';
                            this.style.transform = 'translate(-50%, -50%)';
                            this.style.maxWidth = '90vw';
                            this.style.maxHeight = '90vh';
                            this.style.zIndex = '9999';
                            this.style.cursor = 'zoom-out';
                            document.body.style.overflow = 'hidden';
                        }
                    });
                });
            }

            document.addEventListener('DOMContentLoaded', function() {
                filterTests('failed');
                setupImageZoom();
            });
        </script>"""

        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UltraPlot Image Comparison Report</title>
    {css_content}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>UltraPlot Image Comparison Report</h1>
            <div class="summary">
                <div class="summary-item">
                    <span class="count">{total_tests}</span>
                    <span class="label">Total Tests</span>
                </div>
                <div class="summary-item failed">
                    <span class="count">{failed_tests}</span>
                    <span class="label">Failed</span>
                </div>
                <div class="summary-item passed">
                    <span class="count">{passed_tests}</span>
                    <span class="label">Passed</span>
                </div>
                <div class="summary-item unknown">
                    <span class="count">{unknown_tests}</span>
                    <span class="label">Unknown</span>
                </div>
            </div>
        </div>

        <div class="filter-controls">
            <button class="filter-btn" onclick="filterTests('all')">Show All</button>
            <button class="filter-btn active" onclick="filterTests('failed')">Failed Only</button>
            <button class="filter-btn" onclick="filterTests('passed')">Passed Only</button>
            <button class="filter-btn" onclick="filterTests('unknown')">Unknown</button>
        </div>

        <div class="test-results">
            {test_cases_html}
        </div>

        <div class="timestamp">Report generated on {timestamp}</div>
    </div>
    {js_content}
</body>
</html>"""

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

        # Try to load external CSS for better styling
        css_content = ""
        css_template = self._load_template("styles.css")
        if css_template:
            css_content = f"<style>{css_template}</style>"
        else:
            css_content = """<style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; margin: 0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #2c3e50; margin-bottom: 30px; font-size: 2.5em; font-weight: 300; text-align: center; }
                .summary { background: white; border-radius: 8px; padding: 30px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .summary p { display: flex; gap: 20px; justify-content: center; margin: 0; font-size: 1.1em; }
                .test-case { background: white; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }
                .test-header { background: #f8f9fa; padding: 20px; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center; }
                .test-name { font-size: 1.1em; font-weight: 600; color: #2c3e50; }
                .status-badge { padding: 5px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 600; text-transform: uppercase; }
                .status-badge.failed { background: #dc3545; color: white; }
                .status-badge.passed { background: #28a745; color: white; }
                .status-badge.unknown { background: #ffc107; color: #212529; }
                .images-container { padding: 20px; display: flex; gap: 20px; flex-wrap: wrap; }
                .image-column { flex: 1; min-width: 300px; max-width: 400px; }
                .image-column h4 { margin-bottom: 10px; color: #495057; font-size: 1em; font-weight: 600; text-align: center; padding: 10px; background: #f8f9fa; border-radius: 4px; }
                .image-column img { width: 100%; height: auto; border: 1px solid #dee2e6; border-radius: 4px; cursor: zoom-in; }
                .no-image { padding: 40px 20px; text-align: center; color: #6c757d; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 4px; font-style: italic; }
                .filter-controls { text-align: center; margin-bottom: 20px; }
                .filter-btn { background: white; border: 2px solid #dee2e6; border-radius: 25px; padding: 10px 20px; cursor: pointer; font-size: 14px; font-weight: 500; color: #495057; margin: 0 5px; transition: all 0.3s ease; }
                .filter-btn:hover { background: #f8f9fa; border-color: #adb5bd; }
                .filter-btn.active { background: #007bff; border-color: #007bff; color: white; }
                .hidden { display: none !important; }
                @media (max-width: 768px) { .images-container { flex-direction: column; } .image-column { min-width: 100%; max-width: 100%; } }
            </style>"""

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>UltraPlot Image Comparison Report</title>",
            css_content,
            "</head>",
            "<body>",
            "    <div class='container'>",
            "        <h1>UltraPlot Image Comparison Report</h1>",
            "        <div class='summary'>",
            f"            <p><span>Total: {total_tests}</span> <span>Passed: {passed_tests}</span> <span>Failed: {failed_tests}</span> <span>Unknown: {unknown_tests}</span></p>",
            "        </div>",
            "        <div class='filter-controls'>",
            "            <button class='filter-btn' onclick='filterTests(\"all\")'>Show All</button>",
            "            <button class='filter-btn active' onclick='filterTests(\"failed\")'>Failed Only</button>",
            "            <button class='filter-btn' onclick='filterTests(\"passed\")'>Passed Only</button>",
            "            <button class='filter-btn' onclick='filterTests(\"unknown\")'>Unknown</button>",
            "        </div>",
        ]

        # Add test cases
        for test_name, data in sorted(test_results.items()):
            html_parts.append(self._generate_test_case_html(test_name, data))

        # Try to load external JavaScript or use inline fallback
        js_content = ""
        js_template = self._load_template("scripts.js")
        if js_template:
            js_content = f"<script>{js_template}</script>"
        else:
            js_content = """<script>
                function filterTests(filterType) {
                    const testCases = document.querySelectorAll('.test-case');
                    const filterBtns = document.querySelectorAll('.filter-btn');
                    filterBtns.forEach(btn => btn.classList.remove('active'));
                    if (event && event.target) {
                        event.target.classList.add('active');
                    } else {
                        const targetBtn = Array.from(filterBtns).find(btn =>
                            btn.textContent.toLowerCase().includes(filterType === 'all' ? 'show all' : filterType)
                        );
                        if (targetBtn) targetBtn.classList.add('active');
                    }
                    testCases.forEach(testCase => {
                        const status = testCase.getAttribute('data-status');
                        if (filterType === 'all' || status === filterType) {
                            testCase.classList.remove('hidden');
                        } else {
                            testCase.classList.add('hidden');
                        }
                    });
                }

                // Setup image zoom
                function setupImageZoom() {
                    const images = document.querySelectorAll('.image-column img');
                    images.forEach(img => {
                        img.style.cursor = 'zoom-in';
                        img.addEventListener('click', function() {
                            if (this.style.position === 'fixed') {
                                this.style.position = '';
                                this.style.top = '';
                                this.style.left = '';
                                this.style.transform = '';
                                this.style.maxWidth = '100%';
                                this.style.maxHeight = '';
                                this.style.zIndex = '';
                                this.style.cursor = 'zoom-in';
                                document.body.style.overflow = '';
                                const backdrop = document.querySelector('.image-backdrop');
                                if (backdrop) backdrop.remove();
                            } else {
                                const backdrop = document.createElement('div');
                                backdrop.className = 'image-backdrop';
                                backdrop.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9998; cursor: zoom-out;';
                                backdrop.addEventListener('click', () => this.click());
                                document.body.appendChild(backdrop);

                                this.style.position = 'fixed';
                                this.style.top = '50%';
                                this.style.left = '50%';
                                this.style.transform = 'translate(-50%, -50%)';
                                this.style.maxWidth = '90vw';
                                this.style.maxHeight = '90vh';
                                this.style.zIndex = '9999';
                                this.style.cursor = 'zoom-out';
                                document.body.style.overflow = 'hidden';
                            }
                        });
                    });
                }

                document.addEventListener('DOMContentLoaded', function() {
                    filterTests('failed');
                    setupImageZoom();
                });
            </script>"""

        # Add footer with JavaScript and timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_parts.extend(
            [
                f"        <div style='text-align: center; margin-top: 30px; color: #666; font-size: 0.9em;'>Report generated on {timestamp}</div>",
                "    </div>",
                js_content,
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(html_parts)
