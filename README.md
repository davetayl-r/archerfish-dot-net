# Archerfish website

Source for [www.archerfish.net](https://www.archerfish.net) — a static site built with Hugo and deployed to GitHub Pages.

## Stack

- **Framework:** [Hugo](https://gohugo.io/) with the [Hugo Hero theme](https://github.com/zerostaticthemes/hugo-hero-theme)
- **Hosting:** GitHub Pages 
- **Deploy:** GitHub Actions — push to `main` triggers an automatic build and deploy

## Local development

Requires Hugo extended v0.92.0+.

```bash
hugo server        # serve at http://localhost:1313 with live reload
hugo --minify      # build to public/
```

## Structure

```
content/           # Markdown content (pages and insights/blog posts)
layouts/           # Template overrides (partials, page types)
static/            # Assets served at root (images, favicon)
assets/            # SCSS and JS processed by Hugo pipes
themes/            # Hugo Hero theme (inlined)
hugo.toml          # Site configuration
.github/workflows/ # CI/CD deploy pipeline
```