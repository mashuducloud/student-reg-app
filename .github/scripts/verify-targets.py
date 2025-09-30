#!/usr/bin/env python3
import sys, json
from urllib.request import urlopen, Request
from urllib.error import URLError

PROM_URL = "http://localhost:9091/api/v1/targets?state=active"
REQUIRED = {"prometheus", "student-app", "otel-collector"}

def fetch(url, timeout=10):
    req = Request(url, headers={"User-Agent": "ci-verify/1.0"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def main():
    try:
        raw = fetch(PROM_URL, timeout=20)
    except URLError as e:
        print(f"ERROR: cannot reach Prometheus API at {PROM_URL}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
        targets = data["data"]["activeTargets"]
    except Exception as e:
        print("ERROR: bad JSON from Prometheus:", e, file=sys.stderr)
        print(raw[:500], file=sys.stderr)
        sys.exit(1)

    jobs = {t.get("labels", {}).get("job") for t in targets}
    missing = REQUIRED - jobs
    print("Active jobs:", sorted(jobs))
    if missing:
        print("Missing jobs:", sorted(missing), file=sys.stderr)
        sys.exit(1)

    print("Prometheus targets OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
