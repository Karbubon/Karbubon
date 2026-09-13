#!/usr/bin/env python
"""
Арбитражный сканер v2.0 - REST версия с комиссиями и сетями
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import hashlib
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiohttp
import ccxt.async_support as ccxt  # type: ignore

from backend.config import Config
from backend.database import SessionLocal
from backend.models import ArbitrageOpportunity, ScannerLog, TradingPair


@dataclass
class ExchangeInfo:
    """Информация о бирже"""

    id: str
    name: str
    ccxt_instance: ccxt.Exchange
    symbols: List[str] = field(default_factory=list)
    connected: bool = False


@dataclass
class CoinInfo:
    """Информация о монете"""

    symbol: str
    name: str
    cmc_rank: int
    price_usd: float


class ArbitrageScannerV2:
    """Арбитражный сканер с комиссиями и сетями"""

    def __init__(self):
        self.exchanges: Dict[str, ExchangeInfo] = {}
        self.common_pairs: Dict[str, List[str]] = {}
        self.exchange_pairs: Dict[str, List[str]] = {}
        self.top_coins: Dict[str, CoinInfo] = {}
        self.orderbooks: Dict[str, Dict[str, Dict]] = {}

        self.is_running = False

        # Настройки из Config
        self.cmc_api_key = Config.CMC_API_KEY
        self.top_n = Config.TOP_COINS_LIMIT
        self.orderbook_depth = Config.ORDERBOOK_DEPTH
        self.scan_interval = Config.SCAN_INTERVAL
        self.max_volume_usd = Config.MAX_VOLUME_USD
        self.min_profit_percent = Config.MIN_PROFIT_PERCENT

        # Комиссии
        self.exchange_fees = Config.EXCHANGE_FEES
        self.transfer_fees = Config.TRANSFER_FEES
        self.asset_networks = Config.ASSET_NETWORKS

        # Активные арбитражи
        self.active_arbitrages = {}
        self.arbitrage_counter = 0
        self.stats = {"arbitrages_found": 0, "start_time": None}

    async def initialize(self):
        """Инициализация"""
        print("\n" + "=" * 60)
        print("🔄 АРБИТРАЖНЫЙ СКАНЕР v2.0 (REST)")
        print("=" * 60)
        print("Настройки:")
        print(f"  - Макс. объем сделки: ${self.max_volume_usd}")
        print(f"  - Мин. прибыль: {self.min_profit_percent}%")
        print(f"  - Глубина стакана: {self.orderbook_depth}")
        print(f"  - Интервал: {self.scan_interval} сек")
        print("=" * 60)

        # Деактивируем старые арбитражи при старте
        await self._deactivate_old_opportunities_before_run()

        await self.step1_load_markets()
        await self.step2_match_pairs()
        await self.step3_load_cmc_top()
        await self.step4_filter_by_cmc()

        await self.run()

    async def step1_load_markets(self):
        """Загрузка маркетов"""
        print("\n📊 ШАГ 1: Загрузка маркетов...")

        tasks = []
        for exch_config in Config.EXCHANGES:
            task = asyncio.create_task(self._load_exchange(exch_config))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        for result in results:
            if result:
                print(f"  ✅ {result['name']}: {result['count']} USDT пар")

        print(f"\n  📈 ИТОГО: {len(self.exchanges)} бирж")

    async def _load_exchange(self, exch_config: dict) -> Optional[Dict]:
        """Загрузка одной биржи"""
        try:
            exchange_class = getattr(ccxt, exch_config["id"])
            exchange = exchange_class(
                {
                    "enableRateLimit": True,
                    "rateLimit": 1000,
                    "timeout": 30000,
                }
            )

            await exchange.load_markets()

            usdt_symbols = [
                s
                for s, m in exchange.markets.items()
                if m.get("quote") == "USDT" and m.get("active")
            ]

            self.exchanges[exch_config["name"]] = ExchangeInfo(
                id=exch_config["id"],
                name=exch_config["name"],
                ccxt_instance=exchange,
                symbols=usdt_symbols,
                connected=True,
            )

            return {"name": exch_config["name"], "count": len(usdt_symbols)}

        except Exception as e:
            print(f"  ⚠ {exch_config['name']}: {str(e)[:50]}")
            return None

    async def step2_match_pairs(self):
        """Матчинг пар"""
        print("\n🔗 ШАГ 2: Матчинг общих пар...")

        all_symbols = set()
        for ex in self.exchanges.values():
            all_symbols.update(ex.symbols)

        self.common_pairs = {}
        for symbol in all_symbols:
            exchanges = []
            for name, ex in self.exchanges.items():
                if symbol in ex.symbols:
                    exchanges.append(name)
            if len(exchanges) >= 2:
                self.common_pairs[symbol] = exchanges

        self.exchange_pairs = defaultdict(list)
        for symbol, exchanges in self.common_pairs.items():
            for name in exchanges:
                self.exchange_pairs[name].append(symbol)

        print(f"  📈 Пар на 2+ биржах: {len(self.common_pairs)}")
        for name, pairs in sorted(
            self.exchange_pairs.items(), key=lambda x: -len(x[1])
        ):
            print(f"     - {name}: {len(pairs)} пар")

    async def step3_load_cmc_top(self):
        """Загружает топ монет из БД (данные уже обновлены)"""
        print("\n📊 ШАГ 3: Загрузка топа CoinMarketCap...")

        # Если еще нет данных в БД, загружаем из API
        db = SessionLocal()
        try:
            count = (
                db.query(TradingPair).filter(TradingPair.cmc_rank.isnot(None)).count()
            )
            if count == 0:
                await self._update_cmc_data()

            # Загружаем топ из БД
            pairs = (
                db.query(TradingPair)
                .filter(TradingPair.cmc_rank.isnot(None))
                .order_by(TradingPair.cmc_rank)
                .limit(self.top_n)
                .all()
            )

            for pair in pairs:
                self.top_coins[pair.symbol] = CoinInfo(
                    symbol=pair.symbol,
                    name=pair.cmc_name or pair.base_asset,
                    cmc_rank=pair.cmc_rank,
                    price_usd=pair.cmc_price_usd or 0,
                )

            print(f"  ✅ Загружено {len(self.top_coins)} монет из топ-{self.top_n}")

        except Exception as e:
            print(f"  ⚠ Ошибка загрузки CMC из БД: {e}")
        finally:
            db.close()

    async def step4_filter_by_cmc(self):
        """Фильтрация по CMC"""
        print("\n🎯 ШАГ 4: Фильтрация по топу CMC...")

        if not self.top_coins:
            print("  ⚠ Нет данных CMC, работаем со всеми")
            return

        filtered = {s: e for s, e in self.common_pairs.items() if s in self.top_coins}

        removed = len(self.common_pairs) - len(filtered)
        self.common_pairs = filtered

        self.exchange_pairs = defaultdict(list)
        for symbol, exchanges in self.common_pairs.items():
            for name in exchanges:
                self.exchange_pairs[name].append(symbol)

        print(f"  📈 Осталось пар: {len(self.common_pairs)} (удалено {removed})")
        for name, pairs in sorted(
            self.exchange_pairs.items(), key=lambda x: -len(x[1])
        ):
            print(f"     - {name}: {len(pairs)} пар")

    def _check_network_compatibility(
        self, symbol: str, buy_exchange: str, sell_exchange: str
    ) -> Tuple[bool, str, float]:
        """
        Проверяет совместимость сетей между биржами
        Returns: (is_compatible, network_name, transfer_fee)
        """
        base_asset = symbol.split("/")[0]

        # Получаем доступные сети для актива
        if base_asset not in self.asset_networks:
            return False, "", 0

        available_networks = self.asset_networks[base_asset]

        # В реальном проекте здесь нужно проверять какие сети поддерживает каждая биржа
        # Пока упрощенно - берем первую доступную сеть
        for network in available_networks:
            transfer_fee = self.transfer_fees.get(network, 0.5)
            return True, network, transfer_fee

        return False, "", 0

    async def run(self):
        """Основной цикл"""
        print("\n" + "=" * 60)
        print("✅ СКАНЕР ЗАПУЩЕН")
        print("=" * 60)

        self.is_running = True
        self.stats["start_time"] = datetime.now()

        # Запускаем параллельные задачи для каждой биржи
        tasks = []
        for name, ex_info in self.exchanges.items():
            if name in self.exchange_pairs:
                symbols = self.exchange_pairs[name]
                task = asyncio.create_task(self._exchange_worker(ex_info, symbols))
                tasks.append(task)
                print(f"  🔄 {name}: мониторинг {len(symbols)} пар")

        # Запускаем анализатор
        analyzer = asyncio.create_task(self._analyzer_loop())
        tasks.append(analyzer)

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            await self.stop()

    async def _exchange_worker(self, ex_info: ExchangeInfo, symbols: List[str]):
        """Воркер для одной биржи - REST polling"""
        exchange = ex_info.ccxt_instance
        name = ex_info.name

        semaphore = asyncio.Semaphore(5)

        print(f"\n🔄 {name}: загрузка стаканов для {len(symbols)} пар...")

        cycle = 0
        while self.is_running:
            cycle += 1
            start_time = time.time()

            print(
                f"\n  📊 {name} (цикл {cycle}) - начата загрузка {len(symbols)} стаканов..."
            )

            tasks = []
            for symbol in symbols:
                task = asyncio.create_task(
                    self._fetch_orderbook_with_semaphore(
                        semaphore, exchange, name, symbol
                    )
                )
                tasks.append(task)

            # Выполняем все задачи
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Подсчет результатов
            success_count = 0
            error_count = 0
            for r in results:
                if r is not None and not isinstance(r, Exception):
                    success_count += 1
                elif isinstance(r, Exception):
                    error_count += 1

            elapsed = time.time() - start_time

            print(
                f"  📊 {name} (цикл {cycle}) - ЗАВЕРШЕН: успешно {success_count}/{len(symbols)}, ошибок {error_count}, время {elapsed:.1f}с"
            )

            # Если стаканы не загружаются, показываем пример ошибки
            if success_count == 0 and error_count > 0:
                for r in results:
                    if isinstance(r, Exception):
                        print(f"    ⚠ Пример ошибки: {str(r)[:150]}")
                        break

            # Проверяем, есть ли стаканы в кэше
            if success_count > 0:
                print(
                    f"  📊 {name}: стаканы сохранены в orderbooks: {len([s for s in self.orderbooks if name in self.orderbooks[s]])} пар"
                )

            await asyncio.sleep(self.scan_interval)

    async def _fetch_orderbook_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        exchange: ccxt.Exchange,
        name: str,
        symbol: str,
    ):
        """Запрос стакана с семафором и отладкой"""
        async with semaphore:
            try:
                # Отладочный вывод редко (каждый 10-й запрос)
                # if hash(symbol) % 10 == 0:
                #     print(f"    🔍 {name}: запрос {symbol}...")

                orderbook = await exchange.fetch_order_book(
                    symbol, limit=self.orderbook_depth
                )
                if orderbook and orderbook.get("asks") and orderbook.get("bids"):
                    if symbol not in self.orderbooks:
                        self.orderbooks[symbol] = {}
                    self.orderbooks[symbol][name] = orderbook

                    if int(hashlib.md5(symbol.encode()).hexdigest(), 16) % 10 == 0:
                        print(
                            f" ✅ {name}: {symbol} - получен (asks: {len(orderbook['asks'])}, bids: {len(orderbook['bids'])})"
                        )
                    return True
                else:
                    if int(hashlib.md5(symbol.encode()).hexdigest(), 16) % 10 == 0:
                        print(f" ⚠ {name}: {symbol} - пустой стакан")
                    return None
            except Exception as e:
                if int(hashlib.md5(symbol.encode()).hexdigest(), 16) % 5 == 0:  # Показываем каждую 5-ю ошибку
                    print(f" ❌ {name}: {symbol} - ошибка: {str(e)[:80]}")
                return None

    async def _analyzer_loop(self):
        """Анализатор спредов с комиссиями и сетями"""
        last_deactivation = 0

        while self.is_running:
            try:
                await self._analyze_arbitrages()

                # Деактивируем старые возможности каждые 30 секунд
                now = time.time()
                if now - last_deactivation > 30:
                    await self._deactivate_old_opportunities()
                    last_deactivation = now

                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)

    async def _analyze_arbitrages(self):
        """Анализ спредов с учетом комиссий и сетей"""
        for symbol, exchange_orderbooks in self.orderbooks.items():
            if len(exchange_orderbooks) < 2:
                continue

            exchanges = list(exchange_orderbooks.keys())

            for i in range(len(exchanges)):
                for j in range(i + 1, len(exchanges)):
                    buy_ex = exchanges[i]
                    sell_ex = exchanges[j]

                    buy_ob = exchange_orderbooks[buy_ex]
                    sell_ob = exchange_orderbooks[sell_ex]

                    if not buy_ob.get("asks") or not sell_ob.get("bids"):
                        continue

                    best_ask = buy_ob["asks"][0][0]
                    best_bid = sell_ob["bids"][0][0]

                    if best_ask >= best_bid:
                        continue

                    # ФИЛЬТР 1: Проверка сетей
                    is_compatible, network, transfer_fee = (
                        self._check_network_compatibility(symbol, buy_ex, sell_ex)
                    )

                    if not is_compatible:
                        continue

                    # Рассчитываем спред с комиссиями
                    buy_fee = self.exchange_fees.get(buy_ex, 0.002)
                    sell_fee = self.exchange_fees.get(sell_ex, 0.002)

                    # Грязный спред
                    gross_spread = ((best_bid - best_ask) / best_ask) * 100

                    # Комиссии в процентах
                    total_fee_percent = (buy_fee + sell_fee) * 100 + (
                        transfer_fee / self.max_volume_usd * 100
                    )

                    # Чистый спред после комиссий
                    net_spread = gross_spread - total_fee_percent

                    # ФИЛЬТР 2: Проверка минимальной прибыли
                    if net_spread < self.min_profit_percent:
                        continue

                    # Матчим объемы
                    match = self._match_volumes(buy_ob["asks"], sell_ob["bids"])

                    if match and match.get("matched_volume", 0) > 0:
                        # Пересчитываем прибыль с учетом комиссий
                        buy_volume_usd = match["buy_volume_usd"]
                        sell_volume_usd = match["sell_volume_usd"]

                        buy_fee_usd = buy_volume_usd * buy_fee
                        sell_fee_usd = sell_volume_usd * sell_fee

                        gross_profit_usd = sell_volume_usd - buy_volume_usd
                        net_profit_usd = (
                            gross_profit_usd - buy_fee_usd - sell_fee_usd - transfer_fee
                        )
                        net_profit_percent = (
                            (net_profit_usd / buy_volume_usd) * 100
                            if buy_volume_usd > 0
                            else 0
                        )

                        if (
                            net_profit_usd > 0.01
                            and net_profit_percent >= self.min_profit_percent
                        ):
                            await self._report_arbitrage(
                                symbol,
                                buy_ex,
                                sell_ex,
                                net_profit_usd,
                                net_profit_percent,
                                match,
                                network,
                                transfer_fee,
                                buy_fee,
                                sell_fee,
                            )

    def _match_volumes(self, asks: List, bids: List) -> Optional[Dict]:
        """Матчинг объемов"""
        sorted_asks = sorted(asks, key=lambda x: x[0])
        sorted_bids = sorted(bids, key=lambda x: x[0], reverse=True)

        best_ask = sorted_asks[0][0]
        best_bid = sorted_bids[0][0]

        if best_ask >= best_bid:
            return None

        # Покупка
        remaining = self.max_volume_usd
        buy_volume = 0
        buy_cost = 0
        buy_orders = 0
        buy_prices = []

        for price, amount in sorted_asks:
            if remaining <= 0 or price >= best_bid:
                break
            take = min(amount, remaining / price)
            if take <= 0:
                continue
            buy_volume += take
            buy_cost += price * take
            remaining -= price * take
            buy_orders += 1
            buy_prices.append(price)

        if buy_volume <= 0:
            return None

        # Продажа
        sell_volume = 0
        sell_revenue = 0
        sell_orders = 0
        sell_prices = []

        for price, amount in sorted_bids:
            if sell_volume >= buy_volume or price <= best_ask:
                break
            take = min(amount, buy_volume - sell_volume)
            if take <= 0:
                continue
            sell_volume += take
            sell_revenue += price * take
            sell_orders += 1
            sell_prices.append(price)

        matched = min(buy_volume, sell_volume)

        if matched <= 0 or not buy_prices or not sell_prices:
            return None

        return {
            "matched_volume": matched,
            "buy_volume_usd": buy_cost,
            "sell_volume_usd": sell_revenue,
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "avg_buy_price": buy_cost / matched,
            "avg_sell_price": sell_revenue / matched,
            "min_buy_price": min(buy_prices),
            "max_buy_price": max(buy_prices),
            "min_sell_price": min(sell_prices),
            "max_sell_price": max(sell_prices),
        }

    async def _save_opportunity_to_db(self, opportunity_data: dict):
        """Сохраняет арбитражную возможность в БД (или обновляет существующую)"""
        db = SessionLocal()
        try:
            # Проверяем, есть ли уже активная возможность для этой пары бирж
            existing = (
                db.query(ArbitrageOpportunity)
                .filter(
                    ArbitrageOpportunity.symbol == opportunity_data["symbol"],
                    ArbitrageOpportunity.buy_exchange
                    == opportunity_data["buy_exchange"],
                    ArbitrageOpportunity.sell_exchange
                    == opportunity_data["sell_exchange"],
                    ArbitrageOpportunity.is_active == True,
                )
                .first()
            )

            if existing:
                # Обновляем существующую запись
                existing.buy_price = opportunity_data["avg_buy_price"]
                existing.sell_price = opportunity_data["avg_sell_price"]
                existing.min_buy_price = opportunity_data.get("min_buy_price")
                existing.max_buy_price = opportunity_data.get("max_buy_price")
                existing.min_sell_price = opportunity_data.get("min_sell_price")
                existing.max_sell_price = opportunity_data.get("max_sell_price")
                existing.volume_asset = opportunity_data["matched_volume"]
                existing.volume_usd = opportunity_data["buy_volume_usd"]
                existing.buy_orders_used = opportunity_data["buy_orders"]
                existing.sell_orders_used = opportunity_data["sell_orders"]
                existing.buy_fee_usd = opportunity_data["buy_fee_usd"]
                existing.sell_fee_usd = opportunity_data["sell_fee_usd"]
                existing.transfer_fee_usd = opportunity_data["transfer_fee_usd"]
                existing.total_fee_usd = (
                    opportunity_data["buy_fee_usd"]
                    + opportunity_data["sell_fee_usd"]
                    + opportunity_data["transfer_fee_usd"]
                )
                existing.gross_profit_usd = opportunity_data["gross_profit_usd"]
                existing.net_profit_usd = opportunity_data["net_profit_usd"]
                existing.net_profit_percent = opportunity_data["net_profit_percent"]
                existing.updated_at = datetime.now()
                db.commit()
                print(f"   🔄 Обновлена существующая возможность (ID: {existing.id})")
            else:
                # Получаем или создаем TradingPair
                pair = (
                    db.query(TradingPair)
                    .filter(TradingPair.symbol == opportunity_data["symbol"])
                    .first()
                )

                if not pair:
                    base_asset = opportunity_data["symbol"].split("/")[0]
                    pair = TradingPair(
                        symbol=opportunity_data["symbol"],
                        base_asset=base_asset,
                        quote_asset="USDT",
                    )
                    db.add(pair)
                    db.flush()

                # Создаем новую запись
                opportunity = ArbitrageOpportunity(
                    symbol=opportunity_data["symbol"],
                    base_asset=opportunity_data["symbol"].split("/")[0],
                    quote_asset="USDT",
                    buy_exchange=opportunity_data["buy_exchange"],
                    sell_exchange=opportunity_data["sell_exchange"],
                    buy_price=opportunity_data["avg_buy_price"],
                    sell_price=opportunity_data["avg_sell_price"],
                    min_buy_price=opportunity_data.get("min_buy_price"),
                    max_buy_price=opportunity_data.get("max_buy_price"),
                    min_sell_price=opportunity_data.get("min_sell_price"),
                    max_sell_price=opportunity_data.get("max_sell_price"),
                    volume_asset=opportunity_data["matched_volume"],
                    volume_usd=opportunity_data["buy_volume_usd"],
                    buy_orders_used=opportunity_data["buy_orders"],
                    sell_orders_used=opportunity_data["sell_orders"],
                    buy_fee_percent=opportunity_data["buy_fee_percent"],
                    sell_fee_percent=opportunity_data["sell_fee_percent"],
                    buy_fee_usd=opportunity_data["buy_fee_usd"],
                    sell_fee_usd=opportunity_data["sell_fee_usd"],
                    transfer_fee_usd=opportunity_data["transfer_fee_usd"],
                    total_fee_usd=opportunity_data["buy_fee_usd"]
                    + opportunity_data["sell_fee_usd"]
                    + opportunity_data["transfer_fee_usd"],
                    total_fee_percent=opportunity_data["buy_fee_percent"]
                    + opportunity_data["sell_fee_percent"],
                    gross_spread_percent=opportunity_data["gross_spread"],
                    net_spread_percent=opportunity_data["net_profit_percent"],
                    gross_profit_usd=opportunity_data["gross_profit_usd"],
                    net_profit_usd=opportunity_data["net_profit_usd"],
                    net_profit_percent=opportunity_data["net_profit_percent"],
                    network=opportunity_data.get("network"),
                    is_active=True,
                    detected_at=datetime.now(),
                    buy_trade_url=self._get_trade_url(
                        opportunity_data["buy_exchange"], opportunity_data["symbol"]
                    ),
                    sell_trade_url=self._get_trade_url(
                        opportunity_data["sell_exchange"], opportunity_data["symbol"]
                    ),
                )

                db.add(opportunity)
                db.commit()
                print(f"   ✨ Создана новая возможность (ID: {opportunity.id})")

        except Exception as e:
            print(f"  ⚠ Ошибка сохранения в БД: {e}")
            db.rollback()
        finally:
            db.close()

    async def _deactivate_old_opportunities(self):
        """Деактивирует возможности, которые больше не актуальны"""
        db = SessionLocal()
        try:
            # Находим активные возможности, которые не обновлялись больше 2 минут
            from datetime import timedelta

            timeout = datetime.now() - timedelta(minutes=2)

            old_opportunities = (
                db.query(ArbitrageOpportunity)
                .filter(
                    ArbitrageOpportunity.is_active == True,
                    ArbitrageOpportunity.updated_at < timeout,
                )
                .all()
            )

            for opp in old_opportunities:
                opp.is_active = False
                opp.disappeared_at = datetime.now()
                print(
                    f"   🕒 Деактивирована возможность #{opp.id}: {opp.symbol} {opp.buy_exchange}→{opp.sell_exchange}"
                )

            if old_opportunities:
                db.commit()
        except Exception as e:
            print(f"  ⚠ Ошибка деактивации: {e}")
            db.rollback()
        finally:
            db.close()

    def _get_trade_url(self, exchange: str, symbol: str) -> str:
        """Генерирует URL для торговли на бирже"""
        urls = {
            "MEXC": f"https://www.mexc.com/exchange/{symbol.replace('/', '_')}",
            "Bitget": f"https://www.bitget.com/spot/{symbol.replace('/', '')}",
            "KuCoin": f"https://www.kucoin.com/trade/{symbol.replace('/', '-')}",
            "Bybit": f"https://www.bybit.com/trade/spot/{symbol.replace('/', '')}",
        }
        return urls.get(exchange, "#")

    async def _log_to_db(
        self, level: str, message: str, cycle: Optional[int] = None, opportunities: Optional[int] = None
    ):
        """Логирует событие в БД"""
        db = SessionLocal()
        try:
            log = ScannerLog(
                level=level,
                message=message,
                scan_cycle=cycle,
                opportunities_found=opportunities,
            )
            db.add(log)
            db.commit()
        except Exception:
            pass
        finally:
            db.close()

    async def _report_arbitrage(
        self,
        symbol: str,
        buy_ex: str,
        sell_ex: str,
        profit_usd: float,
        profit_percent: float,
        match: Dict,
        network: str,
        transfer_fee: float,
        buy_fee: float,
        sell_fee: float,
    ):
        """Отчет об арбитраже с сохранением в БД"""

        key = f"{symbol}_{buy_ex}_{sell_ex}"
        now = time.time()

        if key not in self.active_arbitrages:
            self.arbitrage_counter += 1
            self.active_arbitrages[key] = {"number": self.arbitrage_counter, "last": 0}

        info = self.active_arbitrages[key]
        if now - info["last"] < 60:
            return

        info["last"] = now
        self.stats["arbitrages_found"] += 1

        # Рассчитываем дополнительные метрики
        gross_profit_usd = match["sell_volume_usd"] - match["buy_volume_usd"]
        buy_fee_usd = match["buy_volume_usd"] * buy_fee
        sell_fee_usd = match["sell_volume_usd"] * sell_fee
        gross_spread = (
            (match["avg_sell_price"] - match["avg_buy_price"]) / match["avg_buy_price"]
        ) * 100

        # Подготавливаем данные для БД
        opportunity_data = {
            "symbol": symbol,
            "buy_exchange": buy_ex,
            "sell_exchange": sell_ex,
            "avg_buy_price": match["avg_buy_price"],
            "avg_sell_price": match["avg_sell_price"],
            "min_buy_price": match["min_buy_price"],
            "max_buy_price": match["max_buy_price"],
            "min_sell_price": match["min_sell_price"],
            "max_sell_price": match["max_sell_price"],
            "matched_volume": match["matched_volume"],
            "buy_volume_usd": match["buy_volume_usd"],
            "sell_volume_usd": match["sell_volume_usd"],
            "buy_orders": match["buy_orders"],
            "sell_orders": match["sell_orders"],
            "buy_fee_percent": buy_fee * 100,
            "sell_fee_percent": sell_fee * 100,
            "buy_fee_usd": buy_fee_usd,
            "sell_fee_usd": sell_fee_usd,
            "transfer_fee_usd": transfer_fee,
            "gross_spread": gross_spread,
            "gross_profit_usd": gross_profit_usd,
            "net_profit_usd": profit_usd,
            "net_profit_percent": profit_percent,
            "network": network,
        }

        # Сохраняем в БД
        await self._save_opportunity_to_db(opportunity_data)

        # Выводим в консоль
        print(f"\n{'=' * 70}")
        print(f"💰 [АРБИТРАЖ #{info['number']}] {symbol}")
        print(f"{'=' * 70}")
        print(f"\n{profit_percent:.3f}% | {buy_ex}→{sell_ex}")

        print(f"\n📗 ПОКУПКА: {buy_ex}")
        print(
            f"   Цена: {match['avg_buy_price']:.8f} [{match['min_buy_price']:.8f} - {match['max_buy_price']:.8f}]"
        )
        print(
            f"   Объем: ${match['buy_volume_usd']:.2f} | {match['matched_volume']:.4f} монет | {match['buy_orders']} ордеров"
        )
        print(f"   Комиссия: {buy_fee * 100:.2f}% (${buy_fee_usd:.2f})")

        print(f"\n📕 ПРОДАЖА: {sell_ex}")
        print(
            f"   Цена: {match['avg_sell_price']:.8f} [{match['min_sell_price']:.8f} - {match['max_sell_price']:.8f}]"
        )
        print(
            f"   Объем: ${match['sell_volume_usd']:.2f} | {match['matched_volume']:.4f} монет | {match['sell_orders']} ордеров"
        )
        print(f"   Комиссия: {sell_fee * 100:.2f}% (${sell_fee_usd:.2f})")

        print("\n🔗 ПЕРЕВОД:")
        print(f"   Сеть: {network}")
        print(f"   Комиссия: ${transfer_fee:.2f}")

        print("\n💰 ПРИБЫЛЬ:")
        print(f"   Валовая: ${gross_profit_usd:.2f}")
        print(f"   Комиссии: ${buy_fee_usd + sell_fee_usd + transfer_fee:.2f}")
        print(f"   ЧИСТАЯ: +${profit_usd:.2f} ({profit_percent:.3f}%)")
        print("   💾 Сохранено в БД")

    async def stop(self):
        """Остановка"""
        print("\n🛑 Остановка...")
        self.is_running = False

        for ex in self.exchanges.values():
            try:
                await ex.ccxt_instance.close()
            except:
                pass

        print("\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        print(f"   Арбитражей найдено: {self.stats['arbitrages_found']}")

    async def _update_cmc_data(self):
        """Обновляет данные CoinMarketCap в таблице trading_pairs"""
        print("\n📊 Обновление данных CoinMarketCap...")

        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        headers = {"X-CMC_PRO_API_KEY": self.cmc_api_key, "Accept": "application/json"}
        params = {"limit": self.top_n, "convert": "USD"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        top_coins = data.get("data", [])
                        print(f"  ✅ Загружено {len(top_coins)} монет из CMC")

                        db = SessionLocal()
                        updated = 0
                        created = 0

                        try:
                            for coin in top_coins:
                                symbol = f"{coin['symbol']}/USDT"
                                quote = coin.get("quote", {}).get("USD", {})

                                pair = (
                                    db.query(TradingPair)
                                    .filter(TradingPair.symbol == symbol)
                                    .first()
                                )

                                if pair:
                                    # Обновляем существующую
                                    pair.cmc_rank = coin.get("cmc_rank")
                                    pair.cmc_name = coin.get("name")
                                    pair.cmc_price_usd = quote.get("price")
                                    pair.cmc_market_cap = quote.get("market_cap")
                                    pair.cmc_volume_24h = quote.get("volume_24h")
                                    pair.cmc_percent_change_24h = quote.get(
                                        "percent_change_24h"
                                    )
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
                                        cmc_percent_change_24h=quote.get(
                                            "percent_change_24h"
                                        ),
                                        cmc_updated_at=datetime.now(),
                                    )
                                    db.add(pair)
                                    created += 1

                            db.commit()
                            print(
                                f"  📈 Обновлено: {updated} пар, создано: {created} пар"
                            )

                        except Exception as e:
                            print(f"  ❌ Ошибка сохранения CMC данных: {e}")
                            db.rollback()
                        finally:
                            db.close()

                    else:
                        error_data = await response.json()
                        print(
                            f"  ❌ Ошибка CMC API: {error_data.get('status', {}).get('error_message', 'Unknown')}"
                        )

            except Exception as e:
                print(f"  ⚠ Ошибка загрузки CMC: {e}")

    async def _deactivate_old_opportunities_before_run(self):
        """Деактивирует все старые арбитражные возможности при старте сканера"""
        print("\n🔄 Деактивация старых арбитражей...")

        db = SessionLocal()
        try:
            # Находим все активные возможности
            active_opps = (
                db.query(ArbitrageOpportunity)
                .filter(ArbitrageOpportunity.is_active == True)
                .all()
            )

            if not active_opps:
                print("  ✅ Нет активных арбитражей для деактивации")
                return

            # Деактивируем все активные возможности
            for opp in active_opps:
                opp.is_active = False
                opp.disappeared_at = datetime.now()

            db.commit()
            print(f"  ✅ Деактивировано {len(active_opps)} старых арбитражей")

        except Exception as e:
            print(f"  ❌ Ошибка деактивации: {e}")
            db.rollback()
        finally:
            db.close()


async def main():
    scanner = ArbitrageScannerV2()
    await scanner.initialize()


if __name__ == "__main__":
    asyncio.run(main())
