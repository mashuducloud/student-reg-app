import os
import sys
import logging
from prometheus_client import Counter
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Prometheus metrics
env_var_counter = Counter(
    "env_vars_loaded_total",
    "Total number of environment variables successfully loaded",
    ["env_var"],  # ✅ fixed: valid label name
)
env_var_failures = Counter(
    "env_vars_missing_total",
    "Total number of missing environment variables",
    ["env_var"],  # ✅ fixed
)


def get_env_var(key: str) -> str:
    """
    Fetch an environment variable or exit if missing.
    """
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("get_env_var") as span:
        value = os.getenv(key)
        if not value:
            msg = f"❌ Missing required environment variable: {key}"
            log.error(msg, extra={"env_var": key})
            env_var_failures.labels(env_var=key).inc()  # ✅ use .labels().inc()
            span.set_status(Status(StatusCode.ERROR, msg))
            sys.exit(1)

        log.info(f"✅ Loaded environment variable: {key}")
        env_var_counter.labels(env_var=key).inc()  # ✅ use .labels().inc()
        span.set_status(Status(StatusCode.OK))
        return value


DB_CONFIG = {
    "host": get_env_var("DB_HOST"),
    "port": int(get_env_var("DB_PORT")),
    "database": get_env_var("DB_NAME"),
    "user": get_env_var("DB_USER"),
    "password": get_env_var("DB_PASSWORD"),
}
