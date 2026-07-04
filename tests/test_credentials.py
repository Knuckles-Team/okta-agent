"""CONCEPT:OK-OS.identity.okta Auth header injection: SSWS token and OAuth2 private-key-JWT."""

import time
from typing import Any
from urllib.parse import parse_qs

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from okta_agent.api.credentials import (
    CLIENT_ASSERTION_TYPE,
    NoCredential,
    PrivateKeyJwt,
    SswsToken,
)
from tests.conftest import ORG_URL, TEST_TOKEN, json_response


@pytest.fixture(scope="module")
def rsa_keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


def make_pkjwt(private_pem, handler, **kwargs) -> PrivateKeyJwt:
    return PrivateKeyJwt(
        org_url=ORG_URL,
        client_id=kwargs.pop("client_id", "0oaclient1"),
        private_key_pem=private_pem,
        scopes=kwargs.pop("scopes", ["okta.users.read"]),
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


@pytest.mark.concept("OK-OS.identity.okta")
class TestSswsToken:
    def test_header_injection(self):
        assert SswsToken(TEST_TOKEN).headers() == {
            "Authorization": f"SSWS {TEST_TOKEN}"
        }

    def test_secrets_exposed_for_redaction(self):
        assert SswsToken(TEST_TOKEN).secrets() == [TEST_TOKEN]

    def test_empty_token_has_no_secrets(self):
        assert SswsToken("").secrets() == []

    def test_request_carries_ssws_header(self, make_api):
        seen = {}

        def handler(request):
            seen["auth"] = request.headers["Authorization"]
            return json_response({"id": "00o1"})

        make_api(handler).get_org()
        assert seen["auth"] == f"SSWS {TEST_TOKEN}"


@pytest.mark.concept("OK-OS.identity.okta")
class TestNoCredential:
    def test_no_headers_no_secrets(self):
        cred = NoCredential()
        assert cred.headers() == {}
        assert cred.secrets() == []


@pytest.mark.concept("OK-OS.identity.okta")
class TestPrivateKeyJwt:
    def test_token_request_shape_and_assertion_claims(self, rsa_keypair):
        private_pem, public_pem = rsa_keypair
        captured: dict[str, Any] = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["form"] = parse_qs(request.read().decode())
            return json_response({"access_token": "at-1", "expires_in": 3600})

        cred = make_pkjwt(private_pem, handler)
        headers = cred.headers()

        assert headers == {"Authorization": "Bearer at-1"}
        assert captured["url"] == f"{ORG_URL}/oauth2/v1/token"
        form = captured["form"]
        assert form["grant_type"] == ["client_credentials"]
        assert form["scope"] == ["okta.users.read"]
        assert form["client_assertion_type"] == [CLIENT_ASSERTION_TYPE]

        claims = jwt.decode(
            form["client_assertion"][0],
            public_pem,
            algorithms=["RS256"],
            audience=f"{ORG_URL}/oauth2/v1/token",
        )
        assert claims["iss"] == "0oaclient1"
        assert claims["sub"] == "0oaclient1"
        assert claims["exp"] > claims["iat"]
        assert claims["jti"]

    def test_kid_lands_in_assertion_header(self, rsa_keypair):
        private_pem, _ = rsa_keypair
        captured = {}

        def handler(request):
            captured["form"] = parse_qs(request.read().decode())
            return json_response({"access_token": "at-2", "expires_in": 3600})

        make_pkjwt(private_pem, handler, kid="kid-1").headers()
        header = jwt.get_unverified_header(captured["form"]["client_assertion"][0])
        assert header["kid"] == "kid-1"

    def test_token_cached_until_expiry(self, rsa_keypair):
        private_pem, _ = rsa_keypair
        calls = {"n": 0}

        def handler(request):
            calls["n"] += 1
            return json_response(
                {"access_token": f"at-{calls['n']}", "expires_in": 3600}
            )

        cred = make_pkjwt(private_pem, handler)
        assert cred.headers() == cred.headers()
        assert calls["n"] == 1

    def test_token_refreshed_when_stale(self, rsa_keypair):
        private_pem, _ = rsa_keypair
        calls = {"n": 0}

        def handler(request):
            calls["n"] += 1
            return json_response(
                {"access_token": f"at-{calls['n']}", "expires_in": 3600}
            )

        cred = make_pkjwt(private_pem, handler)
        cred.headers()
        cred._expires_at = time.time()  # force staleness
        assert cred.headers() == {"Authorization": "Bearer at-2"}
        assert calls["n"] == 2

    def test_token_endpoint_error_raises(self, rsa_keypair):
        private_pem, _ = rsa_keypair

        def handler(request):
            return json_response({"error": "invalid_client"}, status=401)

        with pytest.raises(RuntimeError, match="401"):
            make_pkjwt(private_pem, handler).headers()

    def test_secrets_include_key_and_access_token(self, rsa_keypair):
        private_pem, _ = rsa_keypair

        def handler(request):
            return json_response({"access_token": "at-9", "expires_in": 3600})

        cred = make_pkjwt(private_pem, handler)
        assert cred.secrets() == [private_pem]
        cred.headers()
        assert "at-9" in cred.secrets()
