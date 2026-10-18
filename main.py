import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pwdlib import PasswordHash
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from database import Base, SessionLocal, engine, get_db
from models import MembershipPlan, User


app = FastAPI(title="Gym Membership & Workout Planner")

# Keep the same session-signing key across restarts. For deployment, set
# GYM_SESSION_SECRET as an environment variable instead of relying on this file.
_secret_file = Path(__file__).with_name(".session_secret")
SESSION_SECRET = os.getenv("GYM_SESSION_SECRET")
if not SESSION_SECRET:
    if not _secret_file.exists():
        _secret_file.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    SESSION_SECRET = _secret_file.read_text(encoding="utf-8").strip()
    if not SESSION_SECRET:
        raise RuntimeError(
            "The .session_secret file is empty. Set GYM_SESSION_SECRET or recreate the file."
        )

# Local development uses HTTP. Set GYM_HTTPS_ONLY=true when deployed with HTTPS.
https_only = os.getenv("GYM_HTTPS_ONLY", "false").lower() == "true"
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="gym_planner_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=https_only,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create missing tables, then migrate existing SQLite databases. create_all()
# does not add new columns to a table that already exists.
Base.metadata.create_all(bind=engine)


def ensure_user_role_column():
    tables = inspect(engine).get_table_names()
    if "users" not in tables:
        return
    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "role" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
            )


ensure_user_role_column()
password_hasher = PasswordHash.recommended()


def dashboard_url(user: User) -> str:
    """Choose the dashboard from the user's database role, not form input."""
    return "/admin/dashboard" if user.role == "admin" else "/dashboard"


# These are illustrative prices/features. Existing plan rows are not overwritten.
def seed_membership_plans():
    db = SessionLocal()
    try:
        if db.query(MembershipPlan).count() == 0:
            db.add_all(
                [
                    MembershipPlan(
                        name="Starter",
                        slug="starter",
                        tagline="Build the habit.",
                        description="The essentials to get moving and stay consistent.",
                        price_monthly=799,
                        features=["Gym access", "Workout planner", "Basic progress tracking"],
                        is_featured=False,
                        sort_order=1,
                    ),
                    MembershipPlan(
                        name="Plus",
                        slug="plus",
                        tagline="Make every session count.",
                        description="A balanced plan for members ready to level up.",
                        price_monthly=1499,
                        features=[
                            "Everything in Starter",
                            "Personalised workout plans",
                            "Progress history and goals",
                            "Monthly plan review",
                        ],
                        is_featured=True,
                        sort_order=2,
                    ),
                    MembershipPlan(
                        name="Elite",
                        slug="elite",
                        tagline="Train with a plan.",
                        description="More guidance and structure for focused training.",
                        price_monthly=2499,
                        features=[
                            "Everything in Plus",
                            "Priority trainer consultation",
                            "Advanced progress insights",
                            "Monthly routine adjustment",
                        ],
                        is_featured=False,
                        sort_order=3,
                    ),
                ]
            )
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


seed_membership_plans()


@app.get("/")
def home():
    return {"message": "Gym Workout Planner is running!"}


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": None, "form_name": "", "form_email": ""},
    )


@app.post("/register")
def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    name = name.strip()
    email = email.strip().lower()

    if not name or len(name) > 100:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "Please enter a name of up to 100 characters.",
                "form_name": name,
                "form_email": email,
            },
            status_code=400,
        )

    if len(email) > 255 or "@" not in email:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "Please enter a valid email address.",
                "form_name": name,
                "form_email": email,
            },
            status_code=400,
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "Password must contain at least 8 characters.",
                "form_name": name,
                "form_email": email,
            },
            status_code=400,
        )

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "An account with this email already exists.",
                "form_name": name,
                "form_email": email,
            },
            status_code=400,
        )

    # The role is assigned server-side. A public signup cannot create admins.
    user = User(
        full_name=name,
        email=email,
        password_hash=password_hasher.hash(password),
        role="user",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "An account with this email already exists.",
                "form_name": name,
                "form_email": email,
            },
            status_code=400,
        )

    return RedirectResponse(url="/login?registered=1", status_code=303)


@app.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is not None:
        user = db.get(User, user_id)
        if user:
            return RedirectResponse(url=dashboard_url(user), status_code=303)
        request.session.clear()

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "form_email": "",
            "registered": request.query_params.get("registered") == "1",
            "logged_out": request.query_params.get("logged_out") == "1",
        },
    )


@app.post("/login")
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if user is None or not password_hasher.verify(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": "Email or password is incorrect. Please try again.",
                "form_email": email,
                "registered": False,
                "logged_out": False,
            },
            status_code=401,
        )

    # Rotate the session contents after successful authentication.
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse(url=dashboard_url(user), status_code=303)


@app.get("/dashboard")
def member_dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        return RedirectResponse(url="/login", status_code=303)

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    # Keep member and admin interfaces separate.
    if user.role == "admin":
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"user": user},
    )


@app.get("/admin/dashboard")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        return RedirectResponse(url="/login", status_code=303)

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    if user.role != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)

    members = (
        db.query(User)
        .filter(User.role == "user")
        .order_by(User.created_at.desc(), User.id.desc())
        .all()
    )
    plans = db.query(MembershipPlan).order_by(MembershipPlan.sort_order, MembershipPlan.id).all()
    active_plan_count = sum(1 for plan in plans if plan.is_active)

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": user,
            "members": members,
            "member_count": len(members),
            "plans": plans,
            "plan_count": len(plans),
            "active_plan_count": active_plan_count,
        },
    )


@app.get("/membership-plans")
def membership_plans(request: Request, db: Session = Depends(get_db)):
    # Intentionally public: anyone can browse plans without logging in.
    plans = (
        db.query(MembershipPlan)
        .filter(MembershipPlan.is_active.is_(True))
        .order_by(MembershipPlan.sort_order, MembershipPlan.id)
        .all()
    )
    user = None
    user_id = request.session.get("user_id")
    if user_id is not None:
        user = db.get(User, user_id)

    return templates.TemplateResponse(
        request=request,
        name="membership_plans.html",
        context={
            "plans": plans,
            "signed_in": user is not None,
            "dashboard_url": dashboard_url(user) if user else "/dashboard",
            "user_role": user.role if user else None,
        },
    )


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login?logged_out=1", status_code=303)
