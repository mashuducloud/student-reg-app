#!/usr/bin/env python3
import html, json, subprocess, urllib.request, pathlib

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout

cfg = run(["docker","compose","-f","infra/docker-compose.yml","config"])
ps  = run(["docker","compose","-f","infra/docker-compose.yml","ps"])
imgs= run(["docker","compose","-f","infra/docker-compose.yml","images"])

try:
    raw = urllib.request.urlopen("http://localhost:9091/api/v1/targets?state=active", timeout=10).read().decode()
    targets = json.dumps(json.loads(raw), indent=2)
except Exception as e:
    targets = f"error fetching targets: {e}"

html_doc = f"""<!doctype html><meta charset="utf-8">
<title>CI Infra Report</title>
<style>
  body{{font:14px/1.5 system-ui,Segoe UI,Arial,sans-serif;margin:24px;max-width:1100px}}
  h1,h2{{margin:16px 0 8px}}
  pre{{background:#f6f8fa;padding:12px;border-radius:8px;overflow:auto;border:1px solid #eaecef}}
  code{{font-family:ui-monospace,Menlo,Consolas,monospace}}
</style>
<h1>CI Infra Report</h1>
<h2>Compose Config (sanity)</h2>
<pre><code>{html.escape(cfg)}</code></pre>
<h2>Services (docker compose ps)</h2>
<pre><code>{html.escape(ps)}</code></pre>
<h2>Images (docker compose images)</h2>
<pre><code>{html.escape(imgs)}</code></pre>
<h2>Prometheus Active Targets</h2>
<pre><code>{html.escape(targets)}</code></pre>
"""
pathlib.Path("ci-report.html").write_text(html_doc, encoding="utf-8")
print("Wrote ci-report.html")
