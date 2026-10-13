#!/usr/bin/env python3
"""Minimal static file server for local preview (standard library only).

    python3 scripts/serve.py [dir] [port]

Serves pretty directory URLs (/writeups/slug/ -> .../index.html) and falls back
to 404.html, mirroring how GitHub Pages behaves. With --dev it injects a tiny
live-reload snippet that polls /__reload and refreshes when the build changes.
"""

import os
import sys
import posixpath
import mimetypes
import urllib.parse
import http.server
import socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RELOAD_JS = (
    b"<script>(function(){var cur=null;setInterval(function(){"
    b"fetch('/__reload',{cache:'no-store'}).then(function(r){return r.text()})"
    b".then(function(v){if(cur===null){cur=v}else if(v!==cur){location.reload()}})"
    b".catch(function(){})},1000);})();</script>"
)


def run(directory=None, port=8000, dev=False):
    directory = os.path.abspath(directory or os.path.join(ROOT, "dist"))
    real_root = os.path.realpath(directory)

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            sys.stdout.write("  " + (fmt % args) + "\n")

        def do_HEAD(self):
            self._handle(head=True)

        def do_GET(self):
            self._handle(head=False)

        def _handle(self, head):
            path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)

            if dev and path == "/__reload":
                data = b"0"
                bid = os.path.join(directory, ".buildid")
                if os.path.isfile(bid):
                    data = open(bid, "rb").read().strip() or b"0"
                return self._send(200, "text/plain; charset=utf-8", data, head)

            rel = posixpath.normpath(path).lstrip("/")
            fs = os.path.join(directory, rel)
            if os.path.isdir(fs):
                fs = os.path.join(fs, "index.html")

            if not os.path.isfile(fs) or not os.path.realpath(fs).startswith(real_root):
                nf = os.path.join(directory, "404.html")
                if os.path.isfile(nf):
                    body = open(nf, "rb").read()
                    return self._send(404, "text/html; charset=utf-8",
                                      self._inject(body) if dev else body, head)
                return self._send(404, "text/plain; charset=utf-8", b"404 Not Found", head)

            ctype = mimetypes.guess_type(fs)[0] or "application/octet-stream"
            body = open(fs, "rb").read()
            if dev and ctype.startswith("text/html"):
                body = self._inject(body)
            self._send(200, ctype, body, head)

        def _inject(self, body):
            if b"</body>" in body:
                return body.replace(b"</body>", _RELOAD_JS + b"</body>", 1)
            return body + _RELOAD_JS

        def _send(self, code, ctype, body, head):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            if dev:
                self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if not head:
                self.wfile.write(body)

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", port), Handler)
    httpd.daemon_threads = True
    print(f"  serving {os.path.relpath(directory, ROOT)}/ at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--dev"]
    run(directory=args[0] if len(args) > 0 else None,
        port=int(args[1]) if len(args) > 1 else 8000,
        dev="--dev" in sys.argv)
