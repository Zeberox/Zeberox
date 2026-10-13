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


# --- tiny, dependency-free syntax highlighter -----------------------------
# Runs on already-HTML-escaped code (so " is &quot; and ' is &#39;). It is a
# deliberately shallow, language-agnostic tokenizer: it colours comments,
# strings, numbers and a union of common keywords. It is not a parser, so it
# won't be perfect for every language — just enough to make code readable.
_KW = {
    # JS / TS
    "const", "let", "var", "function", "return", "if", "else", "for", "while",
    "do", "switch", "case", "break", "continue", "new", "class", "extends",
    "super", "this", "import", "from", "export", "default", "async", "await",
    "yield", "try", "catch", "finally", "throw", "typeof", "instanceof",
    "void", "delete",
    # Python
    "def", "elif", "lambda", "pass", "with", "as", "not", "and", "or", "is",
    "None", "True", "False", "global", "nonlocal", "raise", "except", "assert",
    "del", "in",
    # C / Go / Java-ish + shell
    "public", "private", "protected", "static", "final", "int", "char",
    "float", "double", "long", "short", "bool", "boolean", "string", "struct",
    "enum", "null", "nil", "true", "false", "package", "func", "type",
    "interface", "map", "range", "defer", "chan", "select", "go",
    "echo", "then", "fi", "done", "local", "unset", "read", "of",
}

_TOKEN_RE = re.compile(r'''
      (?P<comment> (?<![^\s])\#[^\n]* | (?<!:)//[^\n]* | /\*[\s\S]*?\*/ )
    | (?P<string> &quot;[^\n]*?&quot; | &\#39;[^\n]*?&\#39; | `[^`\n]*` )
    | (?P<num>     \b\d[\d.]*\b )
    | (?P<word>    [A-Za-z_]\w* )
''', re.VERBOSE)


def _highlight(code):
    def repl(m):
        kind = m.lastgroup
        val = m.group()
        if kind == "word":
            return f'<span class="t-kw">{val}</span>' if val in _KW else val
        return f'<span class="t-{kind[:3]}">{val}</span>'
    return _TOKEN_RE.sub(repl, code)


# Shell languages: every typed command gets a prompt frame.
_SHELL_LANGS = {"bash", "sh", "shell", "console", "terminal", "zsh"}
# All blocks rendered "green on black". An untagged block counts too (it is
# command output in these writeups) but its lines are never framed as commands.
_TERM_LANGS = _SHELL_LANGS | {""}

# Fallback identity for a bare command seen before any prompt in the document.
DEFAULT_USER, DEFAULT_HOST = "user", "localhost"

# A shell prompt line: user@host:path<$ or #> <command>.
_PROMPT_RE = re.compile(r'^(?P<u>[^\s@]+)@(?P<h>[^\s:]+):(?P<path>\S*?)[#$](?P<c>.*)$')


def _frame(user, host, path, cmd):
    """One command rendered as the Parrot OS two-line prompt."""
    ucls = "t-root" if user == "root" else "t-user"
    return (
        '<span class="t-box">┌──[</span>'
        f'<span class="{ucls}">{user}</span>'
        '<span class="t-at">@</span>'
        f'<span class="t-host">{host}</span>'
        '<span class="t-box">]─[</span>'
        f'<span class="t-path">{path or "~"}</span>'
        '<span class="t-box">]</span>\n'
        '<span class="t-box">└──╼ </span>'
        f'<span class="t-dollar">$</span> {cmd.strip()}'
    )


def _highlight_terminal(code, state, is_shell):
    """Frame typed commands (prompt lines, and bare commands in a shell block)
    while leaving output as plain green. `state` carries the last seen
    user/host across blocks so bare commands inherit the right identity.
    Runs on already-escaped text."""
    lines = code.split("\n")
    has_prompt = any(_PROMPT_RE.match(l) for l in lines)
    out = []
    framed_bare = False  # in a prompt-less shell block, only the first line is the command
    for l in lines:
        m = _PROMPT_RE.match(l)
        if m:
            state["user"], state["host"] = m.group("u"), m.group("h")
            out.append(_frame(m.group("u"), m.group("h"), m.group("path"), m.group("c")))
        elif (is_shell and not has_prompt and not framed_bare
                and l.strip() and not l.lstrip().startswith("#")):
            framed_bare = True
            out.append(_frame(state["user"] or DEFAULT_USER,
                              state["host"] or DEFAULT_HOST, "~", l))
        else:
            out.append(l)  # output / comment
    return "\n".join(out)


def render_markdown(src, id_prefix=""):
    """Return (html, toc) where toc is a list of {'level','text','id'}.

    id_prefix namespaces heading ids (and their anchors), so the same post
    rendered in two languages on one page doesn't produce duplicate ids.
    """
    code_blocks = []
    src = escape(src)

    # Seed the terminal identity from the first prompt in the document, so a
    # bare command appearing before any prompt still shows the right user@host.
    term_state = {"user": None, "host": None}
    seed = next((m for m in (_PROMPT_RE.match(l) for l in src.split("\n")) if m), None)
    if seed:
        term_state["user"], term_state["host"] = seed.group("u"), seed.group("h")

    def _stash(m):
        lang, code = m.group(1), re.sub(r'\n$', '', m.group(2))
        cls = f' class="language-{lang}"' if lang else ""
        low = lang.lower()
        if low in _TERM_LANGS:
            body = _highlight_terminal(code, term_state, low in _SHELL_LANGS)
            code_blocks.append(f'<pre class="term"><code{cls}>{body}</code></pre>')
        else:
            code_blocks.append(f'<pre><code{cls}>{_highlight(code)}</code></pre>')
        return f'\x00{len(code_blocks) - 1}\x00'

    src = re.sub(r'```(\w*)\n(.*?)```', _stash, src, flags=re.DOTALL)

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
