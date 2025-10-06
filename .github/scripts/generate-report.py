#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path


def read_text(path: str, limit: int = 200_000):
    p = Path(path)
    if not p.exists():
        return None
    try:
        data = p.read_text(encoding="utf-8", errors="replace")
        if len(data) > limit:
            data = data[:limit] + "\n...\n[truncated]\n"
        return data
    except Exception as e:
        return f"[error reading {path}: {e}]"


def try_json(path: str):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def section(title, body_html):
    return f"""<section class="card">
  <h2>{escape(title)}</h2>
  {body_html}
</section>"""


def pre_block(text, lang=""):
    cl = f" class='code {lang}'" if lang else " class='code'"
    return f"<pre{cl}><code>{escape(text)}</code></pre>"


now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
repo = os.getenv("GITHUB_REPOSITORY", "")
run_url = f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"
commit = os.getenv("GITHUB_SHA", "")

compose_cfg = read_text("compose.config.yaml")
targets = try_json("prom_targets.json")
coverage_xml = read_text("coverage/coverage.xml")

sections = ""
meta = f"""<table>
<tr><th>Repository</th><td>{escape(repo)}</td></tr>
<tr><th>Run</th><td><a href="{escape(run_url)}">{escape(run_url)}</a></td></tr>
<tr><th>Commit</th><td><code>{escape(commit)}</code></td></tr>
<tr><th>Generated</th><td>{escape(now)}</td></tr>
</table>"""
sections += section("Run metadata", meta)

if compose_cfg:
    sections += section("Compose (merged config)", pre_block(compose_cfg, "yaml"))

if targets:
    rows = []
    for t in targets.get("data", {}).get("activeTargets", []):
        job = t.get("labels", {}).get("job", "")
        url = t.get("scrapeUrl", "")
        last = t.get("lastScrape", "")
        rows.append(f"<tr><td>{escape(job)}</td><td>{escape(url)}</td><td>{escape(last)}</td></tr>")
    table = "<table><tr><th>job</th><th>scrapeUrl</th><th>lastScrape</th></tr>" + "".join(rows) + "</table>"
    sections += section("Prometheus active targets", table)

if coverage_xml:
    sections += section("Coverage (XML snippet)", pre_block(coverage_xml[:4000], "xml"))

html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>CI Report</title>
<style>
:root {{ --muted:#f6f7f9; --border:#e5e7eb; --fg:#111827; --fg2:#374151; }}
* {{ box-sizing: border-box; }}
body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; color: var(--fg); background: #fff; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
h1 {{ font-size: 1.6rem; margin: 0 0 1rem; }}
h2 {{ font-size: 1.2rem; margin: 0 0 .75rem; color: var(--fg2); }}
table {{ border-collapse: collapse; width: 100%; margin: .5rem 0 0; }}
th, td {{ border: 1px solid var(--border); padding: .5rem .6rem; text-align: left; }}
.card {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin: 1rem 0; }}
pre.code {{ background: var(--muted); padding: 1rem; border-radius: 10px; overflow: auto; }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
a {{ color: #2563eb; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>CI Report</h1>
{sections}
</body>
</html>"""

Path("ci-report.html").write_text(html_doc, encoding="utf-8")
print("Wrote ci-report.html")
