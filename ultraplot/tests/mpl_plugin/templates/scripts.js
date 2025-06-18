// Filter functionality for test results
function filterTests(filterType) {
    const testCases = document.querySelectorAll('.test-case');
    const filterBtns = document.querySelectorAll('.filter-btn');

    // Remove active class from all buttons
    filterBtns.forEach(btn => btn.classList.remove('active'));

    // Add active class to clicked button or find the correct one
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // Find button by filter type for programmatic calls
        const targetBtn = Array.from(filterBtns).find(btn =>
            btn.textContent.toLowerCase().includes(filterType === 'all' ? 'show all' : filterType)
        );
        if (targetBtn) targetBtn.classList.add('active');
    }

    // Filter test cases
    testCases.forEach(testCase => {
        const status = testCase.getAttribute('data-status');
        if (filterType === 'all') {
            testCase.classList.remove('hidden');
        } else if (filterType === 'failed' && status === 'failed') {
            testCase.classList.remove('hidden');
        } else if (filterType === 'passed' && status === 'passed') {
            testCase.classList.remove('hidden');
        } else if (filterType === 'unknown' && status === 'unknown') {
            testCase.classList.remove('hidden');
        } else {
            testCase.classList.add('hidden');
        }
    });

    // Update URL hash for bookmarking
    history.replaceState(null, null, `#filter-${filterType}`);
}

// Image zoom functionality
function setupImageZoom() {
    const images = document.querySelectorAll('.image-column img');

    images.forEach(img => {
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', function() {
            if (this.classList.contains('zoomed')) {
                // Zoom out
                this.classList.remove('zoomed');
                this.style.position = '';
                this.style.top = '';
                this.style.left = '';
                this.style.width = '';
                this.style.height = '';
                this.style.zIndex = '';
                this.style.cursor = 'zoom-in';
                document.body.style.overflow = '';

                // Remove backdrop
                const backdrop = document.querySelector('.image-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
            } else {
                // Zoom in
                this.classList.add('zoomed');

                // Create backdrop
                const backdrop = document.createElement('div');
                backdrop.className = 'image-backdrop';
                backdrop.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    z-index: 9998;
                    cursor: zoom-out;
                `;

                backdrop.addEventListener('click', () => {
                    this.click(); // Trigger zoom out
                });

                document.body.appendChild(backdrop);

                // Style the image
                this.style.position = 'fixed';
                this.style.top = '50%';
                this.style.left = '50%';
                this.style.transform = 'translate(-50%, -50%)';
                this.style.maxWidth = '90vw';
                this.style.maxHeight = '90vh';
                this.style.width = 'auto';
                this.style.height = 'auto';
                this.style.zIndex = '9999';
                this.style.cursor = 'zoom-out';
                document.body.style.overflow = 'hidden';
            }
        });
    });
}

// Keyboard navigation
function setupKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        switch(e.key) {
            case '1':
                filterTests('all');
                break;
            case '2':
                filterTests('failed');
                break;
            case '3':
                filterTests('passed');
                break;
            case '4':
                filterTests('unknown');
                break;
            case 'Escape':
                // Close any zoomed images
                const zoomedImage = document.querySelector('.image-column img.zoomed');
                if (zoomedImage) {
                    zoomedImage.click();
                }
                break;
        }
    });
}

// Search functionality
function setupSearch() {
    // Create search input if it doesn't exist
    const filterControls = document.querySelector('.filter-controls');
    if (filterControls && !document.querySelector('#test-search')) {
        const searchInput = document.createElement('input');
        searchInput.id = 'test-search';
        searchInput.type = 'text';
        searchInput.placeholder = 'Search test names...';
        searchInput.style.cssText = `
            padding: 10px 15px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            margin-left: auto;
            max-width: 300px;
            font-size: 14px;
        `;

        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const testCases = document.querySelectorAll('.test-case');

            testCases.forEach(testCase => {
                const testName = testCase.querySelector('.test-name').textContent.toLowerCase();
                const matchesSearch = testName.includes(searchTerm);

                if (matchesSearch) {
                    testCase.classList.remove('search-hidden');
                } else {
                    testCase.classList.add('search-hidden');
                }
            });
        });

        filterControls.appendChild(searchInput);

        // Add CSS for search-hidden
        const style = document.createElement('style');
        style.textContent = '.test-case.search-hidden { display: none !important; }';
        document.head.appendChild(style);
    }
}

// Initialize page with 'failed' filter on load and restore from URL hash
function initializePage() {
    // Check URL hash for filter preference
    const hash = window.location.hash;
    let initialFilter = 'failed'; // Default to failed

    if (hash.startsWith('#filter-')) {
        const filterType = hash.replace('#filter-', '');
        if (['all', 'failed', 'passed', 'unknown'].includes(filterType)) {
            initialFilter = filterType;
        }
    }

    filterTests(initialFilter);
}

// Setup smooth scrolling for internal links
function setupSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupImageZoom();
    setupKeyboardNavigation();
    setupSearch();
    setupSmoothScrolling();

    // Add keyboard shortcuts info
    const container = document.querySelector('.container');
    if (container) {
        const helpText = document.createElement('div');
        helpText.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            opacity: 0.7;
            z-index: 1000;
        `;
        helpText.innerHTML = `
            <strong>Keyboard shortcuts:</strong><br>
            1: Show All | 2: Failed Only | 3: Passed Only | 4: Unknown<br>
            ESC: Close zoomed image | Click images to zoom
        `;
        document.body.appendChild(helpText);

        // Hide help after 10 seconds
        setTimeout(() => {
            helpText.style.opacity = '0';
            setTimeout(() => helpText.remove(), 1000);
        }, 10000);
    }
});
