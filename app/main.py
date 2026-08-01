from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.database import get_db
from app.routers import auth

app = FastAPI(title=settings.PROJECT_NAME)


# include the authentication router
app.include_router(auth.router)

@app.get("/health", status_code=200)
async def system_health_check(db: AsyncSession = Depends(get_db)):
    """
    Phase 1 Verification Route.
    Confirms FastAPI successfully boots and reads from your live cloud Neon database.
    """
    try:
        # Run a micro SQL evaluation test query on Neon
        result = await db.execute(text("SELECT 1"))
        db_status = "connected" if result.scalar() == 1 else "unreachable"
    except Exception as e:
        db_status = f"connection error: {str(e)}"

    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database_status": db_status
    }
