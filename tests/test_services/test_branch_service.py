# tests/test_track_a/test_branch_service.py
import uuid
import pytest
from fastapi import HTTPException

from app.core.factories import get_branch_service
from app.schemas.branch import BranchCreateRequest, BranchUpdateRequest


# ---------------- create_branch ----------------

@pytest.mark.asyncio
async def test_create_branch_succeeds_with_valid_data(db_session):
    service = get_branch_service(db_session)
    data = BranchCreateRequest(name="Mechanical Engineering", code="mech1", total_seats=40, cutoff_marks=70)

    branch = await service.create_branch(data)

    assert branch.id is not None
    assert branch.code == "MECH1"  # confirms uppercase normalization
    assert branch.available_seats == branch.total_seats  # seeded equal on creation


@pytest.mark.asyncio
async def test_create_branch_rejects_duplicate_code_case_insensitively(db_session, test_branch):
    """
    Codes are uppercased before comparison — a duplicate submitted in a
    different case should still be rejected, not slip through.
    """
    service = get_branch_service(db_session)
    data = BranchCreateRequest(
        name="Duplicate Attempt",
        code=test_branch.code.lower(),  # deliberately lowercase version of an existing code
        total_seats=30,
        cutoff_marks=60,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_branch(data)

    assert exc_info.value.status_code == 400


# ---------------- get_branch ----------------

@pytest.mark.asyncio
async def test_get_branch_returns_real_branch(db_session, test_branch):
    service = get_branch_service(db_session)
    fetched = await service.get_branch(test_branch.id)
    assert fetched.id == test_branch.id


@pytest.mark.asyncio
async def test_get_branch_raises_404_for_unknown_id(db_session):
    service = get_branch_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.get_branch(uuid.uuid4())
    assert exc_info.value.status_code == 404


# ---------------- list_branches ----------------

@pytest.mark.asyncio
async def test_list_branches_includes_created_branch(db_session, test_branch):
    service = get_branch_service(db_session)
    branches = await service.list_branches()
    assert any(b.id == test_branch.id for b in branches)


# ---------------- update_branch: capacity math ----------------

@pytest.mark.asyncio
async def test_update_branch_increases_total_seats_preserves_occupied(db_session, test_branch):
    """
    test_branch starts at total_seats=60, available_seats=60 (0 occupied).
    Increasing total_seats to 80 with 0 occupied should leave available_seats=80.
    """
    service = get_branch_service(db_session)
    data = BranchUpdateRequest(total_seats=80)

    updated = await service.update_branch(test_branch.id, data)

    assert updated.total_seats == 80
    assert updated.available_seats == 80


@pytest.mark.asyncio
async def test_update_branch_rejects_capacity_below_occupied_seats(db_session, test_branch, db_session_direct_update=None):
    """
    Simulate occupied seats by directly reducing available_seats below
    total_seats (as if offers had been made), then confirm attempting to
    shrink total_seats below the occupied count is rejected with 422.

    NOTE: this manually mutates test_branch.available_seats to simulate
    occupied seats without going through a real offer flow — adjust if
    your OfferService has a more direct way to occupy seats that you'd
    rather test through instead.
    """
    service = get_branch_service(db_session)

    # Simulate 50 occupied seats out of 60 total (available drops to 10)
    test_branch.available_seats = 10
    await db_session.flush()

    data = BranchUpdateRequest(total_seats=40)  # 40 < 50 occupied — should be rejected

    with pytest.raises(HTTPException) as exc_info:
        await service.update_branch(test_branch.id, data)

    assert exc_info.value.status_code == 422
    assert "occupied seats" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_branch_allows_capacity_reduction_above_occupied_seats(db_session, test_branch):
    """Same setup as above, but reducing to a value still >= occupied seats should succeed."""
    service = get_branch_service(db_session)

    test_branch.available_seats = 10  # 50 occupied
    await db_session.flush()

    data = BranchUpdateRequest(total_seats=55)  # 55 >= 50 occupied — should succeed

    updated = await service.update_branch(test_branch.id, data)

    assert updated.total_seats == 55
    assert updated.available_seats == 5  # 55 - 50 occupied = 5 remaining


# ---------------- update_branch: partial field updates ----------------

@pytest.mark.asyncio
async def test_update_branch_updates_name_only_leaves_other_fields_unchanged(db_session, test_branch):
    service = get_branch_service(db_session)
    original_code = test_branch.code
    original_cutoff = test_branch.cutoff_marks

    data = BranchUpdateRequest(name="Renamed Branch")
    updated = await service.update_branch(test_branch.id, data)

    assert updated.name == "Renamed Branch"
    assert updated.code == original_code
    assert updated.cutoff_marks == original_cutoff


@pytest.mark.asyncio
async def test_update_branch_code_rejects_collision_with_different_branch(db_session, test_branch):
    """
    Create a second branch, then attempt to rename test_branch's code to
    match the second branch's code — should be rejected.
    """
    service = get_branch_service(db_session)
    other_data = BranchCreateRequest(name="Other Branch", code="OTHR1", total_seats=20, cutoff_marks=50)
    other_branch = await service.create_branch(other_data)

    data = BranchUpdateRequest(code=other_branch.code)

    with pytest.raises(HTTPException) as exc_info:
        await service.update_branch(test_branch.id, data)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_branch_code_to_same_value_does_not_raise(db_session, test_branch):
    """
    Updating a branch's code to the value it ALREADY has should not trip
    the collision check — the `if updated_code != branch.code` guard
    exists specifically to allow this. Confirms that guard actually works.
    """
    service = get_branch_service(db_session)
    data = BranchUpdateRequest(code=test_branch.code)

    updated = await service.update_branch(test_branch.id, data)

    assert updated.code == test_branch.code  # no exception, no-op essentially