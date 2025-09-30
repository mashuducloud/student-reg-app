#!/usr/bin/env python3
import json, sys, urllib.request

URL = "http://localhost:9091/api/v1/targets?state=active"
REQUIRED = {"prometheus", "student-app", "otel-collector"}

with urllib.request.urlopen(URL, timeout=20) as r:
    data = json.load(r)

jobs = {t["labels"].get("job") for t in data["data"].get("activeTargets", [])}
missing = REQUIRED - jobs
if missing:
    print(f"Missing Prometheus targets: {sorted(missing)}", file=sys.stderr)
    sys.exit(1)

print("Prometheus targets OK:", ", ".join(sorted(jobs)))
