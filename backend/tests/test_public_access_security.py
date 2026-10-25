from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import pytest

from app.config import Settings, get_cors_origins, settings, validate_production_settings
from app.security.auth import (
    generate_portal_secret,
    hash_portal_secret,
    require_staff_access,
    verify_portal_secret,
)
from app.api.upload import router as upload_router


def test_portal_secret_is_random_and_only_hash_is_persisted():
    first = generate_portal_secret()
    second = generate_portal_secret()

    assert first != second
    assert len(first) >= 40
    digest = hash_portal_secret(first)
    assert digest != first
    assert verify_portal_secret(first, digest)
    assert not verify_portal_secret(second, digest)


def test_staff_endpoint_requires_proxy_secret_and_authenticated_identity(monkeypatch):
    monkeypatch.setattr(settings, "STAFF_AUTH_DISABLED", False)
    monkeypatch.setattr(settings, "STAFF_PROXY_SHARED_SECRET", "proxy-secret-for-test")
    app = FastAPI()

    @app.get("/staff")
    def staff_endpoint(actor=Depends(require_staff_access)):
        return {"actor": actor}

    with TestClient(app) as client:
        assert client.get("/staff").status_code == 401
        assert client.get(
            "/staff", headers={"X-ClaimGuard-Proxy-Token": "wrong", "X-Authenticated-User": "staff@example.test"}
        ).status_code == 401
        assert client.get(
            "/staff", headers={"X-ClaimGuard-Proxy-Token": "proxy-secret-for-test"}
        ).status_code == 401
        assert client.get(
            "/staff",
            headers={
                "X-ClaimGuard-Proxy-Token": "proxy-secret-for-test",
                "X-Authenticated-User": "staff@example.test",
                "X-Authenticated-Groups": "patients",
            },
        ).status_code == 403

        response = client.get(
            "/staff",
            headers={
                "X-ClaimGuard-Proxy-Token": "proxy-secret-for-test",
                "X-Authenticated-User": "staff@example.test",
                "X-Authenticated-Groups": "patients, claimguard-staff",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"actor": "staff@example.test"}


def test_staff_endpoint_fails_closed_when_proxy_is_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "STAFF_AUTH_DISABLED", False)
    monkeypatch.setattr(settings, "STAFF_PROXY_SHARED_SECRET", None)
    app = FastAPI()

    @app.get("/staff")
    def staff_endpoint(actor=Depends(require_staff_access)):
        return {"actor": actor}

    with TestClient(app) as client:
        response = client.get(
            "/staff",
            headers={
                "X-ClaimGuard-Proxy-Token": "anything",
                "X-Authenticated-User": "staff@example.test",
            },
        )
    assert response.status_code == 503


def test_real_staff_router_rejects_direct_origin_header_spoofing(monkeypatch):
    monkeypatch.setattr(settings, "STAFF_AUTH_DISABLED", False)
    monkeypatch.setattr(settings, "STAFF_PROXY_SHARED_SECRET", "proxy-secret-for-test")
    app = FastAPI()
    app.include_router(upload_router)

    with TestClient(app) as client:
        response = client.get(
            "/api/claims",
            headers={
                "X-Authenticated-User": "attacker@example.test",
                "X-Authenticated-Groups": "claimguard-staff",
            },
        )
    assert response.status_code == 401


def test_production_configuration_rejects_insecure_or_incomplete_settings():
    config = Settings(
        APP_ENV="production",
        DEBUG=True,
        SECRET_KEY="default_unsafe_secret_key_for_dev_only",
        DATABASE_URL="sqlite+aiosqlite:///./claimguard.db",
        STAFF_PROXY_SHARED_SECRET=None,
        STAFF_AUTH_DISABLED=True,
        CORS_ALLOWED_ORIGINS="*",
        VLM_PROVIDER="openai",
        OPENAI_API_KEY="replace-with-key",
    )

    with pytest.raises(RuntimeError, match="Invalid production configuration"):
        validate_production_settings(config)


def test_production_configuration_accepts_explicit_secure_settings():
    config = Settings(
        APP_ENV="production",
        DEBUG=False,
        SECRET_KEY="s" * 48,
        DATABASE_URL="postgresql+asyncpg://user:password@localhost/claimguard",
        STAFF_PROXY_SHARED_SECRET="p" * 48,
        STAFF_AUTH_DISABLED=False,
        CORS_ALLOWED_ORIGINS="https://portal.example.test",
        UPLOAD_DIR="/var/data/uploads",
        VLM_PROVIDER="openai",
        OPENAI_API_KEY="valid-provider-key",
    )

    validate_production_settings(config)


def test_cors_origins_are_explicit_and_whitespace_is_removed():
    config = Settings(CORS_ALLOWED_ORIGINS=" https://portal.example.test, https://staff.example.test ")
    assert get_cors_origins(config) == [
        "https://portal.example.test",
        "https://staff.example.test",
    ]
