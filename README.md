# sessec-com

Reconstructed from <https://sessec.com/api> by Universal Website Clone Bot. See `PROJECT_REPORT.md` for what was rebuilt and
`RECONSTRUCTION_LIMITATIONS.md` for what could not be.

## Project layout

```
frontend/   static site (index.html, pages/, assets/, js/, css/)
backend/    FastAPI application (admin, snapshot, forms, auth)
database/   schema.sql (PostgreSQL)
docs/       this documentation
tests/      pytest suite for the backend
```

## Host it (Node / Render / Railway / panels)

```bash
npm start        # serves ./frontend on $PORT (default 8080) - no dependencies to install
```
Netlify and Vercel publish the `frontend/` folder (`netlify.toml`, `vercel.json` are included). Forms and the admin panel need
the Python backend (below); a static host only serves the pages.

## Quick start - frontend only

```bash
python -m http.server 8080 --directory frontend
# open http://localhost:8080
```

## Run the full stack (frontend + backend)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit ADMIN_TOKEN
export $(grep -v '^#' .env | xargs)
python -m uvicorn backend.main:app --port 8000
# open http://localhost:8000  (the backend also serves the frontend)
```

## Configure

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./app.db` |
| `ADMIN_TOKEN` | Header `X-Admin-Token` for reading submissions | (required for admin routes) |
| `CORS_ORIGINS` | Comma-separated allowed origins if the frontend is hosted elsewhere | empty |
| `RATE_LIMIT_PER_MINUTE` | Per-IP limit on form/auth endpoints | 20 |

If you host the frontend separately, set `window.CLONE_API_BASE` in `frontend/js/config.js` to the API origin.

## Database (PostgreSQL)

```bash
createdb app && psql app -f database/schema.sql
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/app
```
Tables are also created automatically on start-up (`init_db`). `schema.sql` is provided for managed/production setups.

## API

- `GET /health`
- `POST /api/forms/forgot-password-generic-1` - generic form from https://sessec.com/forgot-password
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- `GET /api/forms?slug=<form>` (admin token) - list submissions
- `GET /admin` - admin panel UI (enter `ADMIN_TOKEN`); JSON API under `/api/admin/*` (header `X-Admin-Token`)
- Stored public API responses are served at their original paths (see `backend/services/snapshot_manifest.py`)

## Deploy with Docker

```bash
cp .env.example .env   # set ADMIN_TOKEN and DB_PASSWORD
docker compose up -d --build
```

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests
```
