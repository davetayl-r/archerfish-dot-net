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
wget \
  --mirror \
  --convert-links \
  --adjust-extension \
  --page-requisites \
  --no-parent \
  --directory-prefix=./squarespace-mirror \
  https://www.archerfish.net/
```

### Serve locally

```bash
source .venv/bin/activate
python3 -m http.server 8000      # open http://localhost:8000
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

The final output is a plain static site (no build step, no framework). Structure:

```
/
├── index.html
├── about/index.html
├── [other pages]/index.html
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
└── CNAME                        ← contains "www.archerfish.net"
```

The scrape lands in `./squarespace-mirror/` and is cleaned/restructured into the root before deployment. The site must work from `file://` (no server dependency).

## Migration workflow

1. **Scrape** → `squarespace-mirror/` via wget
2. **Audit** — strip Squarespace scripts, CDN refs, cookie banners, proprietary meta tags; replace any Squarespace-CDN fonts with Google Fonts or self-hosted equivalents
3. **Restructure** — move files into the target layout above; consolidate CSS; make all links relative
4. **Test** — local server + spider check + manual visual review (pages, images, nav, fonts, mobile)
5. **Deploy** — push to `main`, enable GitHub Pages, add `CNAME`, enforce HTTPS

## Key constraints

- Replace any Squarespace JS (galleries, forms) with vanilla JS equivalents
- Contact forms → Formspree (https://formspree.io); Squarespace backend won't work statically
- No Squarespace licence keys, API tokens, or proprietary platform code in output
- Faithfulness to the original design is the priority (layout, typography, spacing, colours)
- If a page fails to scrape, fetch manually with `curl` and reconstruct
