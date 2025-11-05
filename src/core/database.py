from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import asyncpg


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)  # Set to False to reduce noise
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def setup_vector_extension(self):
        """Setup pgvector extension for embeddings"""
        async with self.engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()


# Global database instance - will be initialized in main.py
db = None


async def get_db_session():
    """Get database session"""
    if db is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    async for session in db.get_session():
        yield session
