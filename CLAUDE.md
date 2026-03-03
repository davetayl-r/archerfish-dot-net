# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Migrate **https://www.archerfish.net/** from Squarespace to a static site deployed on GitHub Pages at `dtay0016/archerfish-dot-net`. All content and images are copyright of the site owner.

Custom domain: `www.archerfish.net`

## Commands

### Python environment

```bash
source .venv/bin/activate        # activate venv
pip install -r requirements.txt  # restore dependencies
pip freeze > requirements.txt    # update after adding packages
```

### Scrape the live site

```bash
source .venv/bin/activate
python scripts/scrape.py         # crawls archerfish.net → squarespace-mirror/
```

### Clean and restructure

```bash
source .venv/bin/activate
python scripts/clean.py          # strips Squarespace cruft → site/
```

### Serve locally

```bash
cd site && python3 -m http.server 8000   # open http://localhost:8000
```

### Check for broken links

```bash
wget --spider -r -nd -nv http://localhost:8000 2>&1 | grep -i 'broken\|404\|error'
```

### R environment

```bash
R -e "renv::restore()"   # restore R packages from renv.lock
R -e "renv::snapshot()"  # update renv.lock after adding packages
```

## Architecture

Two-stage pipeline: scrape → clean. No build step, no framework.

```
scripts/
├── scrape.py          # crawls archerfish.net, saves raw mirror to squarespace-mirror/
└── clean.py           # strips Squarespace cruft, localises assets, outputs to site/

squarespace-mirror/    # raw scrape output (not deployed)
├── www.archerfish.net/
│   └── [pages as index.html files]
└── images.squarespace-cdn.com/
    └── [content images]

site/                  # clean static site (deploy this)
├── index.html
├── analysis/index.html
├── insights/index.html
├── insights/[article-slug]/index.html
├── assets/
│   ├── css/site.css
│   └── images/        (42 images, all local)
└── CNAME              ← "www.archerfish.net"
```

### scrape.py

- Crawls `https://www.archerfish.net/` and all internal links
- Downloads HTML pages, CSS, JS, images (including `data-src` lazy-load attributes)
- Skips generic Squarespace platform assets (`/universal/`, `/website-component-definition/` paths)
- Hashes path components exceeding macOS's 255-byte filename limit
- Output goes to `squarespace-mirror/` organised by host

### clean.py

- Removes all Squarespace/Typekit/GTM scripts (including protocol-relative `//` URLs)
- Removes Squarespace `<link>` tags: preconnect, stylesheets, favicon, RSS alternate, image_src
- Removes Squarespace comment widgets and social sharing buttons
- Removes JSON-LD blobs containing Squarespace URLs
- Strips residual Squarespace `data-*` attributes
- Replaces Typekit with Google Fonts: **Montserrat** (was Proxima Nova) and **EB Garamond** (was Adobe Garamond Pro)
- Rewrites all CDN image URLs to local `assets/images/` paths
- Promotes lazy-load `data-src` → `src`, removes `srcset` (CDN-dependent)
- Rewrites site CSS link to `assets/css/site.css`
- In the CSS: substitutes font-family names and removes `@font-face` for `squarespace-ui-font`

## Pages (7 total)

- `/` — Homepage
- `/analysis` — Analysis services page
- `/insights` — Blog index
- `/insights/why-social-return-on-investment-should-be-avoided`
- `/insights/how-can-cba-prioritise-social-policy-spending`
- `/insights/where-can-we-remember-them`
- `/insights/what-can-we-learn-from-baseball`

## Remaining work

- Phase 4: Visual review at `http://localhost:8000` — check layout, images, fonts, mobile
- Phase 5: Replace Squarespace JS galleries with vanilla JS (slideshow on homepage is currently static)
- Phase 5: Add Formspree contact form (Squarespace form backend is gone)
- Phase 6: Git init, push to `dtay0016/archerfish-dot-net`, enable GitHub Pages, enforce HTTPS

## Key constraints

- Faithfulness to the original design is the priority (layout, typography, spacing, colours)
- Contact forms → Formspree (https://formspree.io)
- No Squarespace licence keys, API tokens, or proprietary platform code in output
