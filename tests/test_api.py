import pytest
from fastapi.testclient import TestClient

from backend.main import app

FORM_SLUGS = ['forgot-password-generic-1']
CONTACT_FIELDS = {'forgot-password-generic-1': [{'name': 'email', 'type': 'email', 'required': True, 'label': 'Email', 'maxlength': 255, 'options': []}]}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_unknown_form_is_404(client):
    assert client.post("/api/forms/does-not-exist", json={"a": "b"}).status_code == 404


def test_submissions_require_admin_token(client):
    assert client.get("/api/forms").status_code == 401
    assert client.get("/api/forms", headers={"X-Admin-Token": "test-admin-token"}).status_code == 200


@pytest.mark.skipif(not CONTACT_FIELDS, reason="site has no non-auth forms")
def test_valid_and_invalid_submission(client):
    slug, fields = next(iter(CONTACT_FIELDS.items()))
    payload = {f["name"]: ("user@example.com" if f["type"] == "email" else (f["options"][0] if f["type"] == "select" and f["options"] else "hello")) for f in fields}
    ok = client.post(f"/api/forms/{slug}", json=payload)
    assert ok.status_code == 200, ok.text
    required = [f for f in fields if f["required"]]
    if required:
        bad = dict(payload)
        bad.pop(required[0]["name"])
        assert client.post(f"/api/forms/{slug}", json=bad).status_code == 422
    rows = client.get("/api/forms", params={"slug": slug}, headers={"X-Admin-Token": "test-admin-token"}).json()
    assert rows and rows[0]["form_slug"] == slug


def test_register_login_me(client):
    reg = client.post("/api/auth/register", json={"email": "Tester@Example.com", "password": "correct-horse-1"})
    assert reg.status_code == 200, reg.text
    assert client.post("/api/auth/register", json={"email": "tester@example.com", "password": "correct-horse-1"}).status_code == 409
    assert client.post("/api/auth/login", json={"email": "tester@example.com", "password": "wrong-password"}).status_code == 401
    login = client.post("/api/auth/login", json={"email": "tester@example.com", "password": "correct-horse-1"})
    token = login.json()["token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["identity"] == "tester@example.com"
    assert client.get("/api/auth/me").status_code == 401


ADMIN = {"X-Admin-Token": "test-admin-token"}


def test_admin_requires_token(client):
    assert client.get("/api/admin/summary").status_code == 401
    assert client.get("/api/admin/summary", headers={"X-Admin-Token": "wrong"}).status_code == 401
    body = client.get("/api/admin/summary", headers=ADMIN).json()
    assert {"submissions", "users", "snapshots", "collections"} <= set(body)


def test_admin_page_served(client):
    r = client.get("/admin")
    assert r.status_code == 200 and "Admin panel" in r.text


def test_admin_user_management(client):
    created = client.post("/api/admin/users", json={"identity": "Ops@Example.com", "password": "long-enough-1"}, headers=ADMIN)
    assert created.status_code == 201, created.text
    uid = created.json()["id"]
    assert client.post("/api/admin/users", json={"identity": "ops@example.com", "password": "long-enough-1"}, headers=ADMIN).status_code == 409
    assert client.post("/api/admin/users", json={"identity": "x@y.zz", "password": "short"}, headers=ADMIN).status_code == 422
    assert client.post("/api/auth/login", json={"email": "ops@example.com", "password": "long-enough-1"}).status_code == 200
    assert client.post(f"/api/admin/users/{uid}/password", json={"password": "another-pass-2"}, headers=ADMIN).status_code == 204
    assert client.post("/api/auth/login", json={"email": "ops@example.com", "password": "long-enough-1"}).status_code == 401
    assert any(u["id"] == uid for u in client.get("/api/admin/users", headers=ADMIN).json())
    assert client.delete(f"/api/admin/users/{uid}", headers=ADMIN).status_code == 204
    assert client.delete(f"/api/admin/users/{uid}", headers=ADMIN).status_code == 404


def test_admin_submissions_crud(client):
    if not FORM_SLUGS:
        pytest.skip("no forms")
    slug = FORM_SLUGS[0]
    fields = CONTACT_FIELDS[slug]
    payload = {f["name"]: ("a@b.co" if f["type"] == "email" else "x") for f in fields}
    sid = client.post(f"/api/forms/{slug}", json=payload).json()["id"]
    assert any(r["id"] == sid for r in client.get("/api/admin/submissions", headers=ADMIN).json())
    assert client.delete(f"/api/admin/submissions/{sid}", headers=ADMIN).status_code == 204
