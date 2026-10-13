# Zeberox

My personal corner of the internet for writing about offensive security.

I'm an IT student who got into cybersecurity at 17. This site is where I keep the
writeups: CTF challenges I solved, lab machines I rooted, and the occasional bug
or misconfiguration I stumbled into and found worth explaining. Each post walks
through the whole path — recon, the thing that looked wrong, why it was
exploitable, and how it was turned into access.

I write these mostly for myself. Explaining an exploit end to end is the fastest
way I've found to be sure I actually understood it, rather than just having
copied a payload that happened to work. If they're useful to someone else
learning the same things, even better.

Live at **[zeberox.github.io](https://zeberox.github.io)**.

---

## How it's built

A static site generator written for this site specifically — around 1,600 lines
of Python, CSS and JavaScript, with **zero dependencies**. Every import is from
the standard library: no `pip install`, no `npm`, no lockfile.

Posts are plain Markdown in `posts/`. A hand-written renderer
(`src/mdrender.py`, 193 lines) turns them into HTML — headings with anchors,
code blocks with copy buttons, a table of contents — and `scripts/build.py`
assembles the pages, `posts.json`, an RSS feed, a sitemap and a 404 page into
`dist/`.

Every page is fully pre-rendered, so the site works with JavaScript disabled and
search engines and link previews get real `<title>` and Open Graph tags. The
JavaScript on top is progressive enhancement only: live search, category
filtering, and an EN/VI switch that swaps the interface *and* the post bodies.

The home page is 8 KB; all CSS and JS together are 28 KB. GitHub Actions builds
and deploys the site on every push to `main`.

### On authorship

Most of the code in this repository was written by AI. I decided what the site
should do, how it should look and behave, and adjusted things as it came
together — but I did not write the bulk of it by hand, and it would be dishonest
to present it as if I had.

The writeups are a different matter. The research, the exploitation and the
understanding behind every post are mine. English isn't my first language, so I
sometimes have AI rephrase an explanation I've already worked out, so it reads
clearly for everyone. The work is mine; only some of the wording isn't.

---

## Running it locally

```bash
python3 scripts/dev.py
```

Open <http://localhost:8000>. Edit anything in `posts/`, `src/` or `assets/` and
the page reloads itself. To build into `dist/` without a server:
`python3 scripts/build.py`.

## Adding a post

Create a file in `posts/` — the filename becomes the URL, so `posts/my-box.md`
is served at `/writeups/my-box/`. Start it with frontmatter:

```markdown
---
title: My first box
date: 2026-10-13
category: HTB
summary: One or two sentences for the card and the link preview.
featured: false
tags: [sqli, recon]
---

## Recon
The rest is ordinary Markdown.
```

`summary` falls back to the first paragraph, `featured: true` pins the post to
the home page, and `draft: true` keeps it out of the build.

A Vietnamese translation goes in `posts/<slug>.vi.md` and only needs `title`,
`summary` and the body — the dates and categories come from the default-language
file. Where no translation exists, the EN version is shown.

Everything personal — name, links, categories and their colours, certifications,
the About and Certifications copy — lives in [`src/config.py`](src/config.py).

## Project layout

```
posts/        your posts (.md) — the part you actually touch
src/
  config.py   site config (name, links, categories, section copy, i18n)
  mdrender.py Markdown -> HTML, no dependencies
  templates.py page templates
assets/       style.css + app.js, copied into the site as-is
static/       files deployed verbatim to the site root (favicon, images, CNAME…)
scripts/      build.py (generator), dev.py (live preview), serve.py (server)
dist/         generator OUTPUT — not committed, rewritten on every build
```

## Deploying

The repository is named `zeberox.github.io`, so GitHub Pages serves it at the
domain root. One-time setup: **Settings → Pages → Build and deployment →
Source: `GitHub Actions`**. After that, pushing to `main` is the whole deploy.

For a custom domain, put the domain in `static/CNAME`, set `base = "/"` and
`siteUrl = "https://your-domain"` in `src/config.py`, and add the domain under
Settings → Pages.
