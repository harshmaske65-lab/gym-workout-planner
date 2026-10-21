"""White-box tests for registration, login, sessions, and role checks."""
from models import User


def test_home_route_returns_service_message(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Gym Workout Planner is running!"


def test_registration_page_renders(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert "Create account" in response.text or "Start your" in response.text


def test_registration_stores_password_hash_and_regular_role(client, db_session):
    response = client.post(
        "/register",
        data={"name": "Test Member", "email": " NEWUSER@example.com ", "password": "StrongPass123!"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login?registered=1"

    user = db_session.query(User).filter_by(email="newuser@example.com").first()
    assert user is not None
    assert user.password_hash != "StrongPass123!"
    assert main_password_verifies(user.password_hash, "StrongPass123!")
    assert user.role == "user"


def main_password_verifies(password_hash: str, password: str) -> bool:
    # Invoke the application's configured password verifier.
    import main
    return main.password_hasher.verify(password, password_hash)


def test_registration_rejects_blank_name(client):
    response = client.post("/register", data={"name": "   ", "email": "member@example.com", "password": "StrongPass123!"})
    assert response.status_code == 400
    assert "name" in response.text.lower()


def test_registration_rejects_invalid_email(client):
    response = client.post("/register", data={"name": "Member", "email": "invalid-email", "password": "StrongPass123!"})
    assert response.status_code == 400
    assert "email" in response.text.lower()


def test_registration_rejects_short_password(client):
    response = client.post("/register", data={"name": "Member", "email": "short@example.com", "password": "123"})
    assert response.status_code == 400
    assert "8 characters" in response.text


def test_registration_rejects_duplicate_email(client, create_user):
    create_user("duplicate@example.com")
    response = client.post(
        "/register",
        data={"name": "Second Member", "email": "DUPLICATE@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 400
    assert "already exists" in response.text


def test_signup_cannot_assign_admin_role(client, db_session):
    client.post(
        "/register",
        data={"name": "Attempted Admin", "email": "signup-role@example.com", "password": "StrongPass123!", "role": "admin"},
    )
    user = db_session.query(User).filter_by(email="signup-role@example.com").first()
    assert user is not None
    assert user.role == "user"


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_login_rejects_unknown_email(client):
    response = client.post("/login", data={"email": "missing@example.com", "password": "StrongPass123!"})
    assert response.status_code == 401
    assert "incorrect" in response.text.lower()


def test_login_rejects_wrong_password(client, create_user):
    create_user("wrong-password@example.com", password="CorrectPass123!")
    response = client.post("/login", data={"email": "wrong-password@example.com", "password": "WrongPass123!"})
    assert response.status_code == 401


def test_login_accepts_normalized_email_and_redirects_user(client, create_user):
    create_user("member-login@example.com", password="CorrectPass123!")
    response = client.post(
        "/login",
        data={"email": " MEMBER-LOGIN@EXAMPLE.COM ", "password": "CorrectPass123!"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert client.get("/dashboard").status_code == 200


def test_login_redirects_admin_to_admin_dashboard(client, create_user):
    create_user("admin-login@example.com", password="CorrectPass123!", role="admin")
    response = client.post(
        "/login",
        data={"email": "admin-login@example.com", "password": "CorrectPass123!"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard"
    assert client.get("/admin/dashboard").status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_regular_user_cannot_open_admin_dashboard(client, create_user):
    create_user("member-role@example.com")
    client.post("/login", data={"email": "member-role@example.com", "password": "StrongPass123!"})
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"


def test_logout_clears_session(client, create_user):
    create_user("logout@example.com")
    client.post("/login", data={"email": "logout@example.com", "password": "StrongPass123!"})
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?logged_out=1"
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
