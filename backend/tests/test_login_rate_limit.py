"""
Login lockout after repeated failures (app/core/rate_limit.py). The
_reset_login_limiter autouse fixture in conftest clears state between
tests so these don't strand the rest of the run.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import MAX_ATTEMPTS
from tests.conftest import unique


def test_repeated_failures_lock_the_account_then_valid_login_is_also_blocked(school):
    client = TestClient(app)
    bad_email = f"{unique('bruteforce')}@example.com"

    for i in range(MAX_ATTEMPTS):
        r = client.post("/api/v1/auth/login", json={"email": bad_email, "password": "wrong"})
        assert r.status_code == 401, f"attempt {i}: {r.status_code} {r.text}"

    # Next attempt for that email is locked out...
    locked = client.post("/api/v1/auth/login", json={"email": bad_email, "password": "wrong"})
    assert locked.status_code == 429, locked.text

    # ...and because the failures also count against this IP, even the
    # real admin credentials are refused from here until the window passes.
    admin = client.post("/api/v1/auth/login", json={
        "email": school["admin_email"], "password": school["admin_password"],
    })
    assert admin.status_code == 429, admin.text


def test_a_successful_login_clears_the_counter(school):
    client = TestClient(app)

    # A few failures, but under the threshold.
    for _ in range(MAX_ATTEMPTS - 2):
        client.post("/api/v1/auth/login", json={
            "email": school["admin_email"], "password": "wrong",
        })

    good = client.post("/api/v1/auth/login", json={
        "email": school["admin_email"], "password": school["admin_password"],
    })
    assert good.status_code == 200, good.text

    # Counter was cleared, so a fresh run of failures doesn't immediately trip.
    r = client.post("/api/v1/auth/login", json={
        "email": school["admin_email"], "password": "wrong",
    })
    assert r.status_code == 401, r.text
