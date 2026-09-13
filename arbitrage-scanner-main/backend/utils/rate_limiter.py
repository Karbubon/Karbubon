import asyncio
import time
from typing import Dict, Any, Optional, List
import ccxt.async_support as ccxt


class RateLimiter:
    """Rate limiter для API запросов"""

    def __init__(self, requests_per_second: int = 30):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: Dict[str, float] = {}

    async def acquire(self, exchange_id: str):
        """Получить разрешение на запрос"""
        now = time.time()
        last_time = self.last_request_time.get(exchange_id, 0)
        elapsed = now - last_time

        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            await asyncio.sleep(wait_time)

        self.last_request_time[exchange_id] = time.time()


class ExchangeManager:
    """Управление подключениями к биржам"""

    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.ws_supported: Dict[str, bool] = {}

    async def create_exchange(
        self, exchange_id: str, config: Optional[Dict] = None
    ) -> ccxt.Exchange:
        """Создает подключение к бирже"""
        if config is None:
            config = {}

        default_config = {
            "enableRateLimit": True,
            "rateLimit": 1000,  # Увеличил до 1 секунды для стабильности
            "timeout": 30000,
        }

        full_config = {**default_config, **config}

        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class(full_config)

            # Загружаем маркеты
            await exchange.load_markets()

            self.exchanges[exchange_id] = exchange
            self.rate_limiters[exchange_id] = RateLimiter(20)
            self.ws_supported[exchange_id] = hasattr(exchange, "watch_ticker")

            print(f"✓ Подключена биржа: {exchange_id}")
            if exchange_id == "bybit":
                # Проверяем, сколько USDT пар
                usdt_pairs = [s for s in exchange.markets if s.endswith("/USDT")]
                print(f"    Bybit: найдено {len(usdt_pairs)} USDT пар")

            return exchange

        except AttributeError:
            print(f"✗ Биржа {exchange_id} не поддерживается ccxt")
            raise
        except Exception as e:
            print(f"✗ Ошибка подключения {exchange_id}: {str(e)[:100]}")
            raise

    async def get_ticker(self, exchange_id: str, symbol: str) -> Dict:
        """Получить тикер (REST)"""
        limiter = self.rate_limiters.get(exchange_id)
        if limiter:
            await limiter.acquire(exchange_id)

        exchange = self.exchanges.get(exchange_id)
        if not exchange:
            return None

        try:
            # Проверяем, существует ли пара на бирже
            if symbol not in exchange.markets:
                return None

            ticker = await exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            return None

    async def get_order_book(self, exchange_id: str, symbol: str, limit: int = 20):
        """Получить стакан ордеров с адаптивным лимитом под биржу"""
        limiter = self.rate_limiters.get(exchange_id)
        if limiter:
            await limiter.acquire(exchange_id)

        exchange = self.exchanges.get(exchange_id)
        if not exchange:
            return None

        # Адаптируем лимит под требования биржи
        actual_limit = limit
        if exchange_id == "kucoin":
            # KuCoin требует 20 или 100
            actual_limit = 20 if limit <= 20 else 100
        elif exchange_id == "bybit":
            actual_limit = min(limit, 200)
        elif exchange_id == "bitget":
            actual_limit = min(limit, 100)
        elif exchange_id == "mexc":
            actual_limit = min(limit, 100)

        try:
            orderbook = await exchange.fetch_order_book(symbol, limit=actual_limit)
            if orderbook and orderbook.get("asks") and orderbook.get("bids"):
                return orderbook
            return None
        except Exception as e:
            # Не спамим ошибками
            return None

    async def close_all(self):
        """Закрывает все соединения корректно"""
        print("\n[ExchangeManager] Закрытие соединений...")
        for exchange_id, exchange in self.exchanges.items():
            try:
                await exchange.close()
                print(f"  ✓ Закрыто: {exchange_id}")
            except Exception as e:
                print(f"  ✗ Ошибка закрытия {exchange_id}: {e}")
        self.exchanges.clear()
        print("[ExchangeManager] Все соединения закрыты")

    def get_connected_exchanges(self) -> list:
        return list(self.exchanges.keys())


# Глобальный экземпляр
exchange_manager = ExchangeManager()
