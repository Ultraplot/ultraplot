document.addEventListener("DOMContentLoaded", function () {
  // Check if current page has opted out of the TOC
  if (document.body.classList.contains("no-right-toc")) {
    return;
  }

  const content = document.querySelector(".rst-content");
  if (!content) return;

  // Find all headers in the main content
  const headers = Array.from(
    content.querySelectorAll("h1:not(.document-title), h2, h3"),
  ).filter((header) => !header.classList.contains("no-toc"));

  // Only create TOC if there are headers
  if (headers.length === 0) return;

  // Create TOC container
  const toc = document.createElement("div");
  toc.className = "right-toc";
  toc.innerHTML =
    '<div class="right-toc-header">' +
    '<div class="right-toc-title">On This Page</div>' +
    '<div class="right-toc-buttons">' +
    '<button class="right-toc-toggle-btn" title="Toggle TOC visibility">−</button>' +
    "</div></div>" +
    '<div class="right-toc-content"><ul class="right-toc-list"></ul></div>';

  const tocList = toc.querySelector(".right-toc-list");
  const tocContent = toc.querySelector(".right-toc-content");
  const tocToggleBtn = toc.querySelector(
    ".right-toc-toggle-btn",
  );

  // Set up the toggle button
  tocToggleBtn.addEventListener("click", function () {
    if (tocContent.style.display === "none") {
      tocContent.style.display = "block";
      tocToggleBtn.textContent = "−";
      toc.classList.remove("right-toc-collapsed");
      localStorage.setItem("tocVisible", "true");
    } else {
      tocContent.style.display = "none";
      tocToggleBtn.textContent = "+";
      toc.classList.add("right-toc-collapsed");
      localStorage.setItem("tocVisible", "false");
    }
  });

  // Check saved state
  if (localStorage.getItem("tocVisible") === "false") {
    tocContent.style.display = "none";
    tocToggleBtn.textContent = "+";
    toc.classList.add("right-toc-collapsed");
  }

  // Track used IDs to avoid duplicates
  const usedIds = new Set();

  // Get all existing IDs in the document
  document.querySelectorAll("[id]").forEach((el) => {
    usedIds.add(el.id);
  });

  // Generate unique IDs for headers that need them
  headers.forEach((header, index) => {
    // If header already has a unique ID, use that
    if (header.id && !usedIds.has(header.id)) {
      usedIds.add(header.id);
      return;
    }

    // Create a slug from the header text
    let headerText = header.textContent || "";

    // Clean the text (remove icons and special characters)
    headerText = headerText.replace(/\s*\uf0c1\s*$/, "");
    headerText = headerText.replace(/\s*[¶§#†‡]\s*$/, "");
    headerText = headerText.trim();

    let slug = headerText
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/--+/g, "-")
      .trim();

    // Make sure slug is not empty
    if (!slug) {
      slug = "section";
    }

    // Ensure the ID is unique
    let uniqueId = slug;
    let counter = 1;

    while (usedIds.has(uniqueId)) {
      uniqueId = `${slug}-${counter}`;
      counter++;
    }

    // Set the unique ID and add to our tracking set
    header.id = uniqueId;
    usedIds.add(uniqueId);
  });

  // Add entries for each header
  headers.forEach((header) => {
    const item = document.createElement("li");
    const link = document.createElement("a");

    link.href = "#" + header.id;

    // Get clean text without icons
    let headerText = header.textContent || "";
    headerText = headerText.replace(/\s*\uf0c1\s*$/, "");
    headerText = headerText.replace(/\s*[¶§#†‡]\s*$/, "");

    link.textContent = headerText.trim();
    link.className =
      "right-toc-link right-toc-level-" +
      header.tagName.toLowerCase();

    item.appendChild(link);
    tocList.appendChild(item);
  });

  // Add TOC to page
  document.body.appendChild(toc);

  // Add active link highlighting
  const tocLinks = document.querySelectorAll(".right-toc-link");
  const headerElements = Array.from(headers);

  if (tocLinks.length > 0 && headerElements.length > 0) {
    // Highlight the current section on scroll
    window.addEventListener(
      "scroll",
      debounce(function () {
        let currentSection = null;
        let smallestDistanceFromTop = Infinity;

        headerElements.forEach((header) => {
          const distance = Math.abs(
            header.getBoundingClientRect().top,
          );
          if (distance < smallestDistanceFromTop) {
            smallestDistanceFromTop = distance;
            currentSection = header.id;
          }
        });

        tocLinks.forEach((link) => {
          link.classList.remove("active");
          if (
            link.getAttribute("href") === `#${currentSection}`
          ) {
            link.classList.add("active");
          }
        });
      }, 100),
    );
  }
});

// Debounce function to limit scroll event firing
function debounce(func, wait) {
  let timeout;
  return function () {
    const context = this;
    const args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}
