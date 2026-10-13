#!/usr/bin/env python3
"""Local authoring workflow: build, serve, and rebuild on every change.

    python3 scripts/dev.py [port]

Open the printed URL, edit anything under posts/ src/ assets/ static/, and the
page reloads by itself. No build step to remember, no dependencies to install.
"""

import os
import sys
import time
import threading
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH = ["posts", "src", "assets", "static"]
BUILD = os.path.join(ROOT, "scripts", "build.py")

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import serve  # noqa: E402


def snapshot():
    state = {}
    for d in WATCH:
        base = os.path.join(ROOT, d)
        for root, _, files in os.walk(base):
            for f in files:
                p = os.path.join(root, f)
                try:
                    state[p] = os.path.getmtime(p)
                except OSError:
                    pass
    return state


def rebuild():
    env = dict(os.environ, DEV="1", BASE_PATH="/", SITE_URL="")
    r = subprocess.run([sys.executable, BUILD], env=env)
    if r.returncode != 0:
        print("  ! build failed — fix the error above and save again")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print("Building…")
    rebuild()
    threading.Thread(target=serve.run,
                     kwargs={"port": port, "dev": True}, daemon=True).start()
    print("  watching posts/ src/ assets/ static/ — Ctrl+C to stop\n")

    prev = snapshot()
    try:
        while True:
            time.sleep(0.5)
            cur = snapshot()
            if cur != prev:
                prev = cur
                print("Change detected — rebuilding…")
                rebuild()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
