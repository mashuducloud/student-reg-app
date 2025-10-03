import os
import time
import requests

BASE = os.getenv("APP_BASE_URL", "http://localhost:5000")
METRICS = os.getenv("METRICS_URL", "http://localhost:9100/metrics")

def wait_http(url, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=5)
            if r.ok:
                return True
        except Exception:
            pass
        time.sleep(2)
    raise AssertionError(f"Timeout waiting for {url}")

def test_health_ready():
    assert wait_http(f"{BASE}/health", 120)

def test_metrics_exposed():
    wait_http(METRICS, 120)
    r = requests.get(METRICS, timeout=5)
    assert r.status_code == 200
    assert "python_gc_objects_collected_total" in r.text or "process_start_time_seconds" in r.text
