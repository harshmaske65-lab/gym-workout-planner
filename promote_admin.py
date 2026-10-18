"""Promote an existing account to admin using a local terminal, never a public form."""
from sqlalchemy import inspect, text

from database import Base, SessionLocal, engine
from models import MembershipPlan, User  # noqa: F401 - register model metadata


Base.metadata.create_all(bind=engine)
columns = {column["name"] for column in inspect(engine).get_columns("users")}
if "role" not in columns:
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
        )

email = input("Email of the existing account to promote to admin: ").strip().lower()
if not email:
    raise SystemExit("No email entered. Nothing changed.")

with SessionLocal() as db:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise SystemExit(
            "No registered account found for that email. Register the account first, then rerun this script."
        )
    user.role = "admin"
    db.commit()
    print(f"Success: {user.email} now has role='admin'.")
    print("Log out and sign in again to open the admin dashboard.")
