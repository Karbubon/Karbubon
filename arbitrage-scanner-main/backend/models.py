from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class UserSetting(Base):
    """Модель настроек пользователя"""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())


class Exchange(Base):
    """Модель биржи"""

    __tablename__ = "exchanges"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    ccxt_id = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class TradingPair(Base):
    """Модель торговой пары"""

    __tablename__ = "trading_pairs"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False)
    base_asset = Column(String(20), nullable=False)
    quote_asset = Column(String(10), nullable=False, default="USDT")

    # CMC данные
    cmc_rank = Column(Integer, nullable=True)
    cmc_name = Column(String(100), nullable=True)
    cmc_price_usd = Column(Float, nullable=True)
    cmc_market_cap = Column(Float, nullable=True)
    cmc_volume_24h = Column(Float, nullable=True)
    cmc_percent_change_24h = Column(Float, nullable=True)
    cmc_updated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class ArbitrageOpportunity(Base):
    """Модель арбитражной возможности"""

    __tablename__ = "arbitrage_opportunities"

    id = Column(Integer, primary_key=True)

    # Символ
    symbol = Column(String(20), nullable=False)
    base_asset = Column(String(20), nullable=False)
    quote_asset = Column(String(10), nullable=False, default="USDT")

    # Биржи
    buy_exchange = Column(String(50), nullable=False)
    sell_exchange = Column(String(50), nullable=False)

    # Цены
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    min_buy_price = Column(Float, nullable=True)
    max_buy_price = Column(Float, nullable=True)
    min_sell_price = Column(Float, nullable=True)
    max_sell_price = Column(Float, nullable=True)

    # Объемы
    volume_asset = Column(Float, nullable=False)  # Объем в монетах
    volume_usd = Column(Float, nullable=False)  # Объем в USD
    buy_orders_used = Column(Integer, nullable=False)  # Количество ордеров на покупку
    sell_orders_used = Column(Integer, nullable=False)  # Количество ордеров на продажу

    # Комиссии
    buy_fee_percent = Column(Float, nullable=False, default=0)
    sell_fee_percent = Column(Float, nullable=False, default=0)
    buy_fee_usd = Column(Float, nullable=False, default=0)
    sell_fee_usd = Column(Float, nullable=False, default=0)
    transfer_fee_usd = Column(Float, nullable=False, default=0)
    total_fee_usd = Column(Float, nullable=False, default=0)
    total_fee_percent = Column(Float, nullable=False, default=0)

    # Спреды
    gross_spread_percent = Column(Float, nullable=False, default=0)
    net_spread_percent = Column(Float, nullable=False, default=0)

    # Прибыль
    gross_profit_usd = Column(Float, nullable=False, default=0)
    net_profit_usd = Column(Float, nullable=False, default=0)
    net_profit_percent = Column(Float, nullable=False, default=0)

    # Сеть
    network = Column(String(20), nullable=True)

    # Статус
    is_active = Column(Boolean, default=True)  # Актуальна ли еще возможность
    is_executed = Column(Boolean, default=False)  # Была ли исполнена
    disappeared_at = Column(DateTime, nullable=True)  # Когда исчезла

    # Временные метки
    detected_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Ссылки
    buy_trade_url = Column(String(200), nullable=True)
    sell_trade_url = Column(String(200), nullable=True)


class ScannerLog(Base):
    """Модель логов сканера"""

    __tablename__ = "scanner_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now())
    level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    scan_cycle = Column(Integer, nullable=True)
    opportunities_found = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)


class ScannerStats(Base):
    """Модель статистики сканера"""

    __tablename__ = "scanner_stats"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, server_default=func.now())
    total_opportunities = Column(Integer, default=0)
    total_profit_usd = Column(Float, default=0)
    avg_profit_percent = Column(Float, default=0)
    max_profit_usd = Column(Float, default=0)
    exchanges_analyzed = Column(Integer, default=0)
    pairs_analyzed = Column(Integer, default=0)
    scan_duration_seconds = Column(Float, default=0)
