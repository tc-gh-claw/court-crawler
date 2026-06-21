# AGENTS.md

## Cursor Cloud specific instructions

This repo's active product is **MediaMind**, a single-service Flask web app (`app.py` + `templates/index.html`). It is self-contained: no database, no external APIs, no secrets required to run or test.

### Running the app (development)
- A Python virtualenv is created at `.venv` by the startup update script. Use it explicitly: `.venv/bin/python app.py`.
- The dev server listens on port `5000` (override with `PORT`). Flask debug mode is on, so it hot-reloads on file changes.
- Health check: `GET http://localhost:5000/api/health`. Quick smoke test: `GET /api/demo`, or in the UI click **Try sample result**.
- Core API flow to exercise end-to-end: `POST /api/analyze` (JSON or multipart) → returns an `id` → `POST /api/chat` and `GET /api/export/<id>.md` use that `id`.
- Generated analyses are persisted as JSON files under `analysis_cache/` (auto-created, git-ignored). `/api/chat` and `/api/export` read from there.

### Tests / lint / build
- There is **no test framework and no linter configured** (no `pytest`, no tests dir, no eslint/ruff config). Validate changes by running the app and exercising the endpoints above.
- There is no build step; the UI is a single static `templates/index.html`.

### Gotchas
- `runtime.txt` pins Python 3.11.4, but the app runs fine on the system Python 3.12. `python3-venv` must be installed at the OS level to create the venv.
- The repo also contains a dormant, separate "court-crawler" toolset (`crawler_core.py`, `crawl_script.py`, `auto_download.py`, `setup_drive.py`, etc.) plus Google Drive packages in `requirements.txt`. These are NOT part of MediaMind. Note `auto_download.py` imports symbols that no longer exist in the current `app.py` and will fail; the MediaMind app itself is unaffected.
