"""HTML templates. Every page is a full, pre-rendered document so it works
without JavaScript and gets proper <title>/meta tags for search engines and
link previews. All internal links go through ctx.u(...) so the site works both
at a domain root and under a /repo/ subpath on GitHub Pages."""

import json
import re
import datetime

from mdrender import escape

SECTION_PATH = {"home": "", "writeups": "writeups/", "certs": "certs/", "about": "about/"}


def u(base, p=""):
    b = (base or "/").rstrip("/") + "/"
    return b + str(p).lstrip("/")


def _link_href(ctx, val):
    return val if re.match(r'^(https?:|mailto:)', val, re.I) else ctx.u(val)


# --------------------------------------------------------------------------
#  Layout
# --------------------------------------------------------------------------
def layout(ctx, *, title, description, path, active, content,
           og_type="website", image=""):
    site, T = ctx.site, ctx.T
    name = escape(site["name"])

    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        f'<title>{escape(title)}</title>',
        f'<meta name="description" content="{escape(description)}">',
    ]

    canonical = ctx.abs(path)
    if canonical:
        head.append(f'<link rel="canonical" href="{escape(canonical)}">')

    def _img(val):
        if re.match(r'^https?:', val, re.I):
            return val
        return ctx.abs(val) or ctx.u(val)

    og_img = _img(image) if image else (_img(site["ogImage"]) if site.get("ogImage") else "")

    head += [
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{escape(title)}">',
        f'<meta property="og:description" content="{escape(description)}">',
        f'<meta property="og:site_name" content="{name}">',
    ]
    if canonical:
        head.append(f'<meta property="og:url" content="{escape(canonical)}">')
    if og_img:
        head.append(f'<meta property="og:image" content="{escape(og_img)}">')
    head.append(f'<meta name="twitter:card" content="{"summary_large_image" if og_img else "summary"}">')

    # SVG for browsers that take it, .ico for Safari/older, PNG for iOS home screen.
    head += [
        f'<link rel="icon" href="{ctx.u("favicon.svg")}" type="image/svg+xml">',
        f'<link rel="icon" href="{ctx.u("favicon.ico")}" sizes="16x16 32x32 48x48">',
        f'<link rel="apple-touch-icon" href="{ctx.u("img/apple-touch-icon.png")}">',
    ]
    if ctx.site_url:
        head.append(f'<link rel="alternate" type="application/rss+xml" '
                    f'title="{name}" href="{ctx.u("feed.xml")}">')

    head += [
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">',
        f'<link rel="stylesheet" href="{ctx.u("assets/style.css")}">',
        '<meta name="generator" content="md-writeups (static)">',
    ]

    i18n_js = json.dumps(site["i18n"], ensure_ascii=False).replace("<", "\\u003c")
    langs_js = json.dumps(site["langs"])
    head.append(
        f'<script>window.__I18N__={i18n_js};'
        f'window.__LANGS__={langs_js};'
        f'window.__DEFAULT_LANG__="{site["defaultLang"]}";'
        f'window.__SITE_NAME__={json.dumps(site["name"])};</script>'
    )

    # header: brand + nav + language switch
    logo = (
        '<span class="logo" aria-hidden="true">'
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
        '<rect x="6" y="6" width="12" height="12" rx="2"/>'
        '<path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></svg></span>'
    )
    brand = (f'<a class="brand" href="{ctx.u("")}">{logo}'
             f'<span class="bt"><b>{name}</b><small>{escape(site["tagline"])}</small></span></a>')

    nav_items = []
    for key in site["sections"]:
        if key not in SECTION_PATH:
            continue
        cur = ' aria-current="page"' if key == active else ""
        nav_items.append(
            f'<a href="{ctx.u(SECTION_PATH[key])}"{cur} data-i18n="{key}">{escape(T[key])}</a>'
        )
    nav = f'<nav aria-label="Main">{"".join(nav_items)}</nav>'

    # Segmented language switch. The sliding highlight is one element whose
    # position is driven by --i (index of the active language), so flipping the
    # language animates instead of jumping. Without JS it simply sits on the
    # default language, which is what the page actually shows.
    lang_list = site["langs"]
    default_i = lang_list.index(site["defaultLang"]) if site["defaultLang"] in lang_list else 0
    langs = "".join(
        f'<button type="button" class="seg-btn" data-lang="{l}" data-i="{i}" '
        f'aria-pressed="{"true" if l == site["defaultLang"] else "false"}">'
        f'<span>{l.upper()}</span></button>'
        for i, l in enumerate(lang_list)
    )
    tools = (f'<div class="tools"><div class="seg" id="langseg" role="group" aria-label="Language" '
             f'style="--n:{len(lang_list)};--i:{default_i}">'
             f'<span class="seg-thumb" aria-hidden="true"></span>{langs}</div></div>'
             if len(lang_list) > 1 else "")

    year = datetime.date.today().year
    footer = f'© {year} {name}'

    return f"""<!doctype html>
<html lang="{site['defaultLang']}">
<head>
{chr(10).join(head)}
</head>
<body>
<header class="top"><div class="wrap">{brand}{nav}{tools}</div></header>
<main><div class="wrap">{content}</div></main>
<footer><div class="wrap">{footer}</div></footer>
<script src="{ctx.u("assets/app.js")}" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
#  Components
# --------------------------------------------------------------------------
def lang_spans(ctx, values):
    """Render one <span> per language; JS shows the active one. Falls back to
    the default language's text for any language missing a value."""
    default = values[ctx.site["defaultLang"]]
    out = []
    for l in ctx.site["langs"]:
        hid = "" if l == ctx.site["defaultLang"] else " hidden"
        out.append(f'<span data-lang-text="{l}"{hid}>{escape(values.get(l) or default)}</span>')
    return "".join(out)


def crumbs(ctx, items):
    parts = []
    for i, it in enumerate(items):
        if i:
            parts.append('<i>›</i>')
        if it.get("html"):
            parts.append(f'<span>{it["html"]}</span>')
        elif it.get("href"):
            attr = f' data-i18n="{it["i18n"]}"' if it.get("i18n") else ""
            parts.append(f'<a href="{it["href"]}"{attr}>{escape(it["text"])}</a>')
        else:
            parts.append(f'<span>{escape(it["text"])}</span>')
    return f'<div class="crumbs">{"".join(parts)}</div>'


def post_card(ctx, p):
    color = ctx.color_for(p["category"])
    langs = ctx.site["langs"]
    title_h = lang_spans(ctx, {l: p["i18n"][l]["title"] for l in langs})
    summ_h = lang_spans(ctx, {l: p["i18n"][l]["summary"] for l in langs})
    # searchable in either language
    words = [p["i18n"][l]["title"] + " " + p["i18n"][l]["summary"] for l in langs]
    text = escape(" ".join(words + p.get("tags", []) + [p["category"]]).lower())
    return (
        f'<a class="card" data-card data-cat="{escape(p["category"])}" data-text="{text}" '
        f'href="{ctx.u("writeups/" + p["slug"] + "/")}">'
        f'<div class="meta"><span class="tag" style="color:var({color})">{escape(p["category"])}</span>'
        f'<time datetime="{escape(p["date"])}" data-date>{escape(p["date_fmt"])}</time></div>'
        f'<h3>{title_h}</h3>'
        f'<p>{summ_h}</p>'
        f'<span class="more"><span data-i18n="readMore">{escape(ctx.T["readMore"])}</span> →</span>'
        f'</a>'
    )


def _stats(ctx, posts):
    T = ctx.T
    total = len(posts)
    counts = {}
    for p in posts:
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    ordered = [c for c in ctx.site["categories"] if c in counts]
    ordered += [c for c in sorted(counts) if c not in ordered]
    rows = "".join(
        f'<span>{escape(c)}</span><b>{counts[c]}</b>'
        f'<div class="bar" style="grid-column:1/-1"><i style="width:{round(counts[c] / total * 100)}%"></i></div>'
        for c in ordered
    )
    top = posts[0] if posts else None
    newest = ""
    if top:
        color = ctx.color_for(top["category"])
        newest = (
            f'<a href="{ctx.u("writeups/" + top["slug"] + "/")}" style="font-weight:700">{escape(top["title"])}</a>'
            f'<div style="display:flex;gap:10px;align-items:center;font-size:12px;color:var(--muted)">'
            f'<span class="tag" style="color:var({color})">{escape(top["category"])}</span>'
            f'<time datetime="{escape(top["date"])}" data-date>{escape(top["date_fmt"])}</time></div>'
        )
    return (
        '<div class="panels">'
        f'<div class="panel"><div class="panel-h"><span data-i18n="writeups">{escape(T["writeups"])}</span>'
        f'<span class="badge">INDEX</span></div><div class="big">{total}</div>'
        f'<small style="color:var(--muted)">{len(ordered)} <span data-i18n="topics">{escape(T["topics"])}</span></small></div>'
        f'<div class="panel"><div class="panel-h"><span data-i18n="topics">{escape(T["topics"])}</span></div>'
        f'<div class="mini">{rows}</div></div>'
        f'<div class="panel"><div class="panel-h"><span data-i18n="newest">{escape(T["newest"])}</span>'
        f'<span class="badge">NEW</span></div>{newest}</div>'
        '</div>'
    )


# --------------------------------------------------------------------------
#  Views
# --------------------------------------------------------------------------
def view_home(ctx, posts):
    site, T = ctx.site, ctx.T
    links = site["links"]
    featured = [p for p in posts if p.get("featured")][:site["featuredCount"]]
    fset = set(id(p) for p in featured)
    latest = [p for p in posts if id(p) not in fset][:3]

    btns = [f'<a class="btn primary" href="{ctx.u("about/")}" data-i18n="about">{escape(T["about"])}</a>']
    if links.get("github"):
        btns.append(f'<a class="btn" href="{escape(links["github"])}" target="_blank" rel="noopener noreferrer">GitHub</a>')
    if links.get("cv"):
        btns.append(f'<a class="btn" href="{escape(_link_href(ctx, links["cv"]))}" target="_blank" rel="noopener noreferrer">Download CV</a>')
    if links.get("email"):
        btns.append(f'<a class="btn" href="{escape(links["email"])}">Email</a>')
    if links.get("pgp"):
        btns.append(f'<a class="btn" href="{escape(_link_href(ctx, links["pgp"]))}" target="_blank" rel="noopener noreferrer">PGP key</a>')

    html = [
        f'<p class="prompt">~/{escape(site["handle"])} $ whoami</p>',
        f'<h1>{escape(site["name"])}</h1>',
        f'<p class="role" data-i18n="roles">{escape(T["roles"])}</p>',
        f'<p class="lead" data-i18n="bio">{escape(T["bio"])}</p>',
        f'<div class="btns">{"".join(btns)}</div>',
        _stats(ctx, posts),
    ]
    if featured:
        html.append(f'<h2 data-i18n="featured">{escape(T["featured"])}</h2>'
                    f'<div class="grid">{"".join(post_card(ctx, p) for p in featured)}</div>')
    if latest:
        html.append(
            '<h2 style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">'
            f'<span data-i18n="latest">{escape(T["latest"])}</span>'
            f'<a href="{ctx.u("writeups/")}" style="font-size:13px;font-weight:400" data-i18n="viewAll">{escape(T["viewAll"])}</a></h2>'
            f'<div class="grid">{"".join(post_card(ctx, p) for p in latest)}</div>'
        )
    return "".join(html)


def view_writeups(ctx, posts):
    T = ctx.T
    present = [c for c in ctx.site["categories"] if any(p["category"] == c for p in posts)]
    present += sorted({p["category"] for p in posts} - set(present))
    chips = [f'<button class="chip" data-c="" aria-pressed="true" data-i18n="all">{escape(T["all"])}</button>']
    chips += [f'<button class="chip" data-c="{escape(c)}" aria-pressed="false">{escape(c)}</button>' for c in present]
    cards = "".join(post_card(ctx, p) for p in posts)
    return (
        crumbs(ctx, [{"text": T["home"], "href": ctx.u(""), "i18n": "home"},
                     {"text": T["writeups"]}])
        + f'<h1 data-i18n="writeups">{escape(T["writeups"])}</h1>'
        + '<div class="toolbar">'
        f'<input type="search" id="q" placeholder="{escape(T["search"])}" '
        f'aria-label="{escape(T["search"])}" data-i18n-ph="search" data-i18n-aria="search">'
        '</div>'
        f'<div class="chips" id="chips">{"".join(chips)}</div>'
        f'<div class="grid" id="results">{cards}</div>'
        f'<div class="empty" id="empty" hidden data-i18n="noResults">{escape(T["noResults"])}</div>'
    )


def view_post(ctx, p, posts):
    T = ctx.T
    langs = ctx.site["langs"]
    color = ctx.color_for(p["category"])
    title_h = lang_spans(ctx, {l: p["i18n"][l]["title"] for l in langs})

    blocks = []
    for l in langs:
        info = p["i18n"][l]
        toc = ""
        if len(info["toc"]) >= 3:
            # NOTE: no escape() here on purpose. mdrender escapes the whole post
            # source before it parses anything, so heading text reaches the toc
            # already escaped ("/proc/&lt;PID&gt;/mem"). Escaping it a second
            # time turns the entities into literals ("&amp;lt;") and the reader
            # sees the raw &lt; in the contents list.
            lis = "".join(
                f'<li class="lvl{it["level"]}"><a href="#{it["id"]}">{it["text"]}</a></li>'
                for it in info["toc"])
            toc = (f'<nav class="toc" aria-label="Table of contents">'
                   f'<div class="toc-h" data-i18n="contents">{escape(T["contents"])}</div><ul>{lis}</ul></nav>')
        hid = "" if l == ctx.site["defaultLang"] else " hidden"
        blocks.append(f'<div data-lang-body="{l}"{hid}>{toc}<div class="md">{info["html"]}</div></div>')

    return (
        crumbs(ctx, [{"text": T["home"], "href": ctx.u(""), "i18n": "home"},
                     {"text": T["writeups"], "href": ctx.u("writeups/"), "i18n": "writeups"},
                     {"html": title_h}])
        + f'<a class="back" href="{ctx.u("writeups/")}">← <span data-i18n="back">{escape(T["back"])}</span></a>'
        + '<article class="article">'
        + f'<h1>{title_h}</h1>'
        + '<div class="statusbar">'
        + f'<span class="pill" style="--pc:var({color})">{escape(p["category"])}</span>'
        + f'<span><span data-i18n="published">{escape(T["published"])}</span>: '
          f'<time datetime="{escape(p["date"])}" data-date>{escape(p["date_fmt"])}</time></span>'
        + '</div>'
        + "".join(blocks)
        + '</article>'
    )


def view_about(ctx):
    site, T = ctx.site, ctx.T
    links = site["links"]
    rows = []
    label = {"email": "Email", "github": "GitHub", "cv": "CV", "pgp": "PGP"}
    for key in ("email", "github", "cv", "pgp"):
        val = links.get(key)
        if not val:
            continue
        shown = val.replace("mailto:", "")
        href = _link_href(ctx, val)
        ext = "" if val.startswith("mailto:") else ' target="_blank" rel="noopener noreferrer"'
        rows.append(f'<dt>{label[key]}</dt><dd><a href="{escape(href)}"{ext}>{escape(shown)}</a></dd>')
    dl = f'<dl class="kv">{"".join(rows)}</dl>' if rows else ""
    return (
        crumbs(ctx, [{"text": T["home"], "href": ctx.u(""), "i18n": "home"},
                     {"text": T["about"]}])
        + f'<h1 data-i18n="about">{escape(T["about"])}</h1>'
        + f'<p class="lead" data-i18n="aboutBody">{escape(T["aboutBody"])}</p>'
        + (f'<h2 data-i18n="links">{escape(T["links"])}</h2>{dl}' if dl else "")
    )


def view_certs(ctx):
    site, T = ctx.site, ctx.T
    cards = []
    for c in site.get("certs", []):
        badge = ""
        if c.get("badge"):
            bsrc = c["badge"] if re.match(r'^(https?:|data:)', c["badge"]) else ctx.u(c["badge"])
            badge = f'<img src="{escape(bsrc)}" alt="{escape(c["name"])} badge" width="76" height="76" loading="lazy">'
        status = f'<span class="badge">{escape(c["status"])}</span>' if c.get("status") else ""
        issuer = f'<div class="issuer">{escape(c["issuer"])}</div>' if c.get("issuer") else ""
        note = f'<p>{escape(c["note"])}</p>' if c.get("note") else ""
        name = escape(c["name"])
        if c.get("url"):
            name = f'<a href="{escape(c["url"])}" target="_blank" rel="noopener noreferrer">{name}</a>'
        cards.append(
            f'<div class="cert-row">{badge}<div><h3>{name}{status}</h3>{issuer}{note}</div></div>'
        )
    body = "".join(cards) or '<div class="empty">No certifications yet.</div>'
    lead = (f'<p class="lead" data-i18n="certsNote">{escape(T["certsNote"])}</p>'
            if T.get("certsNote") else "")
    return (
        crumbs(ctx, [{"text": T["home"], "href": ctx.u(""), "i18n": "home"},
                     {"text": T["certs"]}])
        + f'<h1 data-i18n="certs">{escape(T["certs"])}</h1>'
        + lead
        + f'<div class="cert-list">{body}</div>'
    )


def view_404(ctx):
    T = ctx.T
    return (f'<h1>404</h1><p class="lead">This page could not be found.</p>'
            f'<p><a class="btn primary" href="{ctx.u("")}" data-i18n="home">{escape(T["home"])}</a></p>')
