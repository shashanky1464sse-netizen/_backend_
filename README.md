# Resume2Interview — FastAPI Backend

A modular, production-ready FastAPI backend for the **Resume2Interview** Android app.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app factory, CORS, startup
│   ├── database.py        # SQLite engine, session, Base, get_db()
│   ├── core/
│   │   └── config.py      # Pydantic settings loaded from .env
│   ├── models/            # SQLAlchemy ORM models (add yours here)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── routers/
│   │   └── health.py      # GET /health
│   └── services/          # Business logic (keep routers thin)
├── .env                   # Local secrets (not committed)
├── .env.example           # Template for .env
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Edit `.env` and set a strong `SECRET_KEY` and any other values.

### 4. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc |

> **Android emulator note:** Use `http://10.0.2.2:8000` as the base URL inside an Android emulator to reach your host machine's `localhost`.

---

## Adding a New Feature

1. **Model** → `app/models/your_model.py` (inherit from `Base`)
2. **Schema** → `app/schemas/your_schema.py` (Pydantic `BaseModel`)
3. **Service** → `app/services/your_service.py` (business logic)
4. **Router** → `app/routers/your_router.py` (thin HTTP layer)
5. Register the router in `app/main.py`:
   ```python
   from app.routers import your_router
   app.include_router(your_router.router, prefix="/your-prefix", tags=["YourTag"])
   ```
6. Import your model in `app/models/__init__.py` so `init_db()` picks it up.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Resume2Interview API` | API title shown in Swagger |
| `APP_VERSION` | `1.0.0` | API version |
| `DEBUG` | `True` | Enables SQL echo and debug mode |
| `DATABASE_URL` | `sqlite:///./resume2interview.db` | SQLAlchemy DB URL |
| `ALLOWED_ORIGINS` | `http://localhost,http://10.0.2.2` | Comma-separated CORS origins |
| `SECRET_KEY` | *(change this!)* | Used for token signing |
