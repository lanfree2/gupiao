from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, channels, dashboard, periods, recommendations, stocks
from app.config import get_settings
from app.database import Base, engine
from app.seed import run_seed

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_seed()
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


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/config/public")
def public_config():
    from app.services.sms import sms_config

    return {
        "app_name": settings.app_name,
        "sms": sms_config(),
    }
