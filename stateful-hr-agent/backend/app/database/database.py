import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# In a real environment, load from .env or config
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/hr_agent_db"
)

engine = create_async_engine(
    DATABASE_URL, 
    echo=True, 
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
