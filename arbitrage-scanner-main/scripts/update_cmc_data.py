#!/usr/bin/env python
"""
Обновление данных CoinMarketCap в базе данных
Запускать при старте сканера или по расписанию
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aiohttp
from datetime import datetime

from backend.database import SessionLocal
from backend.models import TradingPair
from backend.config import Config


async def fetch_top_coins(limit: int = 100) -> list:
    """Загружает топ монет с CoinMarketCap"""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": Config.CMC_API_KEY, "Accept": "application/json"}
    params = {"limit": limit, "convert": "USD"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    print(f"CMC API error: {response.status}")
                    return []
        except Exception as e:
            print(f"CMC API error: {e}")
            return []


async def update_cmc_data():
    """Обновляет CMC данные в таблице trading_pairs"""
    print("=" * 60)
    print("Обновление данных CoinMarketCap")
    print("=" * 60)

    # Загружаем топ монет
    top_coins = await fetch_top_coins(100)

    if not top_coins:
        print("❌ Не удалось загрузить данные CMC")
        return

    print(f"✅ Загружено {len(top_coins)} монет")

    db = SessionLocal()
    updated = 0
    created = 0

    try:
        for coin in top_coins:
            symbol = f"{coin['symbol']}/USDT"
            quote = coin.get("quote", {}).get("USD", {})

            # Ищем существующую пару
            pair = db.query(TradingPair).filter(TradingPair.symbol == symbol).first()

            if pair:
                # Обновляем существующую
                pair.cmc_rank = coin.get("cmc_rank")
                pair.cmc_name = coin.get("name")
                pair.cmc_price_usd = quote.get("price")
                pair.cmc_market_cap = quote.get("market_cap")
                pair.cmc_volume_24h = quote.get("volume_24h")
                pair.cmc_percent_change_24h = quote.get("percent_change_24h")
                pair.cmc_updated_at = datetime.now()
                updated += 1
            else:
                # Создаем новую пару
                pair = TradingPair(
                    symbol=symbol,
                    base_asset=coin["symbol"],
                    quote_asset="USDT",
                    cmc_rank=coin.get("cmc_rank"),
                    cmc_name=coin.get("name"),
                    cmc_price_usd=quote.get("price"),
                    cmc_market_cap=quote.get("market_cap"),
                    cmc_volume_24h=quote.get("volume_24h"),
                    cmc_percent_change_24h=quote.get("percent_change_24h"),
                    cmc_updated_at=datetime.now(),
                )
                db.add(pair)
                created += 1

        db.commit()
        print(f"✅ Обновлено: {updated} пар, создано: {created} пар")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    asyncio.run(update_cmc_data())


if __name__ == "__main__":
    main()
