"""Supabase Auth JWT verification (asymmetric signing keys, published as JWKS)."""

from __future__ import annotations

from typing import Protocol

import jwt


class AuthError(Exception):
    pass


class Verifier(Protocol):
    def user_id(self, token: str) -> str: ...


class SupabaseVerifier:
    """Verifies access tokens against ``<SUPABASE_URL>/auth/v1/.well-known/jwks.json``."""

    algorithms = ["ES256", "RS256"]

    def __init__(self, supabase_url: str, audience: str = "authenticated", jwks_client: jwt.PyJWKClient | None = None):
        if not supabase_url:
            raise ValueError("SUPABASE_URL is required to verify tokens")
        base = supabase_url.rstrip("/")
        self.issuer = f"{base}/auth/v1"
        self.audience = audience
        self.jwks = jwks_client or jwt.PyJWKClient(f"{self.issuer}/.well-known/jwks.json", cache_keys=True, lifespan=3600)

    def user_id(self, token: str) -> str:
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token, key.key, algorithms=self.algorithms, audience=self.audience, issuer=self.issuer,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthError(type(exc).__name__) from None
        return str(claims["sub"])
