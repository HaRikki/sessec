"""Reconstructed backend entry point. Run: uvicorn backend.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import CORS_ORIGINS, FRONTEND_DIR
from backend.database import SessionLocal, init_db
from backend.routes import admin, auth, forms, health, snapshot
from backend.services.snapshot import seed_snapshots


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed_snapshots(db)
    yield


app = FastAPI(title="sessec-com", lifespan=lifespan)
if CORS_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])
app.include_router(health.router)
app.include_router(forms.router)
app.include_router(auth.router)
app.include_router(admin.ui_router)
app.include_router(admin.router)
app.include_router(snapshot.router)

# Serve the reconstructed frontend last so /api/* and /admin take priority.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
