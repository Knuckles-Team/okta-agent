"""CONCEPT:OKTA-1.2 Environment-driven client construction."""

import pytest

from okta_agent.api.credentials import NoCredential, PrivateKeyJwt, SswsToken
from okta_agent.auth import allow_destructive_default, get_client

# Assembled at runtime so secret scanners do not match a key-block literal.
FAKE_PEM = "-----BEGIN " + "PRIVATE KEY-----\nMIIfake\n-----END " + "PRIVATE KEY-----\n"


@pytest.mark.concept("OKTA-1.2")
class TestGetClient:
    def test_ssws_token_selected(self, monkeypatch):
        monkeypatch.setenv("OKTA_ORG_URL", "https://acme.okta.example.com")
        monkeypatch.setenv("OKTA_API_TOKEN", "00env-tok")
        client = get_client()
        assert isinstance(client.credential, SswsToken)
        assert client.credential.token == "00env-tok"
        assert client.org_url == "https://acme.okta.example.com"

    def test_ssws_takes_precedence_over_private_key(self, monkeypatch):
        monkeypatch.setenv("OKTA_API_TOKEN", "00env-tok")
        monkeypatch.setenv("OKTA_CLIENT_ID", "0oa1")
        monkeypatch.setenv("OKTA_PRIVATE_KEY", FAKE_PEM)
        assert isinstance(get_client().credential, SswsToken)

    def test_private_key_jwt_selected(self, monkeypatch):
        monkeypatch.setenv("OKTA_ORG_URL", "https://acme.okta.example.com")
        monkeypatch.setenv("OKTA_CLIENT_ID", "0oa1")
        monkeypatch.setenv("OKTA_PRIVATE_KEY", FAKE_PEM)
        monkeypatch.setenv("OKTA_SCOPES", "okta.logs.read")
        credential = get_client().credential
        assert isinstance(credential, PrivateKeyJwt)
        assert credential.client_id == "0oa1"
        assert credential.scopes == ["okta.logs.read"]

    def test_private_key_loaded_from_file(self, monkeypatch, tmp_path):
        key_file = tmp_path / "okta.pem"
        key_file.write_text(FAKE_PEM)
        monkeypatch.setenv("OKTA_CLIENT_ID", "0oa1")
        monkeypatch.setenv("OKTA_PRIVATE_KEY_FILE", str(key_file))
        credential = get_client().credential
        assert isinstance(credential, PrivateKeyJwt)
        assert credential.private_key_pem == FAKE_PEM

    def test_fallback_is_anonymous(self):
        assert isinstance(get_client().credential, NoCredential)

    def test_retry_and_backoff_knobs(self, monkeypatch):
        monkeypatch.setenv("OKTA_MAX_RETRIES", "5")
        monkeypatch.setenv("OKTA_BACKOFF_CAP_SECONDS", "12.5")
        client = get_client()
        assert client.max_retries == 5
        assert client.backoff_cap == 12.5

    def test_defaults(self):
        client = get_client()
        assert client.org_url == "https://localhost"
        assert client.max_retries == 2
        assert client.backoff_cap == 60.0


@pytest.mark.concept("OKTA-1.4")
class TestAllowDestructiveDefault:
    def test_blocked_by_default(self):
        assert allow_destructive_default() is False

    def test_env_enables(self, monkeypatch):
        monkeypatch.setenv("OKTA_ALLOW_DESTRUCTIVE", "True")
        assert allow_destructive_default() is True
