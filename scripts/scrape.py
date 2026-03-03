#!/usr/bin/env python3
"""
Scraper for https://www.archerfish.net/
Mirrors all pages and assets into ../squarespace-mirror/
"""

import hashlib
import os
import re
import sys
import time
import mimetypes
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.archerfish.net"
OUTPUT_DIR = Path(__file__).parent.parent / "squarespace-mirror"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
DELAY = 0.5  # seconds between requests

# Squarespace platform/UI asset path prefixes — these are generic chrome we
# don't need to preserve; the site's own CSS/images live elsewhere.
SQSP_PLATFORM_PREFIXES = (
    "/universal/",
    "/website-component-definition/",
)

MAX_COMPONENT_LEN = 200  # macOS HFS+ limit is 255 bytes per component


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalise_url(url: str, base: str = BASE_URL) -> str | None:
    """Resolve relative URL, strip fragment, return None if off-domain."""
    parsed = urlparse(urljoin(base, url))
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc not in ("www.archerfish.net", "archerfish.net"):
        return None
    # Strip fragment and trailing slash normalisation for pages
    clean = urlunparse(parsed._replace(fragment="", query=""))
    return clean


SQSP_ASSET_DOMAINS = (
    "assets.squarespace.com",
    "definitions.sqspcdn.com",
    "static1.squarespace.com",
)


def is_platform_asset(url: str) -> bool:
    """Return True for generic Squarespace UI chrome we don't need to keep."""
    parsed = urlparse(url)
    if parsed.netloc in SQSP_ASSET_DOMAINS:
        for prefix in SQSP_PLATFORM_PREFIXES:
            if parsed.path.startswith(prefix):
                return True
    return False


def _safe_component(name: str) -> str:
    """Shorten a path component that exceeds the filesystem limit."""
    if len(name.encode()) <= MAX_COMPONENT_LEN:
        return name
    ext = Path(name).suffix  # preserve extension e.g. ".css"
    digest = hashlib.md5(name.encode()).hexdigest()[:16]
    return digest + ext


def url_to_local_path(url: str) -> Path:
    """Map a URL to a local file path inside OUTPUT_DIR."""
    parsed = urlparse(url)
    # Include host so CDN assets don't collide with same-named site assets
    host = parsed.netloc.replace(":", "_")
    raw_path = parsed.path.lstrip("/")

    # Shorten any component that would bust the filesystem limit
    parts = raw_path.split("/")
    safe_parts = [_safe_component(p) for p in parts if p]

    path = "/".join(safe_parts) if safe_parts else ""
    full_path = f"{host}/{path}" if path else host

    # Determine page vs asset from the URL *path* only, never the host.
    suffix = Path(path).suffix.lower() if path else ""
    is_page = suffix in ("", ".html", ".htm")

    if is_page:
        if not path:
            return OUTPUT_DIR / host / "index.html"
        if not path.endswith(".html"):
            return OUTPUT_DIR / full_path / "index.html"
        return OUTPUT_DIR / full_path

    return OUTPUT_DIR / full_path


def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def save(path: Path, content: bytes) -> None:
    ensure_dir(path)
    path.write_bytes(content)


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

session = requests.Session()
session.headers.update(HEADERS)


def fetch(url: str) -> requests.Response | None:
    try:
        resp = session.get(url, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except Exception as exc:
        print(f"  [WARN] {url} → {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Asset extraction & download
# ---------------------------------------------------------------------------

def download_asset(url: str, visited_assets: set) -> None:
    if url in visited_assets:
        return
    visited_assets.add(url)

    if is_platform_asset(url):
        return  # skip generic Squarespace UI chrome

    local = url_to_local_path(url)
    if local.exists():
        return

    resp = fetch(url)
    if resp is None:
        return

    save(local, resp.content)
    print(f"  asset  {url}")
    time.sleep(DELAY)

    # If it's a CSS file, extract any url(...) references
    ct = resp.headers.get("content-type", "")
    if "css" in ct:
        process_css_assets(resp.text, url, visited_assets)


def process_css_assets(css_text: str, css_url: str, visited_assets: set) -> None:
    """Find url(...) references inside CSS and download them."""
    for match in re.finditer(r'url\(["\']?([^"\')\s]+)["\']?\)', css_text):
        raw = match.group(1)
        if raw.startswith("data:"):
            continue
        abs_url = urljoin(css_url, raw)
        if abs_url not in visited_assets:
            download_asset(abs_url, visited_assets)


def extract_and_download_assets(soup: BeautifulSoup, page_url: str, visited_assets: set) -> None:
    """Download all CSS, JS, images, and fonts referenced from a page."""
    tags = [
        ("link",   "href",      lambda t: t.get("rel", []) in (["stylesheet"], ["preload"])),
        ("script", "src",       lambda t: True),
        ("img",    "src",       lambda t: True),
        ("img",    "data-src",  lambda t: True),
        ("img",    "srcset",    lambda t: True),
        ("source", "srcset",    lambda t: True),
        ("source", "src",       lambda t: True),
    ]

    for tag_name, attr, condition in tags:
        for tag in soup.find_all(tag_name):
            if not condition(tag):
                continue
            raw = tag.get(attr, "")
            if not raw:
                continue
            # srcset can be "url 2x, url2 3x"
            for part in raw.split(","):
                candidate = part.strip().split()[0]
                if not candidate:
                    continue
                abs_url = urljoin(page_url, candidate)
                download_asset(abs_url, visited_assets)

    # Also pull <style> blocks for url() refs
    for style_tag in soup.find_all("style"):
        if style_tag.string:
            process_css_assets(style_tag.string, page_url, visited_assets)


# ---------------------------------------------------------------------------
# Link extraction
# ---------------------------------------------------------------------------

def extract_page_links(soup: BeautifulSoup, page_url: str) -> list[str]:
    links = []
    for tag in soup.find_all("a", href=True):
        norm = normalise_url(tag["href"], page_url)
        if norm:
            links.append(norm)
    return links


# ---------------------------------------------------------------------------
# Main crawl
# ---------------------------------------------------------------------------

def crawl() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    visited_pages: set[str] = set()
    visited_assets: set[str] = set()
    queue: deque[str] = deque([BASE_URL + "/"])

    print(f"Starting crawl of {BASE_URL}")
    print(f"Output → {OUTPUT_DIR}\n")

    while queue:
        url = queue.popleft()
        norm = normalise_url(url)
        if not norm or norm in visited_pages:
            continue
        visited_pages.add(norm)

        print(f"page   {norm}")
        resp = fetch(norm)
        if resp is None:
            continue

        # Only process HTML pages
        ct = resp.headers.get("content-type", "")
        if "html" not in ct:
            download_asset(norm, visited_assets)
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        local_path = url_to_local_path(norm)
        try:
            save(local_path, resp.content)
        except OSError as exc:
            print(f"  [SKIP] cannot save {local_path}: {exc}", file=sys.stderr)
            continue

        # Download all referenced assets
        try:
            extract_and_download_assets(soup, norm, visited_assets)
        except Exception as exc:
            print(f"  [WARN] asset extraction error on {norm}: {exc}", file=sys.stderr)

        # Enqueue discovered page links
        for link in extract_page_links(soup, norm):
            if link not in visited_pages:
                queue.append(link)

        time.sleep(DELAY)

    print(f"\nDone. {len(visited_pages)} pages, {len(visited_assets)} assets.")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    crawl()
