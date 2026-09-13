from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api import opportunities, stats, settings, websocket, cmc
from .database import engine
from . import models


models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Arbitrage Scanner API...")
    yield
    print("🛑 Shutting down Arbitrage Scanner API...")


app = FastAPI(title="Arbitrage Scanner API", version="2.0.0", lifespan=lifespan)

# CORS - разрешаем все для отладки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрируем роутеры
app.include_router(opportunities.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(websocket.router)  # Без префикса, т.к. он уже есть в роутере
app.include_router(cmc.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Arbitrage Scanner API",
        "version": "2.0.0",
        "status": "running",
        "websocket_url": "ws://localhost:8000/ws/opportunities",
    }


@app.get("/api/health")
async def health_check():
    from datetime import datetime

    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
