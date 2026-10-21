GYM WORKOUT PLANNER — WHITE-BOX TESTS

FILES
- tests/conftest.py: configures an isolated temporary SQLite test database.
- tests/test_authentication.py: registration, login, password, session and role branches.
- tests/test_memberships.py: plan listing/details, access control, selection and switching branches.
- pytest.ini: configures test discovery.

SETUP IN VS CODE
1. Extract these files into the ROOT of your existing Gym Workout Planner project. The `tests` folder must sit next to `main.py`, `models.py`, and `database.py`.
2. Open the VS Code terminal at the project root (same folder as `main.py`).
3. Install test dependencies in your existing venv:
   .\venv\Scripts\python.exe -m pip install pytest pytest-cov httpx
4. Ensure the app's normal dependencies are installed too, including FastAPI, SQLAlchemy, pwdlib with Argon2 support, python-multipart, and Jinja2.

RUN THE TESTS
   .\venv\Scripts\python.exe -m pytest -v

BRANCH COVERAGE REPORT
   .\venv\Scripts\python.exe -m pytest --cov=main --cov=models --cov-branch --cov-report=term-missing --cov-report=html
Then open `htmlcov\index.html` to inspect covered and missed lines/branches.

DATABASE SAFETY
These tests replace the `database` module only inside the pytest process with a temporary SQLite database before importing the app. They do not intentionally read or write the project's real `gym.db`. Run pytest from the project root so the existing `templates/` and `static/` directories resolve correctly. Tests create only temporary users and selections. Do not include real database files or secrets in the test bundle or commit them to GitHub.

SCOPE
The tests exercise internal decision branches through FastAPI's TestClient, which is appropriate for branch-oriented white-box testing of the current routes. The suite was syntax-checked but not executed against your local project. Use actual pytest output for the final report; do not mark tests as passed until they have run.

If your local `main.py`, model fields, route names, or templates have changed since the version used to prepare these tests, adjust the relevant test assertions to match the current app.
