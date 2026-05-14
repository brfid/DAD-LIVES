#!/usr/bin/env python3
"""dad-lives — replaces blocked HTTP ads with dad wisdom via Pi-hole."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from flask import Flask, Response, redirect, render_template_string, request

# ── Configuration ──────────────────────────────────────────────────────────────

PORT = 80

STATE_FILE = Path(__file__).parent / "state.json"

SLOGANS: list[str] = [
    "DAD RULES",
    "OBEY YOUR PARENTS",
    "DRINK WATER",
    "BE KIND",
    "NO SHOUTING",
]

# ── Response generation ────────────────────────────────────────────────────────

def _x(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_svg(slogan: str) -> str:
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 100' "
        "preserveAspectRatio='xMidYMid meet'>"
        "<rect width='100%' height='100%' fill='white'/>"
        "<rect x='2' y='2' width='596' height='96' fill='none' stroke='black' stroke-width='2'/>"
        f"<text x='50%' y='50%' dominant-baseline='central' text-anchor='middle' "
        f"font-family='Impact,Arial Black,sans-serif' font-weight='900' "
        f"font-size='56' letter-spacing='4' fill='black'>{_x(slogan)}</text>"
        "</svg>"
    )


def make_html(slogan: str) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        "*{margin:0;padding:0;box-sizing:border-box}"
        "body{background:#fff;display:flex;align-items:center;justify-content:center;height:100vh;width:100vw}"
        "h1{font-family:Impact,'Arial Black',sans-serif;font-size:clamp(28px,8vw,80px);"
        "border:2px solid #000;padding:20px 40px;letter-spacing:.08em;text-align:center}"
        f"</style></head><body><h1>{_x(slogan)}</h1></body></html>"
    )


def response_type(accept: str, path: str) -> str:
    """Classify a request as 'svg', 'js', or 'html'."""
    if "image/" in accept or path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp")):
        return "svg"
    if "javascript" in accept or path.endswith(".js"):
        return "js"
    return "html"


# ── Slogan cycling ─────────────────────────────────────────────────────────────

_lock = threading.Lock()


def _load() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"slogans": list(SLOGANS), "index": 0}


def _save(data: dict) -> None:
    STATE_FILE.write_text(json.dumps(data, indent=2))


def next_slogan() -> str:
    with _lock:
        data = _load()
        slogans = data.get("slogans") or SLOGANS
        idx = data.get("index", 0) % len(slogans)
        slogan = slogans[idx]
        data["index"] = (idx + 1) % len(slogans)
        _save(data)
        return slogan


# ── Flask app ──────────────────────────────────────────────────────────────────

app = Flask(__name__)

_ADMIN_TMPL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>dad-lives</title><style>
body{font-family:monospace;max-width:600px;margin:40px auto;padding:0 20px}
h1{font-family:Impact,sans-serif;letter-spacing:.08em;font-size:2.5rem}
.item{display:flex;align-items:center;justify-content:space-between;
      padding:8px 12px;border:2px solid #000;margin-bottom:6px;
      font-size:18px;font-weight:bold}
.item.next{background:#000;color:#fff}
button{font-family:monospace;font-size:13px;padding:4px 10px;
       cursor:pointer;border:2px solid currentColor;background:transparent}
.item.next button{color:#fff;border-color:#fff}
.add{display:flex;gap:8px;margin-top:20px}
.add input{flex:1;font-family:monospace;font-size:16px;font-weight:bold;
           padding:8px;border:2px solid #000;text-transform:uppercase}
.add button{font-size:16px;padding:8px 16px;background:#000;color:#fff;border:2px solid #000}
</style></head><body>
<h1>DAD-LIVES</h1>
<p>Next: <strong>{{ current }}</strong></p>
<div>
{% for i, s in slogans %}
<div class="item{% if i == idx %} next{% endif %}">
  <span>{{ s }}</span>
  <form method="POST" action="/admin/delete/{{ i }}" style="display:inline">
    <button>delete</button>
  </form>
</div>
{% endfor %}
</div>
<form class="add" method="POST" action="/admin/add">
  <input name="slogan" placeholder="NEW SLOGAN" autocomplete="off" required>
  <button type="submit">ADD</button>
</form>
</body></html>"""


@app.get("/admin")
def admin() -> str:
    data = _load()
    slogans = data.get("slogans") or SLOGANS
    idx = data.get("index", 0) % len(slogans) if slogans else 0
    return render_template_string(
        _ADMIN_TMPL,
        slogans=list(enumerate(slogans)),
        current=slogans[idx] if slogans else "(none)",
        idx=idx,
    )


@app.post("/admin/add")
def admin_add():
    slogan = request.form.get("slogan", "").strip().upper()
    if slogan:
        with _lock:
            data = _load()
            data.setdefault("slogans", list(SLOGANS)).append(slogan)
            _save(data)
    return redirect("/admin")


@app.post("/admin/delete/<int:idx>")
def admin_delete(idx: int):
    with _lock:
        data = _load()
        slogans = data.get("slogans", list(SLOGANS))
        if 0 <= idx < len(slogans):
            slogans.pop(idx)
            data["slogans"] = slogans
            data["index"] = data.get("index", 0) % len(slogans) if slogans else 0
            _save(data)
    return redirect("/admin")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path: str):
    if path.startswith("admin"):
        return redirect("/admin")
    slogan = next_slogan()
    rtype = response_type(request.headers.get("Accept", ""), path)
    if rtype == "js":
        return Response("", mimetype="application/javascript")
    if rtype == "svg":
        return Response(make_svg(slogan), mimetype="image/svg+xml")
    return Response(make_html(slogan), mimetype="text/html")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()
