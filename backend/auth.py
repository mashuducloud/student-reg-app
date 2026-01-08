# auth.py
import logging
import os
from functools import wraps

import jwt  # PyJWT
import requests
from flask import current_app, jsonify, request
from opentelemetry.trace import get_current_span

log = logging.getLogger(__name__)

TENANT_ID = os.getenv("ENTRA_TENANT_ID", "")
API_CLIENT_ID = os.getenv("ENTRA_API_CLIENT_ID", "")
EXPECTED_SCOPE = os.getenv("ENTRA_EXPECTED_SCOPE", "access_as_user")

# Optional explicit audience override, e.g. "api://<API_CLIENT_ID>"
EXPLICIT_AUDIENCE = os.getenv("ENTRA_API_AUDIENCE", "").strip()

if not TENANT_ID or not API_CLIENT_ID:
    print("[auth] WARNING: ENTRA_TENANT_ID or ENTRA_API_CLIENT_ID not set. JWT validation may fail.")

# Discover OpenID config (v2 endpoint)
OIDC_CONFIG_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"

try:
    oidc_config = requests.get(OIDC_CONFIG_URL, timeout=5).json()
    ISSUER_V2 = oidc_config.get("issuer")  # e.g. https://login.microsoftonline.com/<tid>/v2.0
    JWKS_URI = oidc_config.get("jwks_uri")
except Exception as e:
    print(f"[auth] Failed to load OIDC config: {e}")
    ISSUER_V2 = None
    JWKS_URI = None

# v1 style issuer (matches what your token shows: sts.windows.net/tenant/)
ISSUER_V1 = f"https://sts.windows.net/{TENANT_ID}/" if TENANT_ID else None

jwks_client = jwt.PyJWKClient(JWKS_URI) if JWKS_URI else None


def _build_expected_audiences() -> set:
    """
    Build the set of accepted audience values.

    Your token currently has:
      aud: "api://<API_CLIENT_ID>"

    So we accept:
      - API_CLIENT_ID (bare GUID)
      - api://API_CLIENT_ID
      - ENTRA_API_AUDIENCE env override, if set
    """
    expected = set()

    if API_CLIENT_ID:
        expected.add(API_CLIENT_ID)
        expected.add(f"api://{API_CLIENT_ID}")

    if EXPLICIT_AUDIENCE:
        expected.add(EXPLICIT_AUDIENCE)

    return expected


def _build_expected_issuers() -> set:
    """
    Build the set of accepted issuer values.

    Your token currently has:
      iss: "https://sts.windows.net/<TENANT_ID>/"

    OpenID config gives:
      issuer: "https://login.microsoftonline.com/<TENANT_ID>/v2.0"

    We accept both.
    """
    expected = set()
    if ISSUER_V2:
        expected.add(ISSUER_V2)
    if ISSUER_V1:
        expected.add(ISSUER_V1)
    return expected


def requires_auth(f):
    """
    Strict JWT validation decorator for Entra ID access tokens.

    This version:
      - ✅ Validates signature via JWKS
      - ✅ Validates issuer (v1 & v2 forms)
      - ✅ Validates audience (GUID and api://GUID forms, plus optional override)
      - ✅ Validates expiry
      - ✅ Enforces EXPECTED_SCOPE in 'scp'
      - ✅ Adds auth.* attributes to the current span
      - ✅ Logs a structured "JWT validated" with key claims

      Additionally:
      - ✅ Allows bypassing auth when Flask config BYPASS_AUTH=True (used in tests)
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        span = get_current_span()

        # 🔓 Bypass auth when explicitly enabled (e.g. tests)
        try:
            if current_app.config.get("BYPASS_AUTH", False):
                span.add_event("auth_bypassed", {"reason": "BYPASS_AUTH"})
                return f(*args, **kwargs)
        except RuntimeError:
            # No app context available; ignore and proceed with normal auth
            pass

        auth_header = request.headers.get("Authorization", None)

        if not auth_header or not auth_header.startswith("Bearer "):
            span.add_event("auth_missing_or_invalid_header")
            return jsonify({"error": "Authorization header missing"}), 401

        token = auth_header.split(" ", 1)[1]

        if not jwks_client:
            span.add_event("auth_config_not_loaded")
            return jsonify({"error": "Auth not configured properly"}), 500

        try:
            # 1) Signature + expiry validation
            signing_key = jwks_client.get_signing_key_from_jwt(token).key

            # We disable built-in iss/aud verification and do it ourselves
            decoded = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={
                    "verify_exp": True,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )

            token_iss = decoded.get("iss", "")
            token_aud = decoded.get("aud", "")
            token_scp = decoded.get("scp", "")
            token_oid = decoded.get("oid", "")
            token_upn = decoded.get("preferred_username") or decoded.get("email") or decoded.get("unique_name", "")
            token_tid = decoded.get("tid", "")

            # 2) Issuer validation (v1 + v2 allowed)
            expected_issuers = _build_expected_issuers()
            if expected_issuers and token_iss not in expected_issuers:
                span.add_event(
                    "auth_invalid_issuer",
                    {
                        "iss": token_iss,
                        "expected": list(expected_issuers),
                    },
                )
                log.warning(
                    "JWT invalid issuer",
                    extra={
                        "jwt.iss": token_iss,
                        "jwt.expected_issuers": list(expected_issuers),
                    },
                )
                return jsonify({"error": "Invalid token: invalid issuer"}), 401

            # 3) Audience validation (GUID vs api://GUID)
            expected_audiences = _build_expected_audiences()
            if expected_audiences and token_aud not in expected_audiences:
                span.add_event(
                    "auth_invalid_audience",
                    {
                        "aud": token_aud,
                        "expected": list(expected_audiences),
                    },
                )
                log.warning(
                    "JWT invalid audience",
                    extra={
                        "jwt.aud": token_aud,
                        "jwt.expected_audiences": list(expected_audiences),
                    },
                )
                return jsonify({"error": "Invalid token: invalid audience"}), 401

            # 4) Trace attributes (OpenTelemetry)
            span.set_attribute("auth.iss", token_iss)
            span.set_attribute("auth.aud", token_aud)
            span.set_attribute("auth.scopes", token_scp)
            span.set_attribute("auth.oid", token_oid)
            span.set_attribute("auth.user", token_upn)
            span.set_attribute("auth.tenant", token_tid)

            span.add_event(
                "auth_token_claims",
                {
                    "iss": token_iss,
                    "aud": token_aud,
                    "scp": token_scp,
                    "oid": token_oid,
                    "preferred_username": token_upn,
                    "tid": token_tid,
                },
            )

            # 5) Structured log (no raw token)
            log.info(
                "JWT validated",
                extra={
                    "jwt.iss": token_iss,
                    "jwt.aud": token_aud,
                    "jwt.scp": token_scp,
                    "jwt.oid": token_oid,
                    "jwt.preferred_username": token_upn,
                    "jwt.tid": token_tid,
                },
            )

            # 6) Scope enforcement
            scopes_raw = token_scp
            scopes = scopes_raw.split() if isinstance(scopes_raw, str) else []

            if EXPECTED_SCOPE and EXPECTED_SCOPE not in scopes:
                span.add_event(
                    "auth_insufficient_scope",
                    {"scp": scopes_raw, "expected": EXPECTED_SCOPE},
                )
                return jsonify({"error": "Insufficient scope"}), 403

            # 7) Attach decoded token to request for downstream use
            request.jwt_payload = decoded
            span.add_event("auth_success", {"subject": decoded.get("sub", "")})

        except Exception as ex:
            span.add_event("auth_failed", {"error": str(ex)})
            log.warning("JWT validation failed", extra={"auth.error": str(ex)})
            return jsonify({"error": f"Invalid token: {str(ex)}"}), 401

        return f(*args, **kwargs)

    return wrapper
