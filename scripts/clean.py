#!/usr/bin/env python3
"""
Phase 2 & 3: Clean Squarespace cruft from scraped HTML, rewrite assets to
local paths, replace Typekit fonts with Google Fonts, and output a clean
static site into ../site/.

Font replacements:
  proxima-nova       → Montserrat
  adobe-garamond-pro → EB Garamond
"""

import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup, Comment

MIRROR  = Path(__file__).parent.parent / "squarespace-mirror"
SITE    = Path(__file__).parent.parent / "site"
ASSETS  = SITE / "assets"

PAGES_DIR = MIRROR / "www.archerfish.net"
CSS_SRC   = (
    MIRROR
    / "static1.squarespace.com"
    / "static"
    / "sitecss"
    / "5324f255e4b0137cd27d9683"
    / "116"
    / "515c7bd0e4b054dae3fcf003"
    / "532e270be4b0ff70f47a8bd6"
    / "2788"
    / "site.css"
)
IMAGES_SRC = MIRROR / "images.squarespace-cdn.com" / "content" / "v1" / "5324f255e4b0137cd27d9683"

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Montserrat:ital,wght@0,100;0,300;0,400;0,600;0,700;0,800;0,900;"
    "1,100;1,300;1,400;1,600;1,700;1,800;1,900"
    "&family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600;1,700"
    "&display=swap"
)

# ---------------------------------------------------------------------------
# Squarespace domains / patterns to strip
# ---------------------------------------------------------------------------

SQSP_SCRIPT_DOMAINS = (
    "squarespace.com",
    "sqspcdn.com",
    "typekit.net",
    "googletagmanager.com",
    "google-analytics.com",
)

SQSP_LINK_DOMAINS = (
    "squarespace.com",
    "sqspcdn.com",
    "typekit.net",
    "p.typekit.net",
)

# Inline script patterns that are Squarespace platform code
SQSP_INLINE_PATTERNS = (
    "Squarespace",
    "SQUARESPACE_ROLLUPS",
    "Static.SQUARESPACE_CONTEXT",
    "Static.COOKIE_BANNER",
    "window.Typekit",
    "Typekit.load",
    "squarespace.com",
    "sqspcdn.com",
    "gtag(",
    "GoogleAnalyticsObject",
    "fbq(",
)


# ---------------------------------------------------------------------------
# Build image URL → local filename mapping
# ---------------------------------------------------------------------------

def build_image_map() -> dict[str, Path]:
    """
    Map every CDN image URL path (no query) → local file in assets/images/.
    Images with generic names (image-asset.*) get renamed by their timestamp hash.
    Returns {cdn_path_no_query: dest_path_in_assets_images}.
    """
    mapping: dict[str, Path] = {}  # cdn path (no query) → local dest
    (ASSETS / "images").mkdir(parents=True, exist_ok=True)

    for src_file in sorted(IMAGES_SRC.rglob("*")):
        if not src_file.is_file():
            continue
        # Reconstruct the CDN URL path for this file
        # src_file is something like IMAGES_SRC/1479714439194-.../archerfishApproach.jpg
        parts = src_file.relative_to(MIRROR / "images.squarespace-cdn.com")
        cdn_path = "/" + str(parts)

        # Decide on a clean local name
        stem = src_file.stem
        suffix = src_file.suffix

        # For files saved as index.html (no extension in original name), strip
        if suffix == ".html" and stem == "index":
            # parent dir name is the original filename (no ext)
            stem = src_file.parent.name
            suffix = ""

        # If generic name, prefix with the timestamp-hash directory name
        if stem == "image-asset":
            hash_dir = src_file.parent.name
            stem = hash_dir + "_image-asset"

        local_name = stem + suffix
        dest = ASSETS / "images" / local_name

        shutil.copy2(src_file, dest)
        mapping[cdn_path] = dest
        print(f"  image  {local_name}")

    return mapping


def cdn_url_to_local(url: str, image_map: dict[str, Path], page_depth: int) -> str | None:
    """
    Given a CDN image URL (may have query params), return a relative path
    from a page at the given depth to the local image file.
    Returns None if the image isn't in our map.
    """
    parsed = urlparse(url)
    if parsed.netloc not in ("images.squarespace-cdn.com", "static1.squarespace.com"):
        return None

    # Strip query for lookup
    path_no_q = parsed.path
    if path_no_q in image_map:
        local = image_map[path_no_q]
    else:
        # Try prefix match (data-src URLs are sometimes truncated in scrape)
        matches = [v for k, v in image_map.items() if path_no_q.startswith(k) or k.startswith(path_no_q)]
        if not matches:
            return None
        local = matches[0]

    # Relative path from page to assets/images/
    prefix = "../" * page_depth
    return f"{prefix}assets/images/{local.name}"


# ---------------------------------------------------------------------------
# CSS cleaning
# ---------------------------------------------------------------------------

def clean_css(css_text: str) -> str:
    """Replace Typekit font families and remove Squarespace UI font junk."""
    # Font family substitutions (various quoting styles in CSS)
    subs = [
        (r"['\"]?proxima-nova['\"]?", '"Montserrat"'),
        (r"['\"]?proxima nova['\"]?",  '"Montserrat"'),
        (r"['\"]?adobe-garamond-pro['\"]?", '"EB Garamond"'),
        (r"['\"]?adobe garamond pro['\"]?",  '"EB Garamond"'),
    ]
    for pattern, replacement in subs:
        css_text = re.sub(pattern, replacement, css_text, flags=re.IGNORECASE)

    # Remove the entire @font-face block for squarespace-ui-font
    css_text = re.sub(
        r"@font-face\s*\{[^}]*squarespace-ui-font[^}]*\}",
        "",
        css_text,
        flags=re.IGNORECASE,
    )

    # Remove Squarespace CDN references to UI icons
    css_text = re.sub(
        r"url\(['\"]?https?://assets\.squarespace\.com/universal/fonts/[^)]*['\"]?\)",
        'url("")',
        css_text,
    )

    return css_text


# ---------------------------------------------------------------------------
# HTML cleaning
# ---------------------------------------------------------------------------

def is_sqsp_url(url: str) -> bool:
    if not url:
        return False
    # Handle protocol-relative URLs like //assets.squarespace.com/...
    if url.startswith("//"):
        url = "https:" + url
    netloc = urlparse(url).netloc or ""
    return any(d in netloc for d in SQSP_SCRIPT_DOMAINS)


def has_sqsp_inline(text: str) -> bool:
    return any(p in text for p in SQSP_INLINE_PATTERNS)


def clean_html(html_bytes: bytes, image_map: dict[str, Path], page_depth: int) -> str:
    soup = BeautifulSoup(html_bytes, "lxml")

    # --- Remove HTML comments ---
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # --- Remove <script> tags ---
    for tag in soup.find_all("script"):
        src = tag.get("src", "")
        # External Squarespace / GTM / Typekit scripts
        if src and is_sqsp_url(src):
            tag.decompose()
            continue
        # Inline scripts containing Squarespace platform code
        if not src and tag.string and has_sqsp_inline(tag.string):
            tag.decompose()
            continue
        # All-whitespace / empty inline scripts
        if not src and (not tag.string or not tag.string.strip()):
            tag.decompose()

    # --- Remove Squarespace <link> tags ---
    for tag in soup.find_all("link"):
        href = tag.get("href", "")
        if href.startswith("//"):
            href = "https:" + href
        rel = tag.get("rel", [])

        sqsp_href = any(d in href for d in SQSP_LINK_DOMAINS + ("squarespace-cdn.com",))

        # preconnect / dns-prefetch to Squarespace/Typekit
        if rel and rel[0] in ("preconnect", "dns-prefetch") and sqsp_href:
            tag.decompose()
            continue

        # Squarespace CDN stylesheets
        if "stylesheet" in rel and sqsp_href:
            tag.decompose()
            continue

        # Favicon pointing to CDN
        if "icon" in rel and sqsp_href:
            tag.decompose()
            continue

        # image_src meta-link pointing to CDN
        if "image_src" in rel and sqsp_href:
            tag.decompose()
            continue

        # Alternate feed URL (Squarespace RSS)
        if "alternate" in rel and "squarespace" in href:
            tag.decompose()

    # --- Remove Squarespace <meta> noise ---
    for tag in soup.find_all("meta"):
        name = tag.get("name", "") or ""
        content = tag.get("content", "") or ""
        prop = tag.get("property", "") or ""
        # Generator tag
        if "squarespace" in name.lower() or "squarespace" in content.lower():
            tag.decompose()
            continue
        # Open Graph image pointing to Squarespace CDN — we'll leave OG tags intact
        # but strip the Squarespace-specific ones
        if prop == "og:image" and "squarespace" in content.lower():
            tag.decompose()

    # --- Rewrite site CSS <link> to local ---
    for tag in soup.find_all("link", rel=["stylesheet"]):
        href = tag.get("href", "")
        if "static1.squarespace.com" in href and "site.css" in href:
            prefix = "../" * page_depth
            tag["href"] = f"{prefix}assets/css/site.css"

    # --- Inject Google Fonts ---
    head = soup.find("head")
    if head:
        # Remove any existing Google Fonts links first
        for tag in head.find_all("link", href=re.compile(r"fonts\.googleapis\.com")):
            tag.decompose()

        gf_preconnect1 = soup.new_tag("link", rel="preconnect", href="https://fonts.googleapis.com")
        gf_preconnect2 = soup.new_tag("link", rel="preconnect", href="https://fonts.gstatic.com", crossorigin="")
        gf_link = soup.new_tag("link", rel="stylesheet", href=GOOGLE_FONTS_URL)

        # Insert right after <meta charset> or at the start of <head>
        first = head.find("meta") or head.contents[0]
        first.insert_after(gf_link)
        first.insert_after(gf_preconnect2)
        first.insert_after(gf_preconnect1)

    # --- Rewrite image src / data-src / data-image; clean srcset ---
    for img in soup.find_all("img"):
        # Resolve src / data-src to local paths
        for attr in ("src", "data-src"):
            url = img.get(attr, "")
            if not url:
                continue
            if url.startswith("//"):
                url = "https:" + url
            local = cdn_url_to_local(url, image_map, page_depth)
            if local:
                img[attr] = local
                # Promote lazy-load data-src → src
                if attr == "data-src" and not img.get("src"):
                    img["src"] = local
                    del img["data-src"]

        # Strip Squarespace data-image / data-image-dimensions / data-loader attrs
        for attr in list(img.attrs):
            if attr.startswith("data-image") or attr in ("data-loader", "data-load", "data-stretch"):
                del img[attr]

        # Rewrite or remove srcset (CDN URLs won't work; use single src instead)
        if img.get("srcset"):
            del img["srcset"]
        if img.get("sizes"):
            del img["sizes"]

    # --- Remove JSON-LD scripts containing Squarespace URLs ---
    for tag in soup.find_all("script", type="application/ld+json"):
        if tag.string and "squarespace" in tag.string.lower():
            tag.decompose()

    # --- Remove Squarespace social buttons and comment widgets (non-functional statically) ---
    for tag in soup.find_all(class_=re.compile(r"squarespace-social-buttons|squarespace-comments", re.I)):
        tag.decompose()

    # --- Strip residual Squarespace data-* attributes from any tag ---
    SQSP_DATA_ATTRS = {
        "data-asset-url", "data-full-url", "data-record-type",
        "data-system-data-id", "data-title", "data-load", "data-loader",
        "data-image-focal-point", "data-image-dimensions",
    }
    for tag in soup.find_all(True):
        for attr in SQSP_DATA_ATTRS & set(tag.attrs):
            del tag[attr]

    # --- Remove cookie consent / GDPR banners ---
    for tag in soup.find_all(id=re.compile(r"cookie|gdpr|consent", re.I)):
        tag.decompose()
    for tag in soup.find_all(class_=re.compile(r"cookie|gdpr|consent", re.I)):
        tag.decompose()

    # --- Fix canonical and other absolute internal links ---
    for tag in soup.find_all("link", rel=["canonical"]):
        href = tag.get("href", "")
        if "archerfish.net" in href:
            tag["href"] = href.replace("http://", "https://")

    return str(soup)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Output → {SITE}\n")

    # Wipe and recreate output dir
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (ASSETS / "css").mkdir(parents=True)
    (ASSETS / "js").mkdir(parents=True)
    (ASSETS / "images").mkdir(parents=True)

    # 1. Copy and clean site CSS
    print("Cleaning CSS...")
    if CSS_SRC.exists():
        css_text = CSS_SRC.read_text(encoding="utf-8", errors="replace")
        css_text = clean_css(css_text)
        (ASSETS / "css" / "site.css").write_text(css_text, encoding="utf-8")
        print(f"  css    assets/css/site.css")
    else:
        print("  [WARN] site.css not found in mirror")

    # 2. Copy images and build URL map
    print("\nCopying images...")
    image_map = build_image_map()

    # 3. Process HTML pages
    print("\nCleaning HTML pages...")
    for html_file in sorted(PAGES_DIR.rglob("index.html")):
        rel = html_file.relative_to(PAGES_DIR)
        # page_depth: how many dirs deep from site root
        # e.g. index.html → 0, analysis/index.html → 1
        depth = len(rel.parts) - 1

        dest = SITE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        html_bytes = html_file.read_bytes()
        cleaned = clean_html(html_bytes, image_map, depth)
        dest.write_text(cleaned, encoding="utf-8")
        print(f"  page   {rel}")

    # 4. Write CNAME
    (SITE / "CNAME").write_text("www.archerfish.net\n")
    print("\n  wrote  CNAME")

    # 5. Summary
    pages  = list(SITE.rglob("*.html"))
    images = list((ASSETS / "images").iterdir())
    print(f"\nDone. {len(pages)} HTML pages, {len(images)} images.")
    print(f"Output: {SITE}")


if __name__ == "__main__":
    main()
