GYM WORKOUT PLANNER — SCRUM-21: VIEW MEMBERSHIP DETAILS

WHAT THIS UPDATE ADDS
- Adds a dedicated detail page for each active membership plan at /membership-plans/{slug}.
- Adds a "View plan details" link to every card on the membership plans overview page.
- Displays the selected plan's name, tagline, description, monthly price, and included features using values from the existing SQLite database.
- Lets signed-in members see whether the plan is already selected and select/switch plans using the existing POST /membership-plans/select endpoint and confirmation modal.
- Lets visitors view details without signing in; selecting a plan still requires a member account.
- Keeps admin accounts in read-only browse mode for member-plan selection.
- Adds a direct "View membership details" link on the member dashboard when a plan has been selected.
- Keeps the same cream/charcoal/olive visual design.

FILES TO UPDATE
1. Replace main.py with this version (adds HTTPException import and the GET /membership-plans/{slug} route).
2. Replace templates/membership_plans.html with this version (adds details links to each plan card; preserves the custom confirmation modal).
3. Add templates/membership_detail.html.
4. Replace static/membership.css with this version (includes plan-detail and card-link styling and keeps existing styles/modal).
5. Replace templates/dashboard.html with this version (keeps the large browse plans button and adds a selected-plan details link).

KEEP THESE EXISTING FILES
- database.py
- gym.db
- .session_secret
- models.py (no model/database schema changes are needed)
- templates/login.html
- templates/register.html
- templates/admin_dashboard.html
- static/style.css
- static/gym-editorial.jpg
- promote_admin.py

BACKUP FIRST
Back up main.py, templates/membership_plans.html, templates/dashboard.html and static/membership.css before replacing them. Do not delete or overwrite gym.db.

RUN
From the project root:
  .\venv\Scripts\python.exe -m uvicorn main:app --reload

OPEN
  http://127.0.0.1:8000/membership-plans
Click "View plan details" on any plan card, or open e.g.:
  http://127.0.0.1:8000/membership-plans/starter
  http://127.0.0.1:8000/membership-plans/plus
  http://127.0.0.1:8000/membership-plans/elite

TEST CHECKLIST
1. Open each plan's detail page and verify the name, description, price and features reflect the database.
2. Use an invalid slug and verify a 404 response.
3. Browse as a logged-out visitor; details should render, but selection requires signing in.
4. Sign in as a regular member; confirm that the selected plan is marked as current, or select/switch plans using the custom modal.
5. Sign in as admin and verify that plan details can be viewed but the member selection action is not offered.
6. From the member dashboard, click "View membership details" for the selected plan.

NOTES
- Prices are illustrative demo values, and payment processing / paid subscription activation is not implemented.
- This feature reads the existing MembershipPlan model. It does not change the database schema.
