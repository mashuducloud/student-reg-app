#!/usr/bin/env python3
from datetime import datetime
html = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>CI Infra Report</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}
pre,code{background:#f6f8fa;padding:.25rem .5rem;border-radius:6px}
.section{margin:1.2rem 0}
h1{font-size:1.5rem} h2{font-size:1.1rem}
ul{line-height:1.5}
</style>
<h1>CI Infra Report</h1>
<p>Generated: {datetime.utcnow().isoformat()}Z</p>

<div class="section">
  <h2>What ran</h2>
  <ul>
    <li>Compose config sanity</li>
    <li>In-network health checks (Prometheus ⇄ App ⇄ OTEL)</li>
    <li>Prometheus active targets verification</li>
    <li>Integration tests (health + metrics)</li>
  </ul>
</div>

<div class="section">
  <h2>Quick links (local compose ports)</h2>
  <ul>
    <li>Prometheus: <code>http://localhost:9091</code></li>
    <li>Grafana: <code>http://localhost:3300</code></li>
    <li>Tempo: <code>http://localhost:3201</code></li>
    <li>App health: <code>http://localhost:5000/health</code></li>
  </ul>
</div>
</html>"""
open("ci-report.html","w",encoding="utf-8").write(html)
print("Wrote ci-report.html")
