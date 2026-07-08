from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, channels, dashboard, invites, periods, recommendations, stocks
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.seed import run_seed

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.migrate import run_migrations
    from app.services.invites import backfill_invite_codes

    run_migrations()
    run_seed()
    db = SessionLocal()
    try:
        backfill_invite_codes(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(periods.router, prefix="/api")
app.include_router(channels.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(invites.router, prefix="/api")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "api_version": "2026-07-08",
        "features": ["rec_remove", "rec_refetch", "auto_fetch", "invites"],
    }


@app.get("/api/config/public")
def public_config():
    from app.database import SessionLocal
    from app.services.app_settings import register_sms_required
    from app.services.sms import sms_config

    db = SessionLocal()
    try:
        sms = sms_config()
        sms["register_sms_required"] = register_sms_required(db)
    finally:
        db.close()
    return {
        "app_name": settings.app_name,
        "sms": sms,
    }
