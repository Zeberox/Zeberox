#!/usr/bin/env python3
"""Build the static site from posts/*.md into dist/.

Usage:
    python3 scripts/build.py

Reads these environment variables (GitHub Actions sets them automatically):
    BASE_PATH       URL path the site is served under ("/" or "/repo/")
    SITE_URL        full site URL, for canonical links / RSS / sitemap
    INCLUDE_DRAFTS  if "1", also build posts marked `draft: true`
    DEV             if "1", write a .buildid file used by the dev live-reload
"""

import os
import re
import sys
import json
import time
import shutil
import datetime
import email.utils
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import config as cfg            # noqa: E402
import mdrender                 # noqa: E402
import templates                # noqa: E402

SITE = cfg.CONFIG
POSTS_DIR = os.path.join(ROOT, "posts")
DIST = os.path.join(ROOT, "dist")

# Palette used to auto-colour categories not listed in config.
PALETTE = ["--t-ctf", "--t-cert", "--t-vuln", "--t-mal", "--t-exp", "--t-red", "--accent-2"]


def make_color_for(categories):
    def color_for(cat):
        if cat in categories:
            return categories[cat]
        h = 0
        for ch in cat:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return PALETTE[h % len(PALETTE)]
    return color_for


def fmt_date_en(iso):
    try:
        d = datetime.date.fromisoformat(iso)
        return d.strftime("%b %d, %Y").replace(" 0", " ")
    except ValueError:
        return iso


def _render_lang(slug, data, body, id_prefix):
    html, toc = mdrender.render_markdown(body, id_prefix=id_prefix)
    words = len(re.findall(r'\S+', body))
    return {
        "title": str(data.get("title") or "").strip() or slug,
        "summary": str(data.get("summary") or mdrender.plain_summary(body)),
        "html": html,
        "toc": toc,
        "read": max(1, round(words / 200)),
    }


def load_posts(include_drafts):
    """Group posts/*.md by slug. A plain `slug.md` is the default language; a
    `slug.<lang>.md` (e.g. slug.vi.md) is that language's translation. Missing
    translations fall back to the default language."""
    default_lang = SITE["defaultLang"]
    langs = SITE["langs"]
    groups = {}   # slug -> { lang: (data, body, mtime, fname) }

    if not os.path.isdir(POSTS_DIR):
        return []

    for fname in sorted(os.listdir(POSTS_DIR)):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        path = os.path.join(POSTS_DIR, fname)
        data, body = mdrender.parse_frontmatter(open(path, encoding="utf-8").read())

        stem = fname[:-3]
        lang, base = default_lang, stem
        if "." in stem and stem.rsplit(".", 1)[1] in langs:
            base, lang = stem.rsplit(".", 1)

        slug = mdrender.slugify(str(data.get("slug") or base))
        bucket = groups.setdefault(slug, {})
        if lang in bucket:
            print(f"  ! duplicate {slug} [{lang}] — skipping {fname}")
            continue
        bucket[lang] = (data, body, os.path.getmtime(path), fname)

    posts = []
    for slug, bylang in groups.items():
        pick = default_lang if default_lang in bylang else \
            next((l for l in langs if l in bylang), sorted(bylang)[0])
        ddata, dbody, dmtime, _ = bylang[pick]

        if ddata.get("draft") and not include_drafts:
            continue

        date = str(ddata.get("date") or "").strip()
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            date = datetime.date.fromtimestamp(dmtime).isoformat()

        tags = ddata.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]

        i18n = {}
        for l in langs:
            d, b = (bylang[l][0], bylang[l][1]) if l in bylang else (ddata, dbody)
            i18n[l] = _render_lang(slug, d, b, "" if l == default_lang else f"{l}-")

        d0 = i18n[default_lang]
        posts.append({
            "slug": slug,
            "date": date,
            "date_fmt": fmt_date_en(date),
            "category": str(ddata.get("category") or "Notes"),
            "featured": bool(ddata.get("featured")),
            "image": str(ddata.get("image") or ""),
            "tags": [str(t) for t in tags],
            "title": d0["title"],
            "summary": d0["summary"],
            "read": d0["read"],
            "i18n": i18n,
        })

    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)
    return posts


def write(rel, text):
    path = os.path.join(DIST, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build():
    base = SITE.get("base") or os.environ.get("BASE_PATH") or "/"
    site_url = (SITE.get("siteUrl") or os.environ.get("SITE_URL") or "").rstrip("/")
    include_drafts = os.environ.get("INCLUDE_DRAFTS") == "1"

    def abs_url(path):
        return f"{site_url}/{str(path).lstrip('/')}" if site_url else ""

    ctx = SimpleNamespace(
        base=base,
        site_url=site_url,
        site=SITE,
        T=SITE["i18n"][SITE["defaultLang"]],
        color_for=make_color_for(SITE["categories"]),
        u=lambda p="": templates.u(base, p),
        abs=abs_url,
    )

    posts = load_posts(include_drafts)
    sections = SITE["sections"]
    name = SITE["name"]
    T = ctx.T

    # fresh output dir
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(DIST, exist_ok=True)

    # static assets
    assets = os.path.join(ROOT, "assets")
    if os.path.isdir(assets):
        shutil.copytree(assets, os.path.join(DIST, "assets"), dirs_exist_ok=True)
    static = os.path.join(ROOT, "static")
    if os.path.isdir(static):
        shutil.copytree(static, DIST, dirs_exist_ok=True)
    open(os.path.join(DIST, ".nojekyll"), "a").close()

    # pages
    write("index.html", templates.layout(
        ctx, title=SITE.get("homeTitle") or f"{name} | {SITE['handle']}",
        description=T["bio"],
        path="", active="home", content=templates.view_home(ctx, posts)))

    if "writeups" in sections:
        write("writeups/index.html", templates.layout(
            ctx, title=f"{T['writeups']} | {name}",
            description=f"Writeups and notes by {name}.",
            path="writeups/", active="writeups",
            content=templates.view_writeups(ctx, posts)))

        for p in posts:
            write(f"writeups/{p['slug']}/index.html", templates.layout(
                ctx, title=f"{p['title']} | {name}", description=p["summary"],
                path=f"writeups/{p['slug']}/", active="writeups",
                og_type="article", image=p["image"],
                content=templates.view_post(ctx, p, posts)))

    if "about" in sections:
        write("about/index.html", templates.layout(
            ctx, title=f"{T['about']} | {name}", description=T["aboutBody"],
            path="about/", active="about", content=templates.view_about(ctx)))

    if "certs" in sections:
        write("certs/index.html", templates.layout(
            ctx, title=f"{T['certs']} | {name}", description=T["certsNote"],
            path="certs/", active="certs", content=templates.view_certs(ctx)))

    write("404.html", templates.layout(
        ctx, title=f"404 | {name}", description="Page not found.",
        path="404.html", active="", content=templates.view_404(ctx)))

    # machine-readable index (handy for future tooling / external search)
    write("posts.json", json.dumps([{
        "slug": p["slug"], "title": p["title"], "date": p["date"],
        "category": p["category"], "summary": p["summary"], "tags": p["tags"],
        "featured": p["featured"], "readingTime": p["read"],
        "url": ctx.u(f"writeups/{p['slug']}/"),
    } for p in posts], ensure_ascii=False, indent=2))

    # RSS + sitemap + robots (need an absolute site URL to be valid)
    if site_url:
        _write_feed(ctx, posts, name)
        _write_sitemap(ctx, posts, sections)
        write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {abs_url('sitemap.xml')}\n")
    else:
        write("robots.txt", "User-agent: *\nAllow: /\n")
        print("  i no siteUrl set — skipping feed.xml and sitemap.xml "
              "(set siteUrl in src/config.py, or let GitHub Actions set SITE_URL).")

    if os.environ.get("DEV") == "1":
        write(".buildid", str(time.time()))

    print(f"✓ Built {len(posts)} post(s) → {os.path.relpath(DIST, ROOT)}/  "
          f"(base={base!r}, siteUrl={site_url or '—'})")


def _write_feed(ctx, posts, name):
    esc = mdrender.escape
    items = []
    for p in posts[:30]:
        link = ctx.abs(f"writeups/{p['slug']}/")
        try:
            dt = datetime.datetime.fromisoformat(p["date"] + "T00:00:00+00:00")
            pub = email.utils.format_datetime(dt)
        except ValueError:
            pub = ""
        items.append(
            "<item>"
            f"<title>{esc(p['title'])}</title>"
            f"<link>{esc(link)}</link>"
            f"<guid isPermaLink=\"true\">{esc(link)}</guid>"
            f"<category>{esc(p['category'])}</category>"
            + (f"<pubDate>{pub}</pubDate>" if pub else "")
            + f"<description>{esc(p['summary'])}</description>"
            "</item>"
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        f"<title>{esc(name)}</title>"
        f"<link>{esc(ctx.abs(''))}</link>"
        f"<description>{esc(ctx.T['bio'])}</description>"
        + "".join(items) +
        "</channel></rss>\n"
    )
    write("feed.xml", feed)


def _write_sitemap(ctx, posts, sections):
    esc = mdrender.escape
    urls = [(ctx.abs(""), None)]
    if "writeups" in sections:
        urls.append((ctx.abs("writeups/"), None))
        urls += [(ctx.abs(f"writeups/{p['slug']}/"), p["date"]) for p in posts]
    if "about" in sections:
        urls.append((ctx.abs("about/"), None))
    if "certs" in sections:
        urls.append((ctx.abs("certs/"), None))
    body = "".join(
        f"<url><loc>{esc(loc)}</loc>" + (f"<lastmod>{esc(lm)}</lastmod>" if lm else "") + "</url>"
        for loc, lm in urls
    )
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + body + "</urlset>\n")


if __name__ == "__main__":
    build()
