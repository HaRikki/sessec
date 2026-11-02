"""Runtime configuration (environment variables)."""
import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(Path(__file__).resolve().parent.parent / "frontend")))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
