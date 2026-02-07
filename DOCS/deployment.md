# Deployment and Run Notes

This document contains basic steps to run the Health Insurance System locally and notes for deploying to a production host.

Local (development)
- Create a Python 3.11 virtual environment and install requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Start the app:

```powershell
python app.py
```

- By default the app runs on port `8080`. Use `PORT` env var to override.

Production notes
- The repo includes `Procfile` and `runtime.txt` for PaaS platforms (Heroku/Render). Ensure `requirements.txt` lists pinned versions.
- Use a production WSGI server (gunicorn) and a proper SQLite path or migrate to Postgres/Cloud SQL for multi-instance deployments.

Environment variables
- `PORT` (optional) - port to listen on
- `SECRET_KEY` (optional) - override `app.secret_key` for production

Files of interest
- `app.py` - main Flask app
- `his.db` - SQLite DB file (created by `init_tables()` on first run)
- `templates/` - HTML templates
- `static/` - static assets

Security
- Replace default credentials and secure admin passwords.
- Use HTTPS in production and secure session cookies.

*** End Patch