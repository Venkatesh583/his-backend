# Health Insurance System (HIS)

This is a minimal Flask-based prototype for a Health Insurance System.

Quick start (dev):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:8080/ in your browser.

Admin login: `admin@his.gov` / `admin123` (change in production)

Useful scripts:
- `scripts/test_caseworker_create.py` - automated test to create a caseworker and verify it appears in the listing.

Docs: see `DOCS/deployment.md` for deployment notes.

*** End Patch