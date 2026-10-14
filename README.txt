GYM MEMBERSHIP & WORKOUT PLANNER — AUTH PAGE REDESIGN

Files included:
- main.py: your existing FastAPI routes, unchanged
- templates/login.html: redesigned login screen
- templates/register.html: redesigned registration screen
- static/style.css: shared responsive styling
- static/gym-editorial.jpg: generated gym editorial visual
- requirements.txt: project dependencies

HOW TO USE
1. Keep main.py in the project root.
2. Replace your existing templates/login.html and templates/register.html with the supplied versions.
3. Replace static/style.css with the supplied CSS.
4. Copy static/gym-editorial.jpg into your project's static folder. Make sure the filename matches exactly.
5. Run from the project root with your virtual environment active:
   uvicorn main:app --reload
6. Open http://127.0.0.1:8000/login and http://127.0.0.1:8000/register.

NOTES
- The existing GET routes and their names are preserved.
- The password Show/Hide controls work in the browser.
- Native HTML required/email/minlength checks are enabled.
- Authentication and registration submission are still frontend-only; no POST endpoints or database logic have been added.
- Google Fonts is used if the browser has internet access; fallback fonts are specified.
