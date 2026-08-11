import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.domain import Student
from app.models.enums import ApplicationStatus, OfferStatus
from app.services.shortlisting.shortlisting_service import ShortlistingService

def _scalar_result(rows):
    """
    Mock result for:

        (await db.execute(...)).scalars().all()
    """
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def _rows_result(rows):
    """
    Mock result for:

        (await db.execute(...)).all()
    """
    result = MagicMock()
    result.all.return_value = rows
    return result

@pytest.mark.asyncio
@pytest.mark.parametrize("round_number", [0, 4, -1, 100])
async def test_run_shortlisting_round_rejects_invalid_round(
    round_number,
):
    db = MagicMock()
    mail_service = MagicMock()

    service = ShortlistingService(
        db=db,
        mail_service=mail_service,
    )

    with pytest.raises(
        ValueError,
        match="round_number must be between 1 and 3",
    ):
        await service.run_shortlisting_round(round_number)

    db.execute.assert_not_called()



@pytest.mark.asyncio
async def test_compute_remaining_seats():
    db = MagicMock()

    cse_id = uuid.uuid4()
    ece_id = uuid.uuid4()
    me_id = uuid.uuid4()

    accepted_rows = [
        MagicMock(branch_id=cse_id, count=30),
        MagicMock(branch_id=ece_id, count=50),
    ]

    cse = MagicMock()
    cse.id = cse_id
    cse.total_seats = 100

    ece = MagicMock()
    ece.id = ece_id
    ece.total_seats = 50

    me = MagicMock()
    me.id = me_id
    me.total_seats = 40

    db.execute = AsyncMock(
        side_effect=[
            _rows_result(accepted_rows),
            _scalar_result([cse, ece, me]),
        ]
    )

    service = ShortlistingService(
        db=db,
        mail_service=MagicMock(),
    )

    result = await service._compute_remaining_seats()

    assert result == {
        cse_id: 70,
        ece_id: 0,
        me_id: 40,
    }

@pytest.mark.asyncio
async def test_build_candidate_pool():
    db = MagicMock()

    application_id = uuid.uuid4()
    student_id = uuid.uuid4()

    branch_1 = uuid.uuid4()
    branch_2 = uuid.uuid4()

    application = MagicMock()
    application.id = application_id
    application.student_id = student_id
    application.status = ApplicationStatus.VALIDATED

    student = MagicMock()
    student.id = student_id
    student.total_marks = 82
    student.marks_maths = 18
    student.marks_physics = 16
    student.marks_chemistry = 20
    student.marks_english = 18
    student.marks_computer_science = 10

    db.execute = AsyncMock(
        side_effect=[
            _scalar_result([application]),
            _rows_result([
                (branch_1,),
                (branch_2,),
            ]),
        ]
    )

    db.get = AsyncMock(return_value=student)

    service = ShortlistingService(
        db=db,
        mail_service=MagicMock(),
    )

    candidates = await service._build_candidate_pool()

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.application_id == application_id
    assert candidate.student_id == student_id
    assert candidate.preferences == [
        branch_1,
        branch_2,
    ]

    db.get.assert_awaited_once_with(
        Student,
        student_id,
    )

@pytest.mark.asyncio
async def test_build_candidate_pool_skips_application_without_preferences():
    db = MagicMock()

    application = MagicMock()
    application.id = uuid.uuid4()
    application.student_id = uuid.uuid4()
    application.status = ApplicationStatus.VALIDATED

    db.execute = AsyncMock(
        side_effect=[
            _scalar_result([application]),
            _rows_result([]),
        ]
    )

    db.get = AsyncMock()

    service = ShortlistingService(
        db=db,
        mail_service=MagicMock(),
    )

    candidates = await service._build_candidate_pool()

    assert candidates == []

    db.get.assert_not_awaited()

@pytest.mark.asyncio
async def test_build_candidate_pool_skips_student_without_marks():
    db = MagicMock()

    application = MagicMock()
    application.id = uuid.uuid4()
    application.student_id = uuid.uuid4()
    application.status = ApplicationStatus.VALIDATED

    student = MagicMock()
    student.id = application.student_id
    student.total_marks = None

    db.execute = AsyncMock(
        side_effect=[
            _scalar_result([application]),
            _rows_result([
                (uuid.uuid4(),),
            ]),
        ]
    )

    db.get = AsyncMock(
        return_value=student
    )

    service = ShortlistingService(
        db=db,
        mail_service=MagicMock(),
    )

    candidates = await service._build_candidate_pool()

    assert candidates == []


@pytest.mark.asyncio
async def test_expire_stale_offer_with_first_preference_withdraws_application():
    db = MagicMock()

    application_id = uuid.uuid4()
    branch_id = uuid.uuid4()

    offer = MagicMock()
    offer.application_id = application_id
    offer.branch_id = branch_id
    offer.round_number = 1
    offer.status = OfferStatus.PENDING

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.OFFER_MADE

    db.execute = AsyncMock(
        side_effect=[
            _scalar_result([offer]),
            MagicMock(),
        ]
    )

    db.get = AsyncMock(
        return_value=application
    )

    # select(ShortlistingPreference...).scalar(...)
    db.scalar = AsyncMock(
        return_value=branch_id
    )

    service = ShortlistingService(
        db=db,
        mail_service=MagicMock(),
    )

    await service._expire_stale_offers(1)

    assert offer.status == OfferStatus.EXPIRED
    assert application.status == ApplicationStatus.WITHDRAWN

    assert offer.responded_at is not None

    assert db.add.call_count == 1

    history = db.add.call_args.args[0]

    assert history.application_id == application_id
    assert history.old_status == ApplicationStatus.OFFER_MADE
    assert history.new_status == ApplicationStatus.WITHDRAWN
    assert history.changed_by == "SYSTEM:SHORTLISTING"

@pytest.mark.asyncio
async def test_expire_stale_offer_non_first_preference_carries_forward():
    db = MagicMock()

    application_id = uuid.uuid4()

    offered_branch_id = uuid.uuid4()
    first_preference_branch_id = uuid.uuid4()

    offer = MagicMock()
    offer.application_id = application_id
    offer.branch_id = offered_branch_id
    offer.round_number = 1
    offer.status = OfferStatus.PENDING

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.OFFER_MADE

    db.execute = AsyncMock(
        return_value=_scalar_result([offer])
    )

    db.get = AsyncMock(
        return_value=application
    )

    db.scalar = AsyncMock(
        return_value=first_preference_branch_id
    )

    service = ShortlistingService(
        db=db,
        mail_service=MagicMock(),
    )

    await service._expire_stale_offers(1)

    assert offer.status == OfferStatus.EXPIRED
    assert application.status == ApplicationStatus.OFFER_EXPIRED

    assert offer.responded_at is not None

    history = db.add.call_args.args[0]

    assert history.application_id == application_id
    assert history.old_status == ApplicationStatus.OFFER_MADE 
    assert history.new_status == ApplicationStatus.OFFER_EXPIRED
    assert history.changed_by == "SYSTEM:SHORTLISTING"


@pytest.mark.asyncio
async def test_run_shortlisting_round_creates_offers():
    db = MagicMock()

    db.flush = AsyncMock()
    db.commit = AsyncMock()

    mail_service = MagicMock()
    mail_service.send_offer_email = AsyncMock()

    application_id = uuid.uuid4()
    branch_id = uuid.uuid4()

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.VALIDATED

    assignments = {
        application_id: branch_id,
    }

    service = ShortlistingService(
        db=db,
        mail_service=mail_service,
    )

    # Round 1 should NOT expire previous offers.
    with patch.object(
        service,
        "_compute_remaining_seats",
        new=AsyncMock(
            return_value={
                branch_id: 1,
            }
        ),
    ) as compute_seats, patch.object(
        service,
        "_build_candidate_pool",
        new=AsyncMock(return_value=[]),
    ) as build_candidates, patch(
        "app.services.shortlisting.shortlisting_service.run_deferred_acceptance",
        return_value=assignments,
    ):
        # Branch query
        branch = MagicMock()
        branch.id = branch_id
        branch.cutoff_marks = 70

        db.execute = AsyncMock(
            return_value=_scalar_result([branch])
        )

        db.get = AsyncMock(
            return_value=application
        )

        result = await service.run_shortlisting_round(1)

    assert result["round"] == 1
    assert result["offers_made"] == 1
    assert result["seats_considered"] == {
        branch_id: 1,
    }

    assert application.status == ApplicationStatus.OFFER_MADE

    compute_seats.assert_awaited_once()
    build_candidates.assert_awaited_once()

    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()

    mail_service.send_offer_email.assert_awaited_once()

    sent_application, offer = (
        mail_service.send_offer_email.await_args.args
    )

    assert sent_application is application
    assert offer.application_id == application_id
    assert offer.branch_id == branch_id
    assert offer.round_number == 1
    assert offer.status == OfferStatus.PENDING
    assert offer.sent_at is not None
    assert offer.expires_at is not None


@pytest.mark.asyncio
async def test_run_shortlisting_round_creates_status_history():
    db = MagicMock()

    db.flush = AsyncMock()
    db.commit = AsyncMock()

    mail_service = MagicMock()
    mail_service.send_offer_email = AsyncMock()

    application_id = uuid.uuid4()
    branch_id = uuid.uuid4()

    application = MagicMock()
    application.id = application_id
    application.status = ApplicationStatus.VALIDATED

    service = ShortlistingService(
        db=db,
        mail_service=mail_service,
    )

    with patch.object(
        service,
        "_compute_remaining_seats",
        new=AsyncMock(
            return_value={branch_id: 1}
        ),
    ), patch.object(
        service,
        "_build_candidate_pool",
        new=AsyncMock(return_value=[]),
    ), patch(
        "app.services.shortlisting.shortlisting_service.run_deferred_acceptance",
        return_value={
            application_id: branch_id,
        },
    ):
        branch = MagicMock()
        branch.id = branch_id
        branch.cutoff_marks = 70

        db.execute = AsyncMock(
            return_value=_scalar_result([branch])
        )

        db.get = AsyncMock(
            return_value=application
        )

        await service.run_shortlisting_round(1)

    assert application.status == ApplicationStatus.OFFER_MADE

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]

    histories = [
        obj
        for obj in added_objects
        if obj.__class__.__name__ == "ApplicationStatusHistory"
    ]

    assert len(histories) == 1

    history = histories[0]

    assert history.application_id == application_id
    assert history.old_status == ApplicationStatus.VALIDATED
    assert history.new_status == ApplicationStatus.OFFER_MADE
    assert history.changed_by == "SYSTEM:SHORTLISTING"

@pytest.mark.asyncio
async def test_round_two_expires_round_one_offers_first():
    db = MagicMock()
    mail_service = MagicMock()

    service = ShortlistingService(
        db=db,
        mail_service=mail_service,
    )

    expire = AsyncMock()
    service._expire_stale_offers = expire

    service._compute_remaining_seats = AsyncMock(
        return_value={}
    )

    service._build_candidate_pool = AsyncMock(
        return_value=[]
    )

    with patch(
        "app.services.shortlisting.shortlisting_service.run_deferred_acceptance",
        return_value={},
    ):
        db.execute = AsyncMock(
            return_value=_scalar_result([])
        )

        db.commit = AsyncMock()

        await service.run_shortlisting_round(2)

    expire.assert_awaited_once_with(1)



@pytest.mark.asyncio
async def test_round_three_expires_round_two_offers_first():
    db = MagicMock()
    mail_service = MagicMock()

    service = ShortlistingService(
        db=db,
        mail_service=mail_service,
    )

    expire = AsyncMock()
    service._expire_stale_offers = expire

    service._compute_remaining_seats = AsyncMock(
        return_value={}
    )

    service._build_candidate_pool = AsyncMock(
        return_value=[]
    )

    with patch(
        "app.services.shortlisting.shortlisting_service.run_deferred_acceptance",
        return_value={},
    ):
        db.execute = AsyncMock(
            return_value=_scalar_result([])
        )

        db.commit = AsyncMock()

        await service.run_shortlisting_round(3)

    expire.assert_awaited_once_with(2)

@pytest.mark.asyncio
async def test_run_shortlisting_round_with_no_assignments():
    db = MagicMock()

    db.flush = AsyncMock()
    db.commit = AsyncMock()

    mail_service = MagicMock()
    mail_service.send_offer_email = AsyncMock()

    branch_id = uuid.uuid4()

    service = ShortlistingService(
        db=db,
        mail_service=mail_service,
    )

    service._compute_remaining_seats = AsyncMock(
        return_value={
            branch_id: 10,
        }
    )

    service._build_candidate_pool = AsyncMock(
        return_value=[]
    )

    with patch(
        "app.services.shortlisting.shortlisting_service.run_deferred_acceptance",
        return_value={},
    ):
        branch = MagicMock()
        branch.id = branch_id
        branch.cutoff_marks = 70

        db.execute = AsyncMock(
            return_value=_scalar_result([branch])
        )

        result = await service.run_shortlisting_round(1)

    assert result == {
        "round": 1,
        "offers_made": 0,
        "seats_considered": {
            branch_id: 10,
        },
    }

    mail_service.send_offer_email.assert_not_awaited()
    db.flush.assert_not_awaited()
    db.commit.assert_awaited_once()