"""
Authentication & Authorization — JWT validation, RBAC, and API key management.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Data models ──────────────────────────────────────────────────────────────

class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    MANAGE_MODELS = "manage_models"
    VIEW_COSTS = "view_costs"
    MANAGE_QUOTAS = "manage_quotas"


@dataclass
class Role:
    name: str
    permissions: set[Permission] = field(default_factory=set)
    description: str = ""


@dataclass
class User:
    user_id: str
    roles: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthResult:
    authenticated: bool
    user: User | None = None
    error: str = ""
    expires_at: float | None = None


# ── JWT Validator ────────────────────────────────────────────────────────────

class JWTValidator:
    """Validate JWT tokens (symmetric HS256 or via external JWKS)."""

    def __init__(
        self,
        *,
        secret: str | None = None,
        jwks_url: str | None = None,
        audience: str | None = None,
        issuer: str | None = None,
    ) -> None:
        self.secret = secret
        self.jwks_url = jwks_url
        self.audience = audience
        self.issuer = issuer

    def validate(self, token: str) -> AuthResult:
        """Validate a JWT token and return an AuthResult.

        For production, use PyJWT or python-jose.  This implementation
        provides the structural pattern; actual cryptographic verification
        is delegated to dedicated libraries.
        """
        try:
            import jwt as pyjwt  # type: ignore[import-untyped]

            options: dict[str, Any] = {}
            kwargs: dict[str, Any] = {"algorithms": ["HS256", "RS256"]}
            if self.audience:
                kwargs["audience"] = self.audience
            if self.issuer:
                kwargs["issuer"] = self.issuer
            if self.secret:
                payload = pyjwt.decode(token, self.secret, **kwargs)
            elif self.jwks_url:
                jwks_client = pyjwt.PyJWKClient(self.jwks_url)
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = pyjwt.decode(token, signing_key.key, **kwargs)
            else:
                return AuthResult(authenticated=False, error="No secret or JWKS URL configured")

            user = User(
                user_id=payload.get("sub", ""),
                roles=payload.get("roles", []),
                metadata=payload,
            )
            return AuthResult(
                authenticated=True,
                user=user,
                expires_at=payload.get("exp"),
            )

        except ImportError:
            return AuthResult(authenticated=False, error="PyJWT not installed")
        except Exception as exc:
            return AuthResult(authenticated=False, error=str(exc))


# ── API Key Manager ──────────────────────────────────────────────────────────

class APIKeyManager:
    """Manage API keys for service-level authentication."""

    def __init__(self) -> None:
        self._keys: dict[str, _KeyRecord] = {}

    def register(self, key: str, *, roles: list[str] | None = None, expires_at: float | None = None) -> str:
        key_hash = self._hash(key)
        self._keys[key_hash] = _KeyRecord(roles=roles or [], expires_at=expires_at)
        return key_hash

    def validate(self, key: str) -> AuthResult:
        key_hash = self._hash(key)
        record = self._keys.get(key_hash)
        if record is None:
            return AuthResult(authenticated=False, error="Invalid API key")
        if record.expires_at and time.time() > record.expires_at:
            return AuthResult(authenticated=False, error="API key expired")
        user = User(user_id=f"key:{key_hash[:8]}", roles=record.roles)
        return AuthResult(authenticated=True, user=user, expires_at=record.expires_at)

    def revoke(self, key: str) -> bool:
        key_hash = self._hash(key)
        return self._keys.pop(key_hash, None) is not None

    @staticmethod
    def _hash(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()


# ── RBAC ─────────────────────────────────────────────────────────────────────

class RBAC:
    """Role-Based Access Control."""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}

    def define_role(self, name: str, permissions: set[Permission], description: str = "") -> Role:
        role = Role(name=name, permissions=permissions, description=description)
        self._roles[name] = role
        return role

    def has_permission(self, user: User, permission: Permission) -> bool:
        for role_name in user.roles:
            role = self._roles.get(role_name)
            if role and permission in role.permissions:
                return True
        return False

    def get_permissions(self, user: User) -> set[Permission]:
        perms: set[Permission] = set()
        for role_name in user.roles:
            role = self._roles.get(role_name)
            if role:
                perms |= role.permissions
        return perms

    def require(self, user: User, permission: Permission) -> None:
        if not self.has_permission(user, permission):
            raise PermissionError(
                f"User {user.user_id} lacks permission: {permission.value}"
            )


# ── Auth Manager ─────────────────────────────────────────────────────────────

class AuthManager:
    """Unified authentication manager combining JWT + API key + RBAC."""

    def __init__(
        self,
        *,
        jwt_secret: str | None = None,
        jwks_url: str | None = None,
    ) -> None:
        self.jwt = JWTValidator(secret=jwt_secret, jwks_url=jwks_url)
        self.api_keys = APIKeyManager()
        self.rbac = RBAC()

    def authenticate(self, *, token: str | None = None, api_key: str | None = None) -> AuthResult:
        if token:
            return self.jwt.validate(token)
        if api_key:
            return self.api_keys.validate(api_key)
        return AuthResult(authenticated=False, error="No credentials provided")

    def authorize(self, user: User, permission: Permission) -> bool:
        return self.rbac.has_permission(user, permission)


# ── Internal ─────────────────────────────────────────────────────────────────

@dataclass
class _KeyRecord:
    roles: list[str]
    expires_at: float | None = None
