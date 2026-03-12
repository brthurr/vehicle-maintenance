# 🔧 Vehicle Maintenance Tracker

A lightweight, self-hosted Python web app for tracking vehicle maintenance intervals and storing receipts. Built with Flask and SQLite — no external database required.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.x-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- **Multi-vehicle support** — Cars, trucks, motorcycles, ATVs, boats, RVs
- **Service logging** — Record every service with date, mileage, cost, and notes
- **17 default service types** — Oil changes, tire rotation, filters, fluids, and more
- **Custom service types** — Add your own categories
- **Receipt uploads** — Attach PDFs, photos, or images to any log entry
- **Overdue alerts** — Dashboard flags services past their mileage threshold
- **Cost reports** — Break down spending by service type across all vehicles
- **Zero dependencies** beyond Flask — uses Python's built-in `sqlite3`

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/vehicle-maintenance.git
cd vehicle-maintenance
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the development server

```bash
python run.py
```

Open **http://localhost:5000** in your browser.

---

## Project Structure

```
vehicle-maintenance/
├── app/
│   ├── __init__.py       # Package — exports create_app()
│   ├── app.py            # Flask application factory & all routes
│   ├── database.py       # SQLite schema, connection helpers, seed data
│   └── templates.py      # Inline Jinja2 HTML templates
├── tests/
│   ├── __init__.py
│   └── test_app.py       # 35 unit & integration tests
├── uploads/              # Receipt files (auto-created, git-ignored)
├── run.py                # Development entry point
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Running Tests

```bash
python -m unittest discover tests -v
```

Or with pytest if installed:

```bash
pytest tests/ -v
```

The test suite covers:
- Database schema creation and idempotency
- Foreign key enforcement
- All CRUD routes for vehicles, logs, and receipts
- File upload allow/deny by extension
- Form validation (missing fields, bad year, bad mileage)
- Overdue mileage detection
- Cost reporting

---

## Configuration

Environment variables (all optional):

| Variable     | Default                            | Description                          |
|--------------|------------------------------------|--------------------------------------|
| `SECRET_KEY` | `dev-secret-change-in-production`  | Flask session secret — **change in production** |
| `DB_PATH`    | `maintenance.db`                   | Path to the SQLite database file     |
| `PORT`       | `5000`                             | Port for the development server      |

Example:

```bash
export SECRET_KEY="my-strong-random-key"
export DB_PATH="/data/maintenance.db"
python run.py
```

---

## File Uploads

Receipts are stored in the `uploads/` directory. Allowed file types: **PDF, PNG, JPG, JPEG, GIF, WEBP**. Maximum upload size is 16 MB.

The `uploads/` directory is excluded from version control via `.gitignore`.

---

## Deployment Notes

For production:
1. Set a strong `SECRET_KEY` environment variable
2. Run behind a WSGI server: `gunicorn "app:create_app()"` 
3. Use a reverse proxy (nginx, Caddy) for HTTPS
4. Back up `maintenance.db` and `uploads/` regularly

---

## License

MIT
