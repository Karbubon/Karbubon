from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional

from ..database import get_db
from ..models import ArbitrageOpportunity
from ..schemas import OpportunityResponse, OpportunityListResponse

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/active", response_model=List[OpportunityResponse])
async def get_active_opportunities(
    limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)
):
    """Получить активные арбитражные возможности"""
    opportunities = (
        db.query(ArbitrageOpportunity)
        .filter(ArbitrageOpportunity.is_active == True)
        .order_by(desc(ArbitrageOpportunity.net_profit_percent))
        .limit(limit)
        .all()
    )

    return opportunities


@router.get("/history", response_model=OpportunityListResponse)
async def get_opportunity_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    symbol: Optional[str] = None,
    buy_exchange: Optional[str] = None,
    sell_exchange: Optional[str] = None,
    min_profit: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Получить историю арбитражей с фильтрацией и пагинацией"""

    query = db.query(ArbitrageOpportunity)

    # Фильтры
    if symbol:
        query = query.filter(ArbitrageOpportunity.symbol.ilike(f"%{symbol}%"))
    if buy_exchange:
        query = query.filter(ArbitrageOpportunity.buy_exchange == buy_exchange)
    if sell_exchange:
        query = query.filter(ArbitrageOpportunity.sell_exchange == sell_exchange)
    if min_profit:
        query = query.filter(ArbitrageOpportunity.net_profit_percent >= min_profit)

    # Пагинация
    total = query.count()
    offset = (page - 1) * per_page

    opportunities = (
        query.order_by(desc(ArbitrageOpportunity.detected_at))
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "opportunities": opportunities,
    }


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity_by_id(opportunity_id: int, db: Session = Depends(get_db)):
    """Получить детали конкретного арбитража"""
    opportunity = (
        db.query(ArbitrageOpportunity)
        .filter(ArbitrageOpportunity.id == opportunity_id)
        .first()
    )

    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return opportunity


@router.get("/by-pair/{symbol}")
async def get_opportunities_by_symbol(
    symbol: str, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)
):
    """Получить арбитражи по символу"""
    opportunities = (
        db.query(ArbitrageOpportunity)
        .filter(ArbitrageOpportunity.symbol == symbol)
        .order_by(desc(ArbitrageOpportunity.detected_at))
        .limit(limit)
        .all()
    )

    return opportunities
