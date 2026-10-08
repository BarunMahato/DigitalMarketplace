"""Minimal HMAC-signed JWT helpers using only Python's standard library."""

import base64
import hashlib
import hmac
import json
import time
import uuid
 
from django.conf import settings


class InvalidToken(ValueError):
    """Raised when a token is malformed, incorrectly signed, or expired."""


def _b64encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value):
    try:
        raw = value.encode("ascii")
        return base64.urlsafe_b64decode(raw + b"=" * (-len(raw) % 4))
    except (ValueError, UnicodeEncodeError) as exc:
        raise InvalidToken("Malformed token encoding") from exc


def _secret():
    # Use Django's project secret unless a separate, strong JWT key is configured.
    return str(getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)).encode("utf-8")


def encode_token(user, token_type, lifetime_seconds):
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user.pk),
        "role": user.role,
        "token_type": token_type,
        "iat": now,
        "exp": now + int(lifetime_seconds),
        "jti": uuid.uuid4().hex,
    }
    head = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{head}.{body}".encode("ascii")
    signature = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    return f"{head}.{body}.{_b64encode(signature)}"


def decode_token(token, expected_type):
    try:
        head, body, signature = token.split(".")
        signing_input = f"{head}.{body}".encode("ascii")
        expected_signature = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, _b64decode(signature)):
            raise InvalidToken("Invalid token signature")
        header = json.loads(_b64decode(head))
        payload = json.loads(_b64decode(body))
    except InvalidToken:
        raise
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise InvalidToken("Malformed token") from exc

    if not isinstance(header, dict) or header.get("alg") != "HS256":
        raise InvalidToken("Unsupported token algorithm")
    if not isinstance(payload, dict) or payload.get("token_type") != expected_type:
        raise InvalidToken("Wrong token type")
    if not payload.get("sub") or not isinstance(payload.get("exp"), int):
        raise InvalidToken("Required token claims are missing")
    if payload["exp"] <= int(time.time()):
        raise InvalidToken("Token has expired")
    return payload


def get_token_pair(user):
    return {
        "access": encode_token(
            user, "access", settings.JWT_ACCESS_EXPIRY_MINUTES * 60
        ),
        "refresh": encode_token(
            user, "refresh", settings.JWT_REFRESH_EXPIRY_DAYS * 24 * 60 * 60
        ),
    }
