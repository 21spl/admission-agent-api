import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    Application,
    Branch,
    Offer,
    ShortlistingPreference,
    Student,
)
from app.models.enums import ApplicationStatus, OfferStatus
from app.services.mail_service import MailService
from app.services.shortlisting.shortlisting_algorithm import (
    BranchInfo,
    Candidate,
    build_rank_key,
    run_deferred_acceptance,
)
from app.models.domain import Application, ApplicationStatusHistory, Offer

logger = logging.getLogger(__name__)


class ShortlistingService:

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
    # here we don't consider ApplicationStatus.OFFER_PENDING, cause shortlisting is done only after the round window ends
    # all pending offers are automatically rejected

    def __init__(self, db: AsyncSession, mail_service: MailService): 
        self.db = db
        self.mail_service = mail_service


    # ======================================== RUN SHORTLISTING ROUND ========================================
    async def run_shortlisting_round(self, round_number: int) -> dict:
        if round_number < 1 or round_number > self.MAX_ROUNDS:
            raise ValueError(f"round_number must be between 1 and {self.MAX_ROUNDS}")

        if round_number > 1:
            await self._expire_stale_offers(round_number - 1)

        seats_remaining = await self._compute_remaining_seats()
        candidates = await self._build_candidate_pool()

        branch_rows = (await self.db.execute(select(Branch))).scalars().all()
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
            app_row = await self.db.get(Application, application_id)
            old_status = app_row.status
            app_row.status = ApplicationStatus.OFFER_MADE
            # we need to update the application status history also
            self.db.add(
                ApplicationStatusHistory(
                    application_id=app_row.id,
                    old_status=old_status,
                    new_status=ApplicationStatus.OFFER_MADE,
                    changed_by="SYSTEM:SHORTLISTING",
                )
            )
            

            offer = Offer(
                application_id=app_row.id,
                branch_id=branch_id,
                round_number=round_number,
                status=OfferStatus.PENDING,
                sent_at=now,
                expires_at=now + timedelta(hours=self.OFFER_RESPONSE_WINDOW_HOURS),
            )
            self.db.add(offer)
            await self.db.flush()  # ensure offer.id + relationships are usable if send_offer_email needs them

            await self.mail_service.send_offer_email(app_row, offer)



        await self.db.commit()
        return {
            "round": round_number,
            "offers_made": len(assignments),
            "seats_considered": seats_remaining,
        }


    # ======================================== EXPIRE STALE OFFERS ========================================

    async def _expire_stale_offers(self, prior_round: int) -> None:
        result = await self.db.execute(
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

            app_row = await self.db.get(Application, offer.application_id)

            old_status = app_row.status

            first_pref_branch_id = await self.db.scalar(
                select(ShortlistingPreference.branch_id)
                .where(ShortlistingPreference.application_id == app_row.id)
                .order_by(ShortlistingPreference.preference_order.asc())
                .limit(1)
            )

            
            if first_pref_branch_id == offer.branch_id:
                # timeout on a first-preference offer -> same outcome as an
                # explicit first-preference reject: application withdrawn
                
                app_row.status = ApplicationStatus.WITHDRAWN
                self.db.add(
                    ApplicationStatusHistory(
                        application_id=app_row.id,
                        old_status=old_status,
                        new_status=ApplicationStatus.WITHDRAWN,
                        changed_by="SYSTEM:SHORTLISTING",
                    )
                )
                deleted_count += 1
            else:
                app_row.status = ApplicationStatus.OFFER_EXPIRED
                self.db.add(
                    ApplicationStatusHistory(
                        application_id=app_row.id,
                        old_status=old_status,
                        new_status=ApplicationStatus.OFFER_EXPIRED,
                        changed_by="SYSTEM:SHORTLISTING",
                    )
                )
                expired_count += 1

        logger.info(
            "Round %d sweep: %d offers expired (carried forward), %d applications deleted (first-pref timeout)",
            prior_round, expired_count, deleted_count,
        )


    # ======================================== COMPUTE REMAINING SEATS ========================================

    async def _compute_remaining_seats(self) -> dict:
        accepted_rows = (
            await self.db.execute(
                select(Offer.branch_id, func.count().label("count"))
                .where(Offer.status == OfferStatus.ACCEPTED)
                .group_by(Offer.branch_id)
            )
        ).all()
        accepted_counts = {row.branch_id: row.count for row in accepted_rows}

        branches = (await self.db.execute(select(Branch))).scalars().all()
        return {
            b.id: max(b.total_seats - accepted_counts.get(b.id, 0), 0) for b in branches
        }


    # ======================================== BUILD CANDIDATE POOL ========================================

    async def _build_candidate_pool(self) -> list[Candidate]:
        applications = (
            (
                await self.db.execute(
                    select(Application).where(Application.status.in_(self.ELIGIBLE_STATUSES))
                )
            )
            .scalars()
            .all()
        )

        candidates = []
        for app_row in applications:
            pref_rows = (
                await self.db.execute(
                    select(ShortlistingPreference.branch_id)
                    .where(ShortlistingPreference.application_id == app_row.id)
                    .order_by(ShortlistingPreference.preference_order.asc())
                )
            ).all()
            preferences = [row[0] for row in pref_rows]
            if not preferences:
                continue

            student = await self.db.get(Student, app_row.student_id)
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




    