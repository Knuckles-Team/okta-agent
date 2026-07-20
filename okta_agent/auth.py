"""CONCEPT:OK-OS.identity.okta Okta credentials loader and client builder.

Builds an authenticated :class:`okta_agent.api_client.Api` from the
environment. Two auth modes (in precedence order):

1. **SSWS API token** — ``OKTA_API_TOKEN``
   (https://developer.okta.com/docs/guides/create-an-api-token/main/)
2. **OAuth2 private-key-JWT** for Okta API scopes against the org
   authorization server — ``OKTA_CLIENT_ID`` + ``OKTA_PRIVATE_KEY`` (PEM
   string) or ``OKTA_PRIVATE_KEY_FILE`` (PEM path), scopes from
   ``OKTA_SCOPES`` (space-separated)
   (https://developer.okta.com/docs/guides/implement-oauth-for-okta/main/)

Other knobs: ``OKTA_ORG_URL`` (e.g. ``https://acme.okta.com``),
``OKTA_TLS_PROFILE`` / ``OKTA_TLS_PROFILE_REF``, ``OKTA_MAX_RETRIES`` and
``OKTA_BACKOFF_CAP_SECONDS``
(429 backoff), and ``OKTA_ALLOW_DESTRUCTIVE`` (CONCEPT:OK-OS.identity.default — default
gate for destructive tool actions, see :mod:`okta_agent.mcp`).
"""

import os

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting
from agent_utilities.core.transport_security import resolve_configured_tls_profile

from okta_agent.api.api_client_base import (
    DEFAULT_BACKOFF_CAP,
    DEFAULT_MAX_RETRIES,
)
from okta_agent.api.credentials import NoCredential, PrivateKeyJwt, SswsToken
from okta_agent.api_client import Api

logger = get_logger(__name__)

DEFAULT_SCOPES = "okta.users.read okta.groups.read okta.apps.read"


def _load_private_key() -> str | None:
    """Read the private key from OKTA_PRIVATE_KEY or OKTA_PRIVATE_KEY_FILE."""
    pem = setting("OKTA_PRIVATE_KEY", "")
    if pem:
        return pem
    path = setting("OKTA_PRIVATE_KEY_FILE", "")
    if path and os.path.exists(path):
        with open(path) as handle:
            return handle.read()
    return None


def get_client() -> Api:
    """Get an authenticated Okta Management API client from the environment."""
    org_url = setting("OKTA_ORG_URL", "") or setting("OKTA_AGENT_BASE_URL", "")
    if not org_url:
        # Default fallback for testing
        org_url = "https://localhost"

    tls_profile = resolve_configured_tls_profile(
        "okta",
        profile_name=setting("OKTA_TLS_PROFILE", "") or None,
        profile_ref=setting("OKTA_TLS_PROFILE_REF", "") or None,
    )
    max_retries = setting("OKTA_MAX_RETRIES", DEFAULT_MAX_RETRIES)
    backoff_cap = setting("OKTA_BACKOFF_CAP_SECONDS", DEFAULT_BACKOFF_CAP)

    api_token = setting("OKTA_API_TOKEN", "")
    client_id = setting("OKTA_CLIENT_ID", "")
    private_key = _load_private_key()

    credential: SswsToken | PrivateKeyJwt | NoCredential
    if api_token:
        credential = SswsToken(api_token)
    elif client_id and private_key:
        credential = PrivateKeyJwt(
            org_url=org_url,
            client_id=client_id,
            private_key_pem=private_key,
            scopes=setting("OKTA_SCOPES", DEFAULT_SCOPES).split(),
            kid=setting("OKTA_KEY_ID", "") or None,
            tls_profile=tls_profile,
        )
    else:
        logger.warning(
            "No Okta credentials configured (OKTA_API_TOKEN or "
            "OKTA_CLIENT_ID + OKTA_PRIVATE_KEY[_FILE]); requests will be "
            "unauthenticated."
        )
        credential = NoCredential()

    return Api(
        org_url=org_url,
        credential=credential,
        tls_profile=tls_profile,
        max_retries=max_retries,
        backoff_cap=backoff_cap,
    )


def allow_destructive_default() -> bool:
    """CONCEPT:OK-OS.identity.default Org-wide default for the destructive-action gate."""
    return setting("OKTA_ALLOW_DESTRUCTIVE", False)
