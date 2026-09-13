import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:test15347@localhost:5432/arbitrage_scanner",
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")

    # Scanner settings
    SCAN_INTERVAL = int(
        os.getenv("SCAN_INTERVAL", "3")
    )  # Интервал сканирования в секундах
    MAX_VOLUME_USD = float(
        os.getenv("MAX_VOLUME_USD", "5000")
    )  # Максимальный объем сделки в USD
    MIN_PROFIT_PERCENT = float(
        os.getenv("MIN_PROFIT_PERCENT", "0.02")
    )  # Минимальная прибыль в %
    MIN_VOLUME_USD = float(
        os.getenv("MIN_VOLUME_USD", "10")
    )  # Минимальный объем для анализа
    ORDERBOOK_DEPTH = int(os.getenv("ORDERBOOK_DEPTH", "20"))  # Глубина стакана
    TOP_COINS_LIMIT = int(os.getenv("TOP_COINS_LIMIT", "100"))  # Топ N монет из CMC

    # CMC API
    CMC_API_KEY = os.getenv("CMC_API_KEY", "c901af39-5dff-4e75-81ff-cfb47df09f91")

    # Commission settings (в процентах)
    EXCHANGE_FEES = {
        "MEXC": 0.002,  # 0.2%
        "Bitget": 0.001,  # 0.1%
        "KuCoin": 0.001,  # 0.1%
        "Bybit": 0.001,  # 0.1%
    }

    # Network transfer fees (в USD)
    TRANSFER_FEES = {
        "TRC20": 0.5,
        "BEP20": 0.3,
        "ERC20": 5.0,
        "SOLANA": 0.02,
        "BTC": 0.0005,
        "ETH": 3.0,
    }

    # Available networks for each asset
    ASSET_NETWORKS = {
        "USDT": ["TRC20", "BEP20", "ERC20"],
        "BTC": ["BTC"],
        "ETH": ["ERC20"],
        "SOL": ["SOLANA"],
    }

    # Rate limits for exchanges (requests per second)
    EXCHANGE_RATE_LIMITS = {
        "mexc": 50,
        "bitget": 50,
        "kucoin": 50,
        "bybit": 50,
    }

    # Exchanges configuration
    EXCHANGES = [
        {"id": "mexc", "name": "MEXC", "rate_limit": 50},
        {"id": "bitget", "name": "Bitget", "rate_limit": 50},
        {"id": "kucoin", "name": "KuCoin", "rate_limit": 50},
        {"id": "bybit", "name": "Bybit", "rate_limit": 50},
    ]
