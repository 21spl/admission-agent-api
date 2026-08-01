from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 1. Create the asynchronous cloud database connection engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Prints every SQL transaction to your terminal for easy debugging
    future=True
)

# 2. Build the session constructor template
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. Create a shared declarative base class for your future data models
class Base(DeclarativeBase):
    pass

# 4. Dependency Injection function to yield safe transactional sessions per API call
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



