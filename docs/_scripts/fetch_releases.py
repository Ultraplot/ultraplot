"""
Dynamically build what's new page based on github releases
"""

import requests, re
from pathlib import Path

GITHUB_REPO = "ultraplot/ultraplot"
OUTPUT_RST = Path("whats_new.rst")


GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases"


def format_release_body(text):
    """Formats GitHub release notes for better RST readability."""
    lines = text.strip().split("\n")
    formatted = []

    for line in lines:
        line = line.strip()

        # Convert Markdown ## Headers to RST H2
        if line.startswith("## "):
            title = line[3:].strip()  # Remove "## " from start
            formatted.append(f"{title}\n{'~' * len(title)}\n")  # RST H2 Format
        else:
            formatted.append(line)

    # Convert PR references (remove "by @user in ..." but keep the link)
    formatted_text = "\n".join(formatted)
    formatted_text = re.sub(
        r" by @\w+ in (https://github.com/[^\s]+)", r" (\1)", formatted_text
    )

    return formatted_text.strip()


def fetch_all_releases():
    """Fetches all GitHub releases across multiple pages."""
    releases = []
    page = 1

    while True:
        response = requests.get(GITHUB_API_URL, params={"per_page": 30, "page": page})
        if response.status_code != 200:
            print(f"Error fetching releases: {response.status_code}")
            break

        page_data = response.json()
        # If the page is empty, stop fetching
        if not page_data:
            break

        releases.extend(page_data)
        page += 1

    return releases


def fetch_releases():
    """Fetches the latest releases from GitHub and formats them as RST."""
    releases = fetch_all_releases()
    if not releases:
        print(f"Error fetching releases!")
        return ""

    rst_content = ".. _whats_new:\n\n==========\n\nWhat's new?\n==========\n\n"  # H1

    for release in releases:
        # ensure title is formatted as {tag}: {title}
        tag = release["tag_name"].lower()
        title = release["name"]
        if title.startswith(tag):
            title = title[len(tag) :]
            while title:
                if not title[0].isalpha():
                    title = title[1:]
                    title = title.strip()
                else:
                    title = title.strip()
                    break

        if title:
            title = f"{tag}: {title}"
        else:
            title = tag

        date = release["published_at"][:10]
        body = format_release_body(release["body"] or "")

        # Version header (H2)
        rst_content += f"{title} ({date})\n{'-' * (len(title) + len(date) + 3)}\n\n"

        # Process body content
        rst_content += f"{body}\n\n"

    return rst_content


def write_rst():
    """Writes fetched releases to an RST file."""
    content = fetch_releases()
    if content:
        with open(OUTPUT_RST, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {OUTPUT_RST}")
    else:
        print("No updates to write.")


if __name__ == "__main__":
    write_rst()
