# tests/test_track_a/test_application_service.py
import uuid
import pytest
from fastapi import HTTPException

from app.core.factories import get_application_service
from app.schemas.application import ApplicationCreateRequest, PreferenceEntry
from app.models.enums import ApplicationStatus


# ---------------- create_student_application ----------------

@pytest.mark.asyncio
async def test_create_student_application_succeeds_for_new_student(db_session, test_student, test_branch):
    service = get_application_service(db_session)
    data = ApplicationCreateRequest(
        total_marks=78.0,
        preferences=[PreferenceEntry(branch_id=test_branch.id, preference_order=1)],
    )

    application = await service.create_student_application(test_student, data)

    assert application is not None
    assert application.student_id == test_student.id
    assert application.status == ApplicationStatus.STARTED


@pytest.mark.asyncio
async def test_create_student_application_rejects_duplicate(db_session, test_student, test_application, test_branch):
    service = get_application_service(db_session)
    data = ApplicationCreateRequest(
        total_marks=60.0,
        preferences=[PreferenceEntry(branch_id=test_branch.id, preference_order=1)],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.create_student_application(test_student, data)

    assert exc_info.value.status_code == 400
    assert "already active" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_student_application_records_initial_status_history(db_session, test_student, test_branch):
    service = get_application_service(db_session)
    data = ApplicationCreateRequest(
        total_marks=91.0,
        preferences=[PreferenceEntry(branch_id=test_branch.id, preference_order=1)],
    )

    application = await service.create_student_application(test_student, data)

    assert len(application.history) == 1
    assert application.history[0].old_status is None
    assert application.history[0].new_status == ApplicationStatus.STARTED


@pytest.mark.asyncio
async def test_create_student_application_rejects_duplicate_branch_preferences(db_session, test_student, test_branch):
    """
    Schema-level validation, not service-level, but worth confirming it
    actually fires: same branch listed twice should be rejected before
    ever reaching the service.
    """
    with pytest.raises(ValueError, match="Duplicate branches"):
        ApplicationCreateRequest(
            total_marks=70.0,
            preferences=[
                PreferenceEntry(branch_id=test_branch.id, preference_order=1),
                PreferenceEntry(branch_id=test_branch.id, preference_order=2),
            ],
        )


# ---------------- get_student_application ----------------

@pytest.mark.asyncio
async def test_get_student_application_returns_existing(db_session, test_student, test_application):
    service = get_application_service(db_session)
    result = await service.get_student_application(test_student)
    assert result.id == test_application.id


@pytest.mark.asyncio
async def test_get_student_application_raises_404_when_none_exists(db_session, test_student):
    service = get_application_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.get_student_application(test_student)
    assert exc_info.value.status_code == 404


# ---------------- get_application_by_id ----------------

@pytest.mark.asyncio
async def test_get_application_by_id_returns_real_application(db_session, test_application):
    service = get_application_service(db_session)
    fetched = await service.get_application_by_id(test_application.id)
    assert fetched.id == test_application.id


@pytest.mark.asyncio
async def test_get_application_by_id_raises_404_for_unknown_id(db_session):
    service = get_application_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.get_application_by_id(uuid.uuid4())
    assert exc_info.value.status_code == 404


# ---------------- update_application_status ----------------

@pytest.mark.asyncio
async def test_update_application_status_changes_status_and_records_history(db_session, test_application):
    service = get_application_service(db_session)

    updated = await service.update_application_status(
        test_application.id, ApplicationStatus.PENDING_REVIEW, changed_by="officer_test"
    )

    assert updated.status == ApplicationStatus.PENDING_REVIEW
    assert len(updated.history) == 2
    assert updated.history[-1].old_status == ApplicationStatus.STARTED
    assert updated.history[-1].new_status == ApplicationStatus.PENDING_REVIEW
    assert updated.history[-1].changed_by == "officer_test"


@pytest.mark.asyncio
async def test_update_application_status_is_idempotent_no_op_when_status_unchanged(db_session, test_application):
    service = get_application_service(db_session)

    result = await service.update_application_status(
        test_application.id, ApplicationStatus.STARTED, changed_by="officer_test"
    )

    assert result.status == ApplicationStatus.STARTED
    assert len(result.history) == 1  # no duplicate entry from the no-op


@pytest.mark.asyncio
async def test_update_application_status_raises_404_for_unknown_id(db_session):
    service = get_application_service(db_session)
    with pytest.raises(HTTPException) as exc_info:
        await service.update_application_status(
            uuid.uuid4(), ApplicationStatus.PENDING_REVIEW, changed_by="officer_test"
        )
    assert exc_info.value.status_code == 404