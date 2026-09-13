from pydantic import BaseModel, Field
from typing import Optional, List, Any  # <-- Добавить Any
from datetime import datetime


# ============================================================
# Арбитражные возможности
# ============================================================


class OpportunityBase(BaseModel):
    """Базовая модель арбитража"""

    symbol: str
    base_asset: str
    quote_asset: str = "USDT"
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    min_buy_price: Optional[float] = None
    max_buy_price: Optional[float] = None
    min_sell_price: Optional[float] = None
    max_sell_price: Optional[float] = None
    volume_asset: float
    volume_usd: float
    buy_orders_used: int
    sell_orders_used: int
    buy_fee_percent: float
    sell_fee_percent: float
    buy_fee_usd: float
    sell_fee_usd: float
    transfer_fee_usd: float
    total_fee_usd: float
    total_fee_percent: float
    gross_spread_percent: float
    net_spread_percent: float
    gross_profit_usd: float
    net_profit_usd: float
    net_profit_percent: float
    network: Optional[str] = None
    buy_trade_url: Optional[str] = None
    sell_trade_url: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    """Ответ с данными арбитража"""

    id: int
    is_active: bool
    detected_at: datetime
    updated_at: Optional[datetime] = None
    disappeared_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpportunityListResponse(BaseModel):
    """Список арбитражей с пагинацией"""

    total: int
    page: int
    per_page: int
    opportunities: List[OpportunityResponse]


# ============================================================
# Статистика
# ============================================================


class StatsResponse(BaseModel):
    """Общая статистика"""

    total_opportunities: int
    active_opportunities: int
    total_profit_usd: float
    avg_profit_percent: float
    max_profit_usd: float
    best_opportunity: Optional[OpportunityResponse] = None
    exchanges_count: int
    pairs_monitored: int
    scanner_uptime_seconds: Optional[float] = None


class DailyStatsResponse(BaseModel):
    """Статистика по дням"""

    date: str
    count: int
    total_profit_usd: float
    avg_profit_percent: float


# ============================================================
# Настройки
# ============================================================


class SettingResponse(BaseModel):
    """Настройка"""

    key: str
    value: Any  # <-- Теперь Any импортирован из typing
    description: Optional[str] = None


class SettingUpdate(BaseModel):
    """Обновление настройки"""

    value: Any  # <-- Здесь тоже


class SettingsBatchUpdate(BaseModel):
    """Массовое обновление настроек"""

    settings: dict


# ============================================================
# WebSocket
# ============================================================


class WebSocketMessage(BaseModel):
    """WebSocket сообщение"""

    type: str  # 'new_opportunity', 'opportunity_gone', 'ping'
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)
