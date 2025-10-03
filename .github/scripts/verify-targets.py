#!/usr/bin/env python3
import sys, json, urllib.request

URL = "http://localhost:9091/api/v1/targets?state=active"
required = {"prometheus", "student-app", "otel-collector"}

try:
    with urllib.request.urlopen(URL, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    jobs = {t["labels"].get("job") for t in data["data"]["activeTargets"]}
except Exception as e:
    print("Error querying Prometheus targets:", e, file=sys.stderr)
    sys.exit(1)

missing = required - jobs
if missing:
    print("Missing Prometheus targets:", ", ".join(sorted(missing)))
    sys.exit(1)

print("Prometheus targets OK:", ", ".join(sorted(jobs)))
