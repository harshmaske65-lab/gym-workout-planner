from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # Every new public registration is a regular user by default.
    # Never expose this field as an option on the public registration form.
    role = Column(String(20), nullable=False, default="user", server_default="user")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    slug = Column(String(80), unique=True, index=True, nullable=False)
    tagline = Column(String(160), nullable=False)
    description = Column(String(300), nullable=False)
    price_monthly = Column(Integer, nullable=False)
    features = Column(JSON, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)


class MembershipSelection(Base):
    """The single currently selected membership plan for each regular user."""

    __tablename__ = "membership_selections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    plan_id = Column(
        Integer,
        ForeignKey("membership_plans.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    selected_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
