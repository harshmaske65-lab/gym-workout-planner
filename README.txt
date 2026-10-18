GYM WORKOUT PLANNER — ROLE-BASED USER AND ADMIN INTERFACES

Goal
- Regular members use /dashboard.
- Administrators use /admin/dashboard.
- The page a user is sent to is determined by the role stored in SQLite, not by the signup form or a URL parameter.
- Public signups always receive role='user'. Never add a public role dropdown to registration.

Included files
- main.py: keeps existing registration, login, session, logout, and public membership plans functionality; adds a SQLite migration for users.role and an admin dashboard route.
- models.py: existing User and MembershipPlan models, with User.role.
- templates/dashboard.html: regular-member interface.
- templates/admin_dashboard.html: separate admin interface with counts, registered members, and membership plans overview.
- templates/membership_plans.html: updates the account navigation to return admins to their admin dashboard.
- static/membership.css: the existing membership plans styling (included for convenience; it should match the display-plans task).
- promote_admin.py: local command-line utility to promote an existing account to admin.

Before replacing files
1. Make a backup of main.py, models.py, templates/dashboard.html, and templates/membership_plans.html.
2. Replace main.py and models.py in the project root.
3. Replace templates/dashboard.html and templates/membership_plans.html.
4. Add templates/admin_dashboard.html.
5. Copy static/membership.css into static/ (if you already have the same file, it is fine to keep it).
6. Add promote_admin.py to the project root.
7. Keep database.py, register.html, login.html, style.css, gym-editorial.jpg, gym.db, and .session_secret. Do not replace or delete your database.

Database migration
- On startup, main.py checks whether users.role exists. If it does not, it adds the SQLite column with DEFAULT 'user'. This preserves existing users and makes them regular members by default.
- New registrations are explicitly assigned role='user'. Admin role is never accepted from public form data.

Make an existing account an admin
1. Start the app once using the new main.py so the role migration runs. Wait for startup to complete, then stop the server with Ctrl+C.
2. Run: .\venv\Scripts\python.exe promote_admin.py
3. Type the email address of the account that should have admin access. The account must already be registered.
4. Restart the app and sign in again using that account.
5. The account should open /admin/dashboard after login. Regular accounts continue to open /dashboard.

Run the app
  .\venv\Scripts\python.exe -m uvicorn main:app --reload

Test checklist
- Regular user logs in -> /dashboard.
- Admin account logs in -> /admin/dashboard.
- A regular user visits /admin/dashboard -> redirected to /dashboard.
- A logged-out visitor visits either dashboard -> redirected to /login.
- A new public registration gets role='user' and cannot self-assign admin.
- Admin dashboard shows registered regular members and plan overview.
- Membership plan page remains public at http://127.0.0.1:8000/membership-plans.

Security note
- Admin promotion is intentionally performed through a local terminal utility, not through a public HTTP endpoint. For production, also add CSRF protections and use a strong environment-provided GYM_SESSION_SECRET over HTTPS.
