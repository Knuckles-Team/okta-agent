"""CONCEPT:OK-OS.identity.okta Okta credential strategies — SSWS token and OAuth2 private-key-JWT.

Two authentication modes against an Okta org:

- ``SswsToken`` — a static Okta API token sent as ``Authorization: SSWS <token>``.
  https://developer.okta.com/docs/guides/create-an-api-token/main/
- ``PrivateKeyJwt`` — OAuth2 client-credentials against the **org authorization
  server** (``{orgUrl}/oauth2/v1/token``) using a ``private_key_jwt`` client
  assertion (RS256), exchanging it for a Bearer access token scoped to Okta API
  scopes (``okta.users.read`` etc.).
  https://developer.okta.com/docs/guides/implement-oauth-for-okta/main/

Every credential exposes ``headers()`` (per-request auth headers) and
``secrets()`` (sensitive strings that must be redacted from logs and error
messages — see :mod:`okta_agent.api.api_client_base`).
"""

import time
import uuid

import httpx
import jwt
from agent_utilities.base_utilities import get_logger
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_configured_tls_profile,
)

logger = get_logger(__name__)

CLIENT_ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
#: Seconds before real expiry at which a cached access token is refreshed.
TOKEN_REFRESH_LEEWAY = 60
#: Lifetime of the signed client assertion (Okta allows up to 1 hour).
ASSERTION_LIFETIME = 300


class SswsToken:
    """Static Okta API token credential (``Authorization: SSWS <token>``)."""

    def __init__(self, token: str):
        self.token = token

    def headers(self) -> dict[str, str]:
        """Auth headers for one request."""
        return {"Authorization": f"SSWS {self.token}"}

    def secrets(self) -> list[str]:
        """Sensitive values to redact from logs/errors."""
        return [self.token] if self.token else []


class NoCredential:
    """Anonymous credential (local testing only — Okta will reject calls)."""

    def headers(self) -> dict[str, str]:
        """No auth headers."""
        return {}

    def secrets(self) -> list[str]:
        """Nothing to redact."""
        return []


class PrivateKeyJwt:
    """OAuth2 ``private_key_jwt`` client-credentials against the org auth server.

    Mints an RS256-signed JWT client assertion (``iss``/``sub`` = client_id,
    ``aud`` = the org token endpoint), exchanges it for an access token at
    ``{org_url}/oauth2/v1/token``, caches the token, and refreshes it
    ``TOKEN_REFRESH_LEEWAY`` seconds before expiry.

    Token endpoint reference:
    https://developer.okta.com/docs/reference/api/oidc/#token
    """

    def __init__(
        self,
        org_url: str,
        client_id: str,
        private_key_pem: str,
        scopes: list[str],
        kid: str | None = None,
        tls_profile: ResolvedTLSProfile | None = None,
        transport: httpx.BaseTransport | None = None,
    ):
        self.org_url = org_url.rstrip("/")
        self.client_id = client_id
        self.private_key_pem = private_key_pem
        self.scopes = scopes
        self.kid = kid
        self._access_token: str | None = None
        self._expires_at: float = 0.0
        self.tls_profile = tls_profile or resolve_configured_tls_profile("okta")
        self._http = httpx.Client(
            transport=transport,
            timeout=30.0,
            **self.tls_profile.httpx_kwargs(),
        )

    @property
    def token_url(self) -> str:
        """Org authorization server token endpoint."""
        return f"{self.org_url}/oauth2/v1/token"

    def _build_assertion(self) -> str:
        """Sign the ``private_key_jwt`` client assertion (RS256)."""
        now = int(time.time())
        claims = {
            "iss": self.client_id,
            "sub": self.client_id,
            "aud": self.token_url,
            "iat": now,
            "exp": now + ASSERTION_LIFETIME,
            "jti": uuid.uuid4().hex,
        }
        headers = {"kid": self.kid} if self.kid else None
        return jwt.encode(
            claims, self.private_key_pem, algorithm="RS256", headers=headers
        )

    def _fetch_token(self) -> None:
        """Exchange a fresh client assertion for an access token."""
        response = self._http.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "scope": " ".join(self.scopes),
                "client_assertion_type": CLIENT_ASSERTION_TYPE,
                "client_assertion": self._build_assertion(),
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Okta token endpoint returned {response.status_code} "
                f"({response.json().get('error', 'unknown_error') if _is_json(response) else 'non-JSON body'})"
            )
        body = response.json()
        self._access_token = body["access_token"]
        self._expires_at = time.time() + float(body.get("expires_in", 3600))
        logger.debug("Minted Okta access token for scopes: %s", " ".join(self.scopes))

    def headers(self) -> dict[str, str]:
        """Auth headers for one request, refreshing the token when stale."""
        if (
            not self._access_token
            or time.time() >= self._expires_at - TOKEN_REFRESH_LEEWAY
        ):
            self._fetch_token()
        return {"Authorization": f"Bearer {self._access_token}"}

    def secrets(self) -> list[str]:
        """Sensitive values to redact from logs/errors."""
        out = [self.private_key_pem]
        if self._access_token:
            out.append(self._access_token)
        return out


def _is_json(response: httpx.Response) -> bool:
    """True when the response body parses as JSON."""
    try:
        response.json()
        return True
    except Exception:
        return False


OktaCredential = SswsToken | PrivateKeyJwt | NoCredential
