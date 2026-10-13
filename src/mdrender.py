"""Tiny, dependency-free Markdown renderer.

Supports the subset you need for writeups: #/##/### headings (with auto
anchors), - and * bullet lists, 1. numbered lists, ```fenced code``` (with an
optional language), > blockquotes, --- rules, and inline `code`, **bold**,
*italic* and [links](url). HTML in the source is escaped first, so a post can
never inject raw markup or scripts.
"""

import re

__all__ = ["escape", "safe_url", "slugify", "render_markdown",
           "parse_frontmatter", "plain_summary"]

_ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}


def escape(s):
    return "".join(_ESC.get(c, c) for c in str(s))


def safe_url(u):
    """Allow only safe link targets; anything odd collapses to '#'."""
    return u if re.match(r'^(https?:|mailto:|#|/|\.{0,2}/)', str(u), re.I) else "#"


def slugify(text):
    text = re.sub(r'`([^`]+)`', r'\1', text)        # drop inline-code backticks
    text = re.sub(r'[*_]', '', text)                 # drop emphasis markers
    text = re.sub(r'<[^>]+>', '', text)              # drop any stray tags
    text = text.strip().lower()
    text = re.sub(r'[^\w\s-]', '', text)             # keep word chars (unicode ok)
    text = re.sub(r'[\s]+', '-', text)
    return re.sub(r'-{2,}', '-', text).strip('-') or "section"


def _inline(s):
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(^|[^*])\*([^*\n]+)\*', r'\1<em>\2</em>', s)

    def _link(m):
        txt, url = m.group(1), m.group(2).replace("&amp;", "&")
        ext = bool(re.match(r'^https?:', url, re.I))
        attrs = ' target="_blank" rel="noopener noreferrer"' if ext else ""
        return f'<a href="{escape(safe_url(url))}"{attrs}>{txt}</a>'

    return re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', _link, s)


def render_markdown(src, id_prefix=""):
    """Return (html, toc) where toc is a list of {'level','text','id'}.

    id_prefix namespaces heading ids (and their anchors), so the same post
    rendered in two languages on one page doesn't produce duplicate ids.
    """
    code_blocks = []

    def _stash(m):
        lang, code = m.group(1), re.sub(r'\n$', '', m.group(2))
        cls = f' class="language-{lang}"' if lang else ""
        code_blocks.append(f'<pre><code{cls}>{code}</code></pre>')
        return f'\x00{len(code_blocks) - 1}\x00'

    src = re.sub(r'```(\w*)\n(.*?)```', _stash, escape(src), flags=re.DOTALL)

    out, toc = [], []
    seen_ids = {}
    list_kind = None
    para = []

    def flush_p():
        if para:
            out.append(f'<p>{_inline(" ".join(para))}</p>')
            para.clear()

    def flush_l():
        nonlocal list_kind
        if list_kind:
            out.append(f'</{list_kind}>')
            list_kind = None

    for line in src.split("\n"):
        stripped = line.strip()

        if re.fullmatch(r'\x00\d+\x00', stripped):
            flush_p(); flush_l()
            out.append(code_blocks[int(stripped.replace("\x00", ""))])
            continue

        m = re.match(r'^(#{1,3})\s+(.*)$', line)
        if m:
            flush_p(); flush_l()
            level, text = len(m.group(1)), m.group(2).strip()
            base_id = slugify(text)
            seen_ids[base_id] = seen_ids.get(base_id, 0) + 1
            hid = base_id if seen_ids[base_id] == 1 else f"{base_id}-{seen_ids[base_id]}"
            hid = id_prefix + hid
            if level >= 2:
                toc.append({"level": level, "text": re.sub(r'[*_`]', '', text), "id": hid})
            out.append(
                f'<h{level} id="{hid}">{_inline(text)}'
                f'<a class="anchor" href="#{hid}" aria-label="Link to this section">#</a>'
                f'</h{level}>'
            )
            continue

        m = re.match(r'^\s*[-*]\s+(.*)$', line)
        if m:
            flush_p()
            if list_kind != "ul":
                flush_l(); out.append("<ul>"); list_kind = "ul"
            out.append(f'<li>{_inline(m.group(1))}</li>')
            continue

        m = re.match(r'^\s*\d+\.\s+(.*)$', line)
        if m:
            flush_p()
            if list_kind != "ol":
                flush_l(); out.append("<ol>"); list_kind = "ol"
            out.append(f'<li>{_inline(m.group(1))}</li>')
            continue

        m = re.match(r'^&gt;\s?(.*)$', line)
        if m:
            flush_p(); flush_l()
            out.append(f'<blockquote>{_inline(m.group(1))}</blockquote>')
            continue

        if re.fullmatch(r'-{3,}', stripped):
            flush_p(); flush_l(); out.append("<hr>")
            continue

        if not stripped:
            flush_p(); flush_l()
            continue

        para.append(stripped)

    flush_p(); flush_l()
    return "\n".join(out), toc


def parse_frontmatter(raw):
    """Split a leading --- YAML-ish block from the body. Returns (data, body).

    Supports: key: value, "quoted", true/false, and simple [a, b, c] lists.
    """
    m = re.match(r'^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$', raw, flags=re.DOTALL)
    if not m:
        return {}, raw
    data = {}
    for line in m.group(1).split("\n"):
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if (val.startswith('"') and val.endswith('"')) or \
           (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        elif val.startswith("[") and val.endswith("]"):
            val = [p.strip().strip('"\'') for p in val[1:-1].split(",") if p.strip()]
        elif val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        data[key] = val
    return data, m.group(2)


def plain_summary(body, limit=160):
    """Best-effort one-line summary from the first real paragraph of a post."""
    in_fence = False
    for line in body.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not s or s.startswith("#") or s.startswith(">") \
           or re.match(r'^([-*]|\d+\.)\s', s) or re.fullmatch(r'-{3,}', s):
            continue
        s = re.sub(r'`([^`]+)`', r'\1', s)
        s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)
        s = re.sub(r'\*([^*]+)\*', r'\1', s)
        s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
        s = s.strip()
        if len(s) > limit:
            s = s[:limit].rsplit(" ", 1)[0] + "…"
        return s
    return ""
