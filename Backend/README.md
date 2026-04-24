# Backend

FastAPI backend for the compute rental system.

It supports two database modes:

- local SQLite for development/tests
- Postgres via `DATABASE_URL` for deployment (for example Neon on Vercel)

## Run

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Run from the `Backend` directory.

## Environment Variables

Copy `Backend/.env.example` into a local `.env` file if you want a template.

- `DATABASE_URL`: Postgres connection string for Neon/Vercel deployment
- `COMPUTE_RENTAL_DB_PATH`: local SQLite path used when `DATABASE_URL` is empty
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins to allow in addition to local Vite URLs

## API

- `GET /api/locations/summary`
- `GET /api/cards`
- `POST /api/rentals`
- `GET /api/rentals/{rental_id}`
- `POST /api/rentals/{rental_id}/cancel`
