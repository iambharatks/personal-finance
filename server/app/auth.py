"""Single-user login: one password, one signed session cookie."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import LoginAttempt

COOKIE_NAME = "fin_session"

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1

LOCKOUT_WINDOW = timedelta(minutes=15)
MAX_FAILURES_PER_IP = 5
# Backstop against a distributed guesser; high enough that one stranger cannot lock the owner out.
MAX_FAILURES_GLOBAL = 20


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32
    )
    return f"scrypt:{_SCRYPT_N}:{_SCRYPT_R}:{_SCRYPT_P}:{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split(":")
        if scheme != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except ValueError:
        return False
    return hmac.compare_digest(actual, expected)


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret, salt="session")


def new_session_token() -> str:
    return _serializer().dumps({"v": 1})


def is_valid_session(token: str | None) -> bool:
    if not token:
        return False
    try:
        _serializer().loads(token, max_age=get_settings().session_days * 86400)
    except BadSignature:  # also covers SignatureExpired
        return False
    return True


def require_session(request: Request) -> None:
    """Dependency guarding every data route."""
    if not get_settings().auth_enabled:
        return  # local development without a password
    if not is_valid_session(request.cookies.get(COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="Not signed in")


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return request.client.host if request.client else "unknown"


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def is_locked_out(db: Session, ip: str) -> bool:
    since = _now() - LOCKOUT_WINDOW
    failed = select(func.count()).where(LoginAttempt.at >= since, LoginAttempt.ok.is_(False))
    from_ip = db.scalar(failed.where(LoginAttempt.ip == ip)) or 0
    overall = db.scalar(failed) or 0
    return from_ip >= MAX_FAILURES_PER_IP or overall >= MAX_FAILURES_GLOBAL


def record_attempt(db: Session, ip: str, ok: bool) -> None:
    db.execute(delete(LoginAttempt).where(LoginAttempt.at < _now() - timedelta(days=1)))
    db.add(LoginAttempt(ip=ip, at=_now(), ok=ok))
    db.commit()
