#!/usr/bin/env python3
import pathlib, datetime

root = pathlib.Path.cwd()
compose_cfg = root / "compose.config.yaml"
cov_xml = root / "coverage" / "coverage.xml"
cov_html_dir = root / "coverage" / "htmlcov"
out = root / "ci-report.html"

ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

rows = []
def add_row(name, path):
    exists = path.exists()
    rows.append( (name, str(path.relative_to(root)), "YES" if exists else "NO") )

add_row("Compose (rendered) config", compose_cfg)
add_row("Coverage XML", cov_xml)
add_row("Coverage HTML index", cov_html_dir / "index.html")

def row_html(name, path, ok):
    cls = "ok" if ok == "YES" else "no"
    return f"<tr><td>{name}</td><td><a href=\"{path}\">{path}</a></td><td><span class=\"badge {cls}\">{ok}</span></td></tr>"

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>CI Report - {ts}</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; padding: 24px; }}
h1 {{ margin: 0 0 12px; font-size: 20px; }}
table {{ border-collapse: collapse; width: 100%; max-width: 900px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; }}
th {{ background: #f8f8f8; text-align: left; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:12px; font-size:12px; color:#fff; }}
.ok {{ background:#16a34a; }}
.no {{ background:#dc2626; }}
small {{ color:#666; }}
</style>
</head>
<body>
  <h1>CI Report <small>({ts})</small></h1>
  <p>This report summarizes artifacts produced by the Infra Smoke & Tests job.</p>
  <table>
    <thead><tr><th>Artifact</th><th>Path</th><th>Status</th></tr></thead>
    <tbody>
      {''.join(row_html(name, path, ok) for name, path, ok in rows)}
    </tbody>
  </table>
  <p>If Coverage HTML is present, open <a href="coverage/htmlcov/index.html">coverage/htmlcov/index.html</a>.</p>
</body>
</html>
"""

out.write_text(html, encoding="utf-8")
print(str(out))
