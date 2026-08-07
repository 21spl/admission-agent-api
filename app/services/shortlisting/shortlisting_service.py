import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ApplicationStatus, OfferStatus
from app.models.domain import Application, ShortlistingPreference, Branch, Student, Offer

from app.services.shortlisting.shortlisting_algorithm import (
    Candidate,
    BranchInfo,
    build_rank_key,
    run_deferred_acceptance,
)
from app.services.mailer import send_offer_email

logger = logging.getLogger(__name__)

MAX_ROUNDS = 3
OFFER_RESPONSE_WINDOW_HOURS = 72  # keep in sync with OFFER_TOKEN_TTL_HOURS in offer_tokens.py

# applications eligible to be considered in a shortlisting pass:
# VALIDATED -> first-time entrants (round 1); OFFER_REJECTED / OFFER_EXPIRED
# -> carried forward from a prior round per your no-float rule
ELIGIBLE_STATUSES = (
    ApplicationStatus.VALIDATED,
    ApplicationStatus.OFFER_REJECTED,
    ApplicationStatus.OFFER_EXPIRED,
)


# ======================================== RUN SHORTLISTING ROUND ========================================
async def run_shortlisting_round(db: AsyncSession, round_number: int) -> dict:
    if round_number < 1 or round_number > MAX_ROUNDS:
        raise ValueError(f"round_number must be between 1 and {MAX_ROUNDS}")

    if round_number > 1:
        await _expire_stale_offers(db, round_number - 1)

    seats_remaining = await _compute_remaining_seats(db)
    candidates = await _build_candidate_pool(db)

    branch_rows = (await db.execute(select(Branch))).scalars().all()
    branches = {
        b.id: BranchInfo(
            branch_id=b.id,
            capacity=seats_remaining.get(b.id, 0),
            cutoff_marks=b.cutoff_marks,
        )
        for b in branch_rows
    }

    assignments = run_deferred_acceptance(candidates, branches)
    now = datetime.now(timezone.utc)

    for application_id, branch_id in assignments.items():
        app_row = await db.get(Application, application_id)
        app_row.status = ApplicationStatus.OFFER_MADE

        offer = Offer(
            application_id=app_row.id,
            branch_id=branch_id,
            round_number=round_number,
            status=OfferStatus.PENDING,
            sent_at=now,
            expires_at=now + timedelta(hours=OFFER_RESPONSE_WINDOW_HOURS),
        )
        db.add(offer)
        await db.flush()  # ensure offer.id + relationships are usable if send_offer_email needs them

        await send_offer_email(db, app_row, offer)

    await db.commit()
    return {
        "round": round_number,
        "offers_made": len(assignments),
        "seats_considered": seats_remaining,
    }


# ======================================== EXPIRE STALE OFFERS ========================================

async def _expire_stale_offers(db: AsyncSession, prior_round: int) -> None:
    result = await db.execute(
        select(Offer).where(
            Offer.status == OfferStatus.PENDING,
            Offer.round_number == prior_round,
        )
    )
    stale_offers = result.scalars().all()
    now = datetime.now(timezone.utc)

    expired_count = 0
    deleted_count = 0
    for offer in stale_offers:
        offer.status = OfferStatus.EXPIRED
        offer.responded_at = now

        app_row = await db.get(Application, offer.application_id)
        first_pref_branch_id = await db.scalar(
            select(ShortlistingPreference.branch_id)
            .where(ShortlistingPreference.application_id == app_row.id)
            .order_by(ShortlistingPreference.preference_order.asc())
            .limit(1)
        )

        if first_pref_branch_id == offer.branch_id:
            # timeout on a first-preference offer -> same outcome as an
            # explicit first-preference reject: application withdrawn
            await db.delete(app_row)
            deleted_count += 1
        else:
            app_row.status = ApplicationStatus.OFFER_EXPIRED
            expired_count += 1

    logger.info(
        "Round %d sweep: %d offers expired (carried forward), %d applications deleted (first-pref timeout)",
        prior_round, expired_count, deleted_count,
    )


# ======================================== COMPUTE REMAINING SEATS ========================================

async def _compute_remaining_seats(db: AsyncSession) -> dict:
    accepted_rows = (
        await db.execute(
            select(Offer.branch_id, func.count().label("count"))
            .where(Offer.status == OfferStatus.ACCEPTED)
            .group_by(Offer.branch_id)
        )
    ).all()
    accepted_counts = {row.branch_id: row.count for row in accepted_rows}

    branches = (await db.execute(select(Branch))).scalars().all()
    return {
        b.id: max(b.total_seats - accepted_counts.get(b.id, 0), 0) for b in branches
    }


# ======================================== BUILD CANDIDATE POOL ========================================

async def _build_candidate_pool(db: AsyncSession) -> list[Candidate]:
    applications = (
        (
            await db.execute(
                select(Application).where(Application.status.in_(ELIGIBLE_STATUSES))
            )
        )
        .scalars()
        .all()
    )

    candidates = []
    for app_row in applications:
        pref_rows = (
            await db.execute(
                select(ShortlistingPreference.branch_id)
                .where(ShortlistingPreference.application_id == app_row.id)
                .order_by(ShortlistingPreference.preference_order.asc())
            )
        ).all()
        preferences = [row[0] for row in pref_rows]
        if not preferences:
            continue

        student = await db.get(Student, app_row.student_id)
        if student is None or student.total_marks is None:
            continue  # not yet validated -> shouldn't happen given ELIGIBLE_STATUSES, but defensive

        rank_key = build_rank_key(
            student.total_marks,
            student.marks_maths,
            student.marks_physics,
            student.marks_chemistry,
            student.marks_english,
        )

        candidates.append(
            Candidate(
                application_id=app_row.id,
                student_id=student.id,
                preferences=preferences,
                rank_key=rank_key,
            )
        )
    return candidates