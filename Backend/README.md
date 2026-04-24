# Backend

FastAPI + SQLite backend for the compute rental system.

## Run

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Run from the `backend` directory.

## API

- `GET /api/locations/summary`
- `GET /api/cards`
- `POST /api/rentals`
- `GET /api/rentals/{rental_id}`
- `POST /api/rentals/{rental_id}/cancel`
