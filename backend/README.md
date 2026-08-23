# FastAPI Backend

Backend control-plane for AI Network Agent.

## Run

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`

## Flow

OpenCode Tool -> FastAPI -> Service -> Driver -> Transport -> Network Device

Configuration workflow target:

current state -> backup -> plan -> validate -> policy -> approval -> apply -> verify -> audit -> rollback on failure
