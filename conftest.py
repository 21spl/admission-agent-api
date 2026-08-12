"""
Shared test fixtures. Every test gets a real async DB session wrapped in
a transaction that is rolled back at the end — so tests run against the
actual dev Neon database, but never leave data behind.
"""
import uuid
from datetime import date
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.core.security import hash_password
from app.database import get_db
from app.main import app  # FastAPI app instance
from app.models.domain import Officer
from app.models.enums import OfficerRole  # DB session factory


# fixture is the dependency pytest creates for our tests and provides to it
# similar to fastapi depends()
@pytest_asyncio.fixture
async def db_session():
    """
    One connection per test, one transaction per test, rolled back at
    teardown — regardless of whether the test itself calls commit().
    Real Neon DB, zero leftover data.
    """
    engine = create_async_engine(settings.DATABASE_URL)
    connection = await engine.connect()
    transaction = await connection.begin()

    session_maker = async_sessionmaker(bind=connection, expire_on_commit=False)
    session: AsyncSession = session_maker()

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()  # <-- this is what keeps your dev DB clean
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """
    An httpx.AsyncClient wired to the FastAPI app, with get_db overridden
    to hand out the SAME rolled-back-at-teardown session used above — so
    requests made through the client and direct service calls in a test
    share one transaction.
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()




@pytest_asyncio.fixture
async def test_student(db_session):
    from app.core.factories import get_student_service

    student_service = get_student_service(db_session)
    student = await student_service.create_new_student(
        name="Test Student",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password="TestPassword123!",
        phone=None,
        date_of_birth=date(2005, 6, 15),
    )
    return student


@pytest_asyncio.fixture
async def test_application(db_session, test_student, test_branch):
    from app.core.factories import get_application_service
    from app.schemas.application import ApplicationCreateRequest, PreferenceEntry

    application_service = get_application_service(db_session)
    data = ApplicationCreateRequest(
        total_marks=85.5,
        preferences=[PreferenceEntry(branch_id=test_branch.id, preference_order=1)],
    )
    application = await application_service.create_student_application(
        test_student, data
    )
    return application


@pytest_asyncio.fixture
async def test_branch(db_session):
    from app.core.factories import get_branch_service
    from app.schemas.branch import BranchCreateRequest

    branch_service = get_branch_service(db_session)
    data = BranchCreateRequest(
        name="Computer Science",
        code=f"CSE{uuid.uuid4().hex[:4]}",  # unique per test run, avoids code-collision across tests
        total_seats=60,
        cutoff_marks=85,
    )
    branch = await branch_service.create_branch(data)
    return branch


"""

@pytest_asyncio.fixture
async def test_offer(db_session, test_application):
    from app.models.domain import Offer
    from app.models.enums import OfferStatus
    now = datetime.now(timezone.utc)

    offer = Offer(
        application_id=test_application.id,
        branch_id=test_application.preferences[0].branch_id,
        round_number=1,
        status=OfferStatus.PENDING,
        sent_at=now,
        expires_at=now + timedelta(minutes = 5),
    )
    db_session.add(offer)
    await db_session.commit()
    return offer

"""


@pytest_asyncio.fixture
async def test_officer(db_session):
    officer = Officer(
        name="Test Admin",
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("TestOfficerPassword123!"),
        role=OfficerRole.ADMIN,
    )

    db_session.add(officer)
    await db_session.flush()

    return officer
