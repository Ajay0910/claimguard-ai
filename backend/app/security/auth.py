import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request, status

from ..config import settings


def generate_portal_secret() -> str:
    """Create a 256-bit capability used to access one submitted claim."""
    return secrets.token_urlsafe(32)


def hash_portal_secret(secret: str) -> str:
    """Return the storage-safe SHA-256 digest of a high-entropy portal secret."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def verify_portal_secret(secret: str, stored_hash: str | None) -> bool:
    if not secret or not stored_hash:
        return False
    return hmac.compare_digest(hash_portal_secret(secret), stored_hash)


def require_staff_access(request: Request) -> str:
    """Accept only requests authenticated by the configured OIDC proxy."""
    if settings.APP_ENV.strip().lower() == "development" and settings.STAFF_AUTH_DISABLED:
        return request.headers.get("X-Authenticated-User") or "local-development"

    expected_proxy_secret = settings.STAFF_PROXY_SHARED_SECRET
    if not expected_proxy_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Staff access is unavailable because the trusted proxy is not configured.",
        )

    supplied_proxy_secret = request.headers.get("X-ClaimGuard-Proxy-Token", "")
    identity = request.headers.get("X-Authenticated-User", "").strip()
    groups = {
        group.strip()
        for group in request.headers.get("X-Authenticated-Groups", "").split(",")
        if group.strip()
    }
    if not hmac.compare_digest(supplied_proxy_secret, expected_proxy_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff authentication required.")
    if not identity or len(identity) > 254 or any(ord(char) < 32 for char in identity):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff identity is missing or invalid.")
    if settings.STAFF_REQUIRED_GROUP not in groups:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role is required.")
    return identity
