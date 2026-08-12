# tests/test_track_a/test_offer_service.py
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.core.factories import get_application_service, get_offer_service
from app.models.domain import Offer
from app.models.enums import ApplicationStatus, OfferStatus
from app.schemas.offer import OfferDecisionRequest


async def _create_offer(
    db_session,
    application_id,
    branch_id,
    status=OfferStatus.PENDING,
    expires_in_hours=48,
    round_number=1,
):
    offer = Offer(
        application_id=application_id,
        branch_id=branch_id,
        round_number=round_number,
        status=status,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
    )
    db_session.add(offer)
    await db_session.flush()
    await db_session.refresh(offer)
    return offer


# ---------------- list_my_offers ----------------


@pytest.mark.asyncio
async def test_list_my_offers_empty_when_no_application(db_session, test_student):
    offer_service = get_offer_service(db_session)
    result = await offer_service.list_my_offers(test_student)
    assert result == []


@pytest.mark.asyncio
async def test_list_my_offers_returns_offers_for_application(
    db_session, test_student, test_application, test_branch
):
    offer_service = get_offer_service(db_session)
    await _create_offer(db_session, test_application.id, test_branch.id)

    result = await offer_service.list_my_offers(test_student)
    assert len(result) == 1
    assert result[0].branch_id == test_branch.id


# ---------------- check_branch_offered_to_student ----------------


@pytest.mark.asyncio
async def test_check_branch_offered_to_student_false_when_no_offer(
    db_session, test_application, test_branch
):
    offer_service = get_offer_service(db_session)
    result = await offer_service.check_branch_offered_to_student(
        test_application.id, test_branch.id
    )
    assert result is False


@pytest.mark.asyncio
async def test_check_branch_offered_to_student_true_when_offer_exists(
    db_session, test_application, test_branch
):
    offer_service = get_offer_service(db_session)
    await _create_offer(db_session, test_application.id, test_branch.id)
    result = await offer_service.check_branch_offered_to_student(
        test_application.id, test_branch.id
    )
    assert result is True


# ---------------- process_student_decision: guards ----------------


@pytest.mark.asyncio
async def test_process_student_decision_raises_404_when_offer_belongs_to_another_student(
    db_session, test_student, test_application, test_branch
):
    from datetime import date

    from app.core.factories import get_student_service
    from app.schemas.application import ApplicationCreateRequest, PreferenceEntry

    student_service = get_student_service(db_session)
    application_service = get_application_service(db_session)

    other_student = await student_service.create_new_student(
        name="Other Student",
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        password="Pass123!",
        phone=None,
        date_of_birth=date(2003, 4, 12),
    )
    other_application = await application_service.create_student_application(
        other_student,
        ApplicationCreateRequest(
            total_marks=70.0,
            preferences=[PreferenceEntry(branch_id=test_branch.id, preference_order=1)],
        ),
    )

    offer_service = get_offer_service(db_session)
    offer = await _create_offer(db_session, other_application.id, test_branch.id)

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.process_student_decision(
            test_student, offer.id, OfferDecisionRequest(accept=True)
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_process_student_decision_raises_409_when_already_resolved(
    db_session, test_student, test_application, test_branch
):
    offer_service = get_offer_service(db_session)
    offer = await _create_offer(
        db_session, test_application.id, test_branch.id, status=OfferStatus.ACCEPTED
    )

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.process_student_decision(
            test_student, offer.id, OfferDecisionRequest(accept=True)
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_process_student_decision_raises_410_when_expired(
    db_session, test_student, test_application, test_branch
):
    offer_service = get_offer_service(db_session)
    offer = await _create_offer(
        db_session, test_application.id, test_branch.id, expires_in_hours=-1
    )

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.process_student_decision(
            test_student, offer.id, OfferDecisionRequest(accept=True)
        )
    assert exc_info.value.status_code == 410


# ---------------- process_student_decision: accept path ----------------


@pytest.mark.asyncio
async def test_process_student_decision_accept_decrements_seat_and_updates_status(
    db_session, test_student, test_application, test_branch
):
    offer_service = get_offer_service(db_session)
    offer = await _create_offer(db_session, test_application.id, test_branch.id)
    seats_before = test_branch.available_seats

    await offer_service.process_student_decision(
        test_student, offer.id, OfferDecisionRequest(accept=True)
    )

    await db_session.refresh(offer)
    await db_session.refresh(test_branch)
    await db_session.refresh(test_application)

    assert offer.status == OfferStatus.ACCEPTED
    assert offer.responded_at is not None
    assert test_branch.available_seats == seats_before - 1
    assert test_application.status == ApplicationStatus.OFFER_ACCEPTED


@pytest.mark.asyncio
async def test_process_student_decision_accept_raises_409_when_no_seats_remaining(
    db_session, test_student, test_application, test_branch
):
    """
    Direct test of the atomic conditional-UPDATE seat guard: if
    available_seats is already 0, the UPDATE...WHERE available_seats > 0
    should match zero rows, and the service should surface a 409 rather
    than silently going negative.
    """
    offer_service = get_offer_service(db_session)
    test_branch.available_seats = 0
    await db_session.flush()

    offer = await _create_offer(db_session, test_application.id, test_branch.id)

    with pytest.raises(HTTPException) as exc_info:
        await offer_service.process_student_decision(
            test_student, offer.id, OfferDecisionRequest(accept=True)
        )
    assert exc_info.value.status_code == 409
    assert "no seats remaining" in exc_info.value.detail.lower()

    # confirm nothing was partially mutated despite the failure —
    # offer should still be PENDING, not left in some half-updated state
    await db_session.refresh(offer)
    assert offer.status == OfferStatus.PENDING


@pytest.mark.asyncio
async def test_process_student_decision_records_history_entry_on_accept(
    db_session, test_student, test_application, test_branch
):
    from app.core.factories import get_application_history_service

    offer_service = get_offer_service(db_session)
    history_service = get_application_history_service(db_session)
    offer = await _create_offer(db_session, test_application.id, test_branch.id)

    await offer_service.process_student_decision(
        test_student, offer.id, OfferDecisionRequest(accept=True)
    )

    history = await history_service.get_history_for_officer(test_application.id)
    assert any(h.new_status == ApplicationStatus.OFFER_ACCEPTED for h in history)


# ---------------- process_student_decision: reject path ----------------


@pytest.mark.asyncio
async def test_process_student_decision_reject_sets_offer_rejected_status(
    db_session, test_student, test_application, test_branch
):
    offer_service = get_offer_service(db_session)
    offer = await _create_offer(db_session, test_application.id, test_branch.id)

    await offer_service.process_student_decision(
        test_student, offer.id, OfferDecisionRequest(accept=False)
    )

    await db_session.refresh(offer)
    assert offer.status == OfferStatus.REJECTED
    assert offer.responded_at is not None


@pytest.mark.asyncio
async def test_process_student_decision_reject_does_not_touch_branch_seats(
    db_session, test_student, test_application, test_branch
):
    """Rejecting an offer must NOT decrement available_seats — only acceptance should."""
    offer_service = get_offer_service(db_session)
    seats_before = test_branch.available_seats
    offer = await _create_offer(db_session, test_application.id, test_branch.id)

    await offer_service.process_student_decision(
        test_student, offer.id, OfferDecisionRequest(accept=False)
    )

    await db_session.refresh(test_branch)
    assert test_branch.available_seats == seats_before


@pytest.mark.asyncio
async def test_process_student_decision_reject_first_preference_marks_withdrawn(
    db_session, test_student, test_application, test_branch
):
    """
    test_application fixture already seeds a preference for test_branch at
    preference_order=1 — reuse it rather than inserting a duplicate.
    """
    offer_service = get_offer_service(db_session)
    offer = await _create_offer(db_session, test_application.id, test_branch.id)

    await offer_service.process_student_decision(
        test_student, offer.id, OfferDecisionRequest(accept=False)
    )

    await db_session.refresh(test_application)
    assert test_application.status == ApplicationStatus.WITHDRAWN


@pytest.mark.asyncio
async def test_process_student_decision_reject_non_first_preference_marks_offer_rejected(
    db_session, test_student, test_application, test_branch
):
    """
    test_application's preference_order=1 already points to test_branch.
    To test the NON-first-preference path, create a SECOND branch, offer
    that instead, and reject it — test_branch stays the untouched first
    preference, so status should be OFFER_REJECTED, not WITHDRAWN.
    """
    from app.core.factories import get_branch_service
    from app.schemas.branch import BranchCreateRequest

    branch_service = get_branch_service(db_session)
    second_branch = await branch_service.create_branch(
        BranchCreateRequest(
            name="Second Choice",
            code=f"SC{uuid.uuid4().hex[:4]}",
            total_seats=30,
            cutoff_marks=80,
        )
    )

    offer_service = get_offer_service(db_session)
    offer = await _create_offer(
        db_session, test_application.id, second_branch.id
    )  # NOT the first preference

    await offer_service.process_student_decision(
        test_student, offer.id, OfferDecisionRequest(accept=False)
    )

    await db_session.refresh(test_application)
    assert test_application.status == ApplicationStatus.OFFER_REJECTED
