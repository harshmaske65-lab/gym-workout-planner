"""White-box tests for membership-plan queries, selection, and access control."""
from models import MembershipPlan, MembershipSelection


def get_plan(db_session, slug="starter"):
    plan = db_session.query(MembershipPlan).filter_by(slug=slug).first()
    assert plan is not None, f"Expected seeded plan {slug!r} to exist"
    return plan


def test_membership_plans_are_public_and_active_plans_display(client):
    response = client.get("/membership-plans")
    assert response.status_code == 200
    assert "Starter" in response.text
    assert "Plus" in response.text
    assert "Elite" in response.text


def test_membership_detail_displays_plan_from_database(client, db_session):
    plan = get_plan(db_session, "starter")
    response = client.get("/membership-plans/starter")
    assert response.status_code == 200
    assert plan.name in response.text
    assert str(plan.price_monthly) in response.text


def test_inactive_plan_detail_returns_404(client, db_session):
    plan = get_plan(db_session, "starter")
    plan.is_active = False
    db_session.commit()
    response = client.get("/membership-plans/starter")
    assert response.status_code == 404


def test_unknown_plan_detail_returns_404(client):
    response = client.get("/membership-plans/not-a-real-plan")
    assert response.status_code == 404


def test_plan_selection_requires_login(client, db_session):
    plan = get_plan(db_session)
    response = client.post("/membership-plans/select", data={"plan_id": plan.id}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_member_can_select_active_plan(client, create_user, db_session):
    create_user("select-plan@example.com")
    plan = get_plan(db_session, "starter")
    client.post("/login", data={"email": "select-plan@example.com", "password": "StrongPass123!"})

    response = client.post(
        "/membership-plans/select",
        data={"plan_id": plan.id},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/membership-plans?selected=1"

    selection = db_session.query(MembershipSelection).filter(
    MembershipSelection.plan_id == plan.id
    ).first()
    assert selection is not None


def test_selecting_another_plan_updates_current_selection(client, create_user, db_session):
    user_id = create_user("switch-plan@example.com")
    starter = get_plan(db_session, "starter")
    plus = get_plan(db_session, "plus")
    client.post("/login", data={"email": "switch-plan@example.com", "password": "StrongPass123!"})
    client.post("/membership-plans/select", data={"plan_id": starter.id})
    response = client.post(
        "/membership-plans/select",
        data={"plan_id": plus.id},
        follow_redirects=False,
    )
    assert response.status_code == 303

    selection = db_session.query(MembershipSelection).filter_by(user_id=user_id).first()
    assert selection is not None
    assert selection.plan_id == plus.id
    assert db_session.query(MembershipSelection).count() == 1


def test_member_cannot_select_inactive_plan(client, create_user, db_session):
    create_user("inactive-plan@example.com")
    plan = get_plan(db_session, "starter")
    plan.is_active = False
    db_session.commit()
    client.post("/login", data={"email": "inactive-plan@example.com", "password": "StrongPass123!"})

    response = client.post(
        "/membership-plans/select",
        data={"plan_id": plan.id},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/membership-plans?error=unavailable"
    assert db_session.query(MembershipSelection).count() == 0


def test_admin_cannot_select_member_plan(client, create_user, db_session):
    create_user("admin-select@example.com", role="admin")
    plan = get_plan(db_session)
    client.post("/login", data={"email": "admin-select@example.com", "password": "StrongPass123!"})

    response = client.post(
        "/membership-plans/select",
        data={"plan_id": plan.id},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/membership-plans?error=members_only"
    assert db_session.query(MembershipSelection).count() == 0


def test_invalid_plan_id_does_not_create_selection(client, create_user, db_session):
    create_user("bad-plan-id@example.com")
    client.post("/login", data={"email": "bad-plan-id@example.com", "password": "StrongPass123!"})
    response = client.post(
        "/membership-plans/select",
        data={"plan_id": 999999},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/membership-plans?error=unavailable"
    assert db_session.query(MembershipSelection).count() == 0
