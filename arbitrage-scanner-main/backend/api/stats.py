from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List

from ..database import get_db
from ..models import ArbitrageOpportunity, Exchange, TradingPair
from ..schemas import StatsResponse, DailyStatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=StatsResponse)
async def get_overview_stats(db: Session = Depends(get_db)):
    """Получить общую статистику"""

    # Общая статистика
    total_opportunities = db.query(ArbitrageOpportunity).count()
    active_opportunities = (
        db.query(ArbitrageOpportunity)
        .filter(ArbitrageOpportunity.is_active == True)
        .count()
    )

    # Прибыль
    total_profit = db.query(func.sum(ArbitrageOpportunity.net_profit_usd)).scalar() or 0
    avg_profit = (
        db.query(func.avg(ArbitrageOpportunity.net_profit_percent)).scalar() or 0
    )
    max_profit = db.query(func.max(ArbitrageOpportunity.net_profit_usd)).scalar() or 0

    # Лучшая возможность
    best_opp = (
        db.query(ArbitrageOpportunity)
        .filter(ArbitrageOpportunity.is_active == True)
        .order_by(ArbitrageOpportunity.net_profit_percent.desc())
        .first()
    )

    # Количество бирж и пар
    exchanges_count = db.query(Exchange).count()
    pairs_count = db.query(TradingPair).count()

    return {
        "total_opportunities": total_opportunities,
        "active_opportunities": active_opportunities,
        "total_profit_usd": round(total_profit, 2),
        "avg_profit_percent": round(avg_profit, 2),
        "max_profit_usd": round(max_profit, 2),
        "best_opportunity": best_opp,
        "exchanges_count": exchanges_count,
        "pairs_monitored": pairs_count,
        "scanner_uptime_seconds": None,  # TODO: добавить отслеживание
    }


@router.get("/daily", response_model=List[DailyStatsResponse])
async def get_daily_stats(
    days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)
):
    """Получить статистику по дням"""

    cutoff_date = datetime.now() - timedelta(days=days)

    stats = (
        db.query(
            func.date(ArbitrageOpportunity.detected_at).label("date"),
            func.count(ArbitrageOpportunity.id).label("count"),
            func.sum(ArbitrageOpportunity.net_profit_usd).label("total_profit"),
            func.avg(ArbitrageOpportunity.net_profit_percent).label("avg_profit"),
        )
        .filter(ArbitrageOpportunity.detected_at >= cutoff_date)
        .group_by(func.date(ArbitrageOpportunity.detected_at))
        .order_by(func.date(ArbitrageOpportunity.detected_at))
        .all()
    )

    return [
        {
            "date": str(stat.date),
            "count": stat.count,
            "total_profit_usd": round(stat.total_profit or 0, 2),
            "avg_profit_percent": round(stat.avg_profit or 0, 2),
        }
        for stat in stats
    ]


@router.get("/exchanges")
async def get_exchanges_stats(db: Session = Depends(get_db)):
    """Статистика по биржам"""

    # Биржи, на которых чаще всего покупают
    buy_stats = (
        db.query(
            ArbitrageOpportunity.buy_exchange,
            func.count(ArbitrageOpportunity.id).label("count"),
            func.sum(ArbitrageOpportunity.net_profit_usd).label("total_profit"),
        )
        .group_by(ArbitrageOpportunity.buy_exchange)
        .all()
    )

    # Биржи, на которых чаще всего продают
    sell_stats = (
        db.query(
            ArbitrageOpportunity.sell_exchange,
            func.count(ArbitrageOpportunity.id).label("count"),
            func.sum(ArbitrageOpportunity.net_profit_usd).label("total_profit"),
        )
        .group_by(ArbitrageOpportunity.sell_exchange)
        .all()
    )

    return {
        "buy_exchanges": [
            {
                "exchange": stat[0],
                "count": stat[1],
                "total_profit": round(stat[2] or 0, 2),
            }
            for stat in buy_stats
        ],
        "sell_exchanges": [
            {
                "exchange": stat[0],
                "count": stat[1],
                "total_profit": round(stat[2] or 0, 2),
            }
            for stat in sell_stats
        ],
    }
