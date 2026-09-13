from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import Config

# Создаем engine с настройками для Windows
engine = create_engine(
    Config.DATABASE_URL,
    pool_size=5,  # уменьшаем для Windows
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,  # установите True для отладки SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Создает все таблицы"""
    Base.metadata.create_all(bind=engine)
