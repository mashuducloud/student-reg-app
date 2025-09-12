import os
import sys
import logging
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
meter = metrics.get_meter(__name__)

# Metrics for monitoring env var loading
env_var_counter = meter.create_counter("env_vars_loaded_total")
env_var_failures = meter.create_counter("env_vars_missing_total")

def get_env_var(key: str) -> str:
    """Fetch required environment variables or exit if missing."""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_env_var") as span:
        value = os.getenv(key)
        if not value:
            msg = f"❌ Missing required environment variable: {key}"
            log.error(msg, extra={"env_var": key})
            env_var_failures.add(1, {"env.var": key})
            span.set_status(Status(StatusCode.ERROR, msg))
            sys.exit(1)

        log.info(f"✅ Loaded environment variable: {key}")
        env_var_counter.add(1, {"env.var": key})
        span.set_status(Status(StatusCode.OK))
        return value

# Centralized DB configuration
DB_CONFIG = {
    'host': get_env_var('DB_HOST'),
    'port': int(get_env_var('DB_PORT')),
    'database': get_env_var('DB_NAME'),
    'user': get_env_var('DB_USER'),
    'password': get_env_var('DB_PASSWORD'),
}
