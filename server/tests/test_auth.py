import pytest

from app import auth
from app.config import Settings

PROTECTED = [
    "/api/dashboard",
    "/api/transactions",
    "/api/accounts",
    "/api/categories",
    "/api/meta",
    "/api/charts/balance",
    "/api/charts/monthly-flows",
    "/api/charts/category-spend",
]


def test_password_hash_round_trip():
    stored = auth.hash_password("hunter2hunter2")
    assert auth.verify_password("hunter2hunter2", stored)
    assert not auth.verify_password("hunter2hunter3", stored)
    assert not auth.verify_password("hunter2hunter2", "not-a-hash")
    assert auth.hash_password("hunter2hunter2") != stored  # fresh salt each time


@pytest.mark.parametrize("path", PROTECTED)
def test_data_routes_need_a_session(client, with_password, path):
    assert client.get(path).status_code == 401


def test_edit_needs_a_session(client, with_password):
    assert client.patch("/api/transactions/1", json={"note": "x"}).status_code == 401


def test_health_is_open_and_marked_private(client, with_password):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "noindex" in response.headers["x-robots-tag"]


def test_login_logout(client, with_password):
    assert client.get("/api/auth/me").json() == {"authenticated": False, "auth_required": True}

    assert client.post("/api/auth/login", json={"password": "wrong"}).status_code == 401
    assert client.get("/api/dashboard").status_code == 401

    response = client.post("/api/auth/login", json={"password": with_password})
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert client.get("/api/dashboard").status_code == 200
    assert client.get("/api/auth/me").json()["authenticated"] is True

    client.post("/api/auth/logout")
    assert client.get("/api/dashboard").status_code == 401


def test_forged_or_stale_cookie_is_rejected(client, with_password):
    client.cookies.set(auth.COOKIE_NAME, "forged.token.value")
    assert client.get("/api/dashboard").status_code == 401

    # A token signed with a different secret is worthless.
    token = auth.new_session_token()
    auth.get_settings().session_secret = "t" * 40
    client.cookies.set(auth.COOKIE_NAME, token)
    assert client.get("/api/dashboard").status_code == 401


def test_lockout_after_five_wrong_passwords(client, with_password):
    for _ in range(auth.MAX_FAILURES_PER_IP):
        assert client.post("/api/auth/login", json={"password": "wrong"}).status_code == 401
    # Even the right password is refused while locked out.
    assert client.post("/api/auth/login", json={"password": with_password}).status_code == 429


def test_lockout_is_per_address(client, with_password):
    for _ in range(auth.MAX_FAILURES_PER_IP):
        client.post(
            "/api/auth/login", json={"password": "wrong"}, headers={"x-forwarded-for": "9.9.9.9"}
        )
    response = client.post(
        "/api/auth/login", json={"password": with_password}, headers={"x-forwarded-for": "1.1.1.1"}
    )
    assert response.status_code == 200


def test_production_refuses_to_start_without_a_login():
    with pytest.raises(RuntimeError, match="APP_PASSWORD_HASH"):
        Settings(app_env="production", app_password_hash="").validate_for_startup()
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        Settings(
            app_env="production", app_password_hash="scrypt:x", session_secret="short"
        ).validate_for_startup()
    Settings(app_env="development", app_password_hash="").validate_for_startup()


def test_hosted_postgres_urls_are_normalised():
    url = Settings(database_url="postgres://u:p@host/db?sslmode=require").sqlalchemy_url
    assert url == "postgresql+psycopg://u:p@host/db?sslmode=require"
