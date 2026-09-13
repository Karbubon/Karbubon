from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TradingPair

router = APIRouter(prefix="/cmc", tags=["cmc"])


@router.get("/{symbol}")
async def get_cmc_info(symbol: str, db: Session = Depends(get_db)):
    """Получить информацию о монете из БД (данные CMC)"""

    # Нормализуем символ
    if "/" not in symbol:
        symbol = f"{symbol}/USDT"

    pair = db.query(TradingPair).filter(TradingPair.symbol == symbol).first()

    if not pair:
        raise HTTPException(status_code=404, detail=f"Coin {symbol} not found")

    return {
        "symbol": pair.symbol,
        "base_asset": pair.base_asset,
        "name": pair.cmc_name or pair.base_asset,
        "rank": pair.cmc_rank or 0,
        "price_usd": pair.cmc_price_usd or 0,
        "market_cap": pair.cmc_market_cap or 0,
        "volume_24h": pair.cmc_volume_24h or 0,
        "percent_change_24h": pair.cmc_percent_change_24h or 0,
        "updated_at": pair.cmc_updated_at.isoformat() if pair.cmc_updated_at else None,
    }


@router.get("/top/{limit}")
async def get_top_coins(limit: int = 50, db: Session = Depends(get_db)):
    """Получить топ монет из БД по рангу CMC"""

    pairs = (
        db.query(TradingPair)
        .filter(TradingPair.cmc_rank.isnot(None))
        .order_by(TradingPair.cmc_rank)
        .limit(limit)
        .all()
    )

    return [
        {
            "symbol": p.symbol,
            "base_asset": p.base_asset,
            "name": p.cmc_name or p.base_asset,
            "rank": p.cmc_rank,
            "price_usd": p.cmc_price_usd or 0,
            "market_cap": p.cmc_market_cap or 0,
            "volume_24h": p.cmc_volume_24h or 0,
        }
        for p in pairs
    ]


@router.post("/update")
async def update_cmc_data_manual(db: Session = Depends(get_db)):
    """Запустить обновление CMC данных (вручную)"""
    # Запускаем в фоне, чтобы не блокировать ответ
    import subprocess

    subprocess.Popen(["python", "scripts/update_cmc_data.py"])
    return {"message": "CMC data update started in background"}
