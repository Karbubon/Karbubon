#!/usr/bin/env python
"""
Инициализация базы данных для сканера v2
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.models import Exchange


def init_database():
    """Создает все таблицы и заполняет начальными данными"""

    print("=" * 60)
    print("Инициализация базы данных для Arbitrage Scanner v2")
    print("=" * 60)

    # Создаем таблицы
    print("\n📊 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно")

    # Добавляем биржи
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Проверяем, есть ли уже данные
        if session.query(Exchange).count() == 0:
            print("\n📈 Добавление бирж...")
            exchanges = [
                Exchange(name="MEXC", ccxt_id="mexc"),
                Exchange(name="Bitget", ccxt_id="bitget"),
                Exchange(name="KuCoin", ccxt_id="kucoin"),
                Exchange(name="Bybit", ccxt_id="bybit"),
            ]
            for ex in exchanges:
                session.add(ex)
            session.commit()
            print(f"✅ Добавлено {len(exchanges)} бирж")

        print("\n✅ Инициализация завершена успешно!")

    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_database()
