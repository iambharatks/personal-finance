from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app import auth
from app.config import get_settings
from app.db import get_db
from app.schemas import AuthStatus, LoginIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def me(request: Request) -> AuthStatus:
    settings = get_settings()
    return AuthStatus(
        authenticated=not settings.auth_enabled
        or auth.is_valid_session(request.cookies.get(auth.COOKIE_NAME)),
        auth_required=settings.auth_enabled,
    )


@router.post("/login")
def login(
    body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)
) -> AuthStatus:
    settings = get_settings()
    if not settings.auth_enabled:
        return AuthStatus(authenticated=True, auth_required=False)

    ip = auth.client_ip(request)
    if auth.is_locked_out(db, ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in 15 minutes.")

    ok = auth.verify_password(body.password, settings.app_password_hash)
    auth.record_attempt(db, ip, ok)
    if not ok:
        raise HTTPException(status_code=401, detail="Wrong password")

    response.set_cookie(
        auth.COOKIE_NAME,
        auth.new_session_token(),
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        path="/",
    )
    return AuthStatus(authenticated=True, auth_required=True)


@router.post("/logout")
def logout(response: Response) -> AuthStatus:
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return AuthStatus(authenticated=False, auth_required=get_settings().auth_enabled)
