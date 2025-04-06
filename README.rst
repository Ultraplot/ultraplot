.. image:: https://raw.githubusercontent.com/Ultraplot/ultraplot/refs/heads/main/UltraPlotLogo.svg
    :alt: UltraPlot Logo
    :width: 100%

|build-status| |coverage| |docs| |pypi| |code-style| |pre-commit| |pr-welcome| |license|

A succinct `matplotlib <https://matplotlib.org/>`__ wrapper for making beautiful,
publication-quality graphics. It builds upon ProPlot_ and transports it into the modern age (supporting mpl 3.9.0+).

.. _ProPlot: https://github.com/proplot-dev/

Why UltraPlot? | Write Less, Create More
=========================================
.. image:: https://raw.githubusercontent.com/Ultraplot/ultraplot/refs/heads/main/logo/whyUltraPlot.svg
    :width: 100%
    :alt: Comparison of ProPlot and UltraPlot
    :align: center

Checkout our examples
=====================

Below is a gallery showing random examples of what UltraPlot can do, refresh the example to show more:

.. raw:: html

    <div id="ultraplot-gallery-container" style="margin: 20px 0;">
        <div id="ultraplot-gallery" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px;">
            <p id="loading-message" style="grid-column: 1/-1; text-align: center;">Loading gallery...</p>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <button id="refresh-gallery-btn" style="padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; display: none;">
                Show Different Examples
            </button>
        </div>
    </div>

    <script>
        (function() {
            const galleryElement = document.getElementById('ultraplot-gallery');
            const loadingElement = document.getElementById('loading-message');
            const refreshButton = document.getElementById('refresh-gallery-btn');

            // Base URLs of the documentation
            const baseUrl = 'https://ultraplot.readthedocs.io/en/latest/';
            const pagesToCheck = [
                'https://ultraplot.readthedocs.io/en/latest/index.html',
                'https://ultraplot.readthedocs.io/en/latest/basics.html',
                'https://ultraplot.readthedocs.io/en/latest/cartesian.html',
                'https://ultraplot.readthedocs.io/en/latest/projections.html',
                'https://ultraplot.readthedocs.io/en/latest/stats.html',
            ];

            // Store collected image URLs
            let allImageUrls = [];
            let pagesChecked = 0;
            const numImagesToShow = 6; // Number of images to display

            // Fetch HTML content from a URL and extract image sources
            async function extractImagesFromPage(url) {
                try {
                    const response = await fetch(url);
                    const html = await response.text();

                    // Create a DOM parser
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    // Find all image elements
                    const images = doc.querySelectorAll('img');
                    let pageImages = [];

                    // Extract image sources
                    images.forEach(img => {
                        let src = img.getAttribute('src');
                        if (src) {
                            // Handle relative URLs
                            if (src.startsWith('/') || !src.startsWith('http')) {
                                src = new URL(src, url).href;
                            }

                            // Filter out icons, logos, etc.
                            if (!src.includes('logo') && !src.includes('icon') &&
                                (src.includes('_images/') || src.includes('_static/'))) {
                                pageImages.push(src);
                            }
                        }
                    });

                    return pageImages;
                } catch (error) {
                    console.error(`Error fetching ${url}:`, error);
                    return [];
                }
            }

            // Create gallery once images are collected
            function createGallery() {
                if (pagesChecked < pagesToCheck.length) {
                    return; // Wait until all pages are checked
                }

                if (allImageUrls.length === 0) {
                    galleryElement.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No images found. Please check the connection to the documentation site.</p>';
                    return;
                }

                // Filter for unique URLs
                allImageUrls = [...new Set(allImageUrls)];

                // Display the refresh button
                refreshButton.style.display = 'inline-block';
                refreshButton.onclick = refreshGallery;

                // Create the initial gallery
                refreshGallery();
            }

            // Refresh the gallery with new random images
            function refreshGallery() {
                // Clear the gallery
                galleryElement.innerHTML = '';

                // Get random images
                const count = Math.min(numImagesToShow, allImageUrls.length);
                const randomImages = getRandomImages(allImageUrls, count);

                // Create grid items for each image
                randomImages.forEach(imageUrl => {
                    const gridItem = createGridItem(imageUrl);
                    galleryElement.appendChild(gridItem);
                });
            }

            // Create a grid item for an image
            function createGridItem(imageUrl) {
                const imgContainer = document.createElement('div');
                imgContainer.className = 'gallery-item';
                imgContainer.style.background = 'white';
                imgContainer.style.padding = '15px';
                imgContainer.style.borderRadius = '8px';
                imgContainer.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                imgContainer.style.display = 'flex';
                imgContainer.style.flexDirection = 'column';
                imgContainer.style.height = '100%';

                const imgWrapper = document.createElement('div');
                imgWrapper.style.flex = '1';
                imgWrapper.style.display = 'flex';
                imgWrapper.style.alignItems = 'center';
                imgWrapper.style.justifyContent = 'center';
                imgWrapper.style.overflow = 'hidden';
                imgWrapper.style.marginBottom = '10px';

                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = 'UltraPlot Example';
                img.style.maxWidth = '100%';
                img.style.maxHeight = '200px'; // Consistent height
                img.style.objectFit = 'contain';
                img.style.display = 'block';

                // Handle load errors
                img.onerror = () => {
                    img.src = 'https://via.placeholder.com/200x150?text=Image+Not+Available';
                    img.alt = 'Image Not Available';
                };

                // Extract filename for caption
                const filename = imageUrl.split('/').pop();

                const caption = document.createElement('div');
                caption.style.fontSize = '12px';
                caption.style.textAlign = 'center';
                caption.style.color = '#666';
                caption.style.marginTop = 'auto';
                caption.style.wordBreak = 'break-word';

                imgWrapper.appendChild(img);
                imgContainer.appendChild(imgWrapper);
                imgContainer.appendChild(caption);

                // Make the grid item clickable to open the image in a new tab
                imgContainer.style.cursor = 'pointer';
                imgContainer.onclick = () => window.open(imageUrl, '_blank');

                return imgContainer;
            }

            // Get a random subset of images
            function getRandomImages(images, count) {
                const shuffled = [...images].sort(() => 0.5 - Math.random());
                return shuffled.slice(0, count);
            }

            // Fetch images from each documentation page
            pagesToCheck.forEach(pageUrl => {
                extractImagesFromPage(pageUrl).then(images => {
                    allImageUrls = allImageUrls.concat(images);
                    pagesChecked++;
                    createGallery();
                });
            });

            // Fallback in case fetching fails
            setTimeout(() => {
                if (pagesChecked < pagesToCheck.length) {
                    pagesChecked = pagesToCheck.length; // Force update
                    createGallery();
                }
            }, 5000);
        })();
    </script>

Documentation
=============

The documentation is `published on readthedocs <https://ultraplot.readthedocs.io>`__.

Installation
============

UltraPlot is published on `PyPi <https://pypi.org/project/ultraplot/>`__ and
`conda-forge <https://conda-forge.org>`__. It can be installed with ``pip`` or
``conda`` as follows:

.. code-block:: bash

   pip install ultraplot
   conda install -c conda-forge ultraplot

Likewise, an existing installation of UltraPlot can be upgraded
to the latest version with:

.. code-block:: bash

   pip install --upgrade ultraplot
   conda upgrade ultraplot

To install a development version of UltraPlot, you can use
``pip install git+https://github.com/ultraplot/ultraplot.git``
or clone the repository and run ``pip install -e .``
inside the ``ultraplot`` folder.


.. |build-status| image::  https://github.com/ultraplot/ultraplot/actions/workflows/build-ultraplot.yml/badge.svg

.. |code-style| image:: https://img.shields.io/badge/code%20style-black-000000.svg

.. |pr-welcome| image:: https://img.shields.io/badge/PRs-welcome-brightgreen

.. |docs| image:: https://readthedocs.org/projects/ultraplot/badge/?version=latest
   :alt: docs
   :target: https://ultraplot.readthedocs.io/en/latest/?badge=latest

.. |pypi| image:: https://img.shields.io/pypi/v/ultraplot?color=83%20197%2052
   :alt: pypi
   :target: https://pypi.org/project/ultraplot/

.. |license| image:: https://img.shields.io/github/license/ultraplot/ultraplot.svg
   :alt: license
   :target: LICENSE.txt

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/Ultraplot/ultraplot/main.svg
   :target: https://results.pre-commit.ci/latest/github/Ultraplot/ultraplot/main
   :alt: pre-commit.ci status

.. |coverage| image:: https://codecov.io/gh/Ultraplot/ultraplot/graph/badge.svg?token=C6ZB7Q9II4
   :target: https://codecov.io/gh/Ultraplot/ultraplot
   :alt: coverage
