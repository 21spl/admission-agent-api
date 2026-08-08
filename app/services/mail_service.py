from textwrap import dedent

from app.core.config import settings
from app.mail import (
    send_brevo_email,
)
from app.models.domain import Application, Offer, Student
from app.models.enums import NotificationStatus, NotificationType
from app.schemas.notification import NotificationLogCreate
from app.services.notification_service import NotificationService


class MailService:
    def __init__(self, db, notification_service: NotificationService) -> None:
        self.db = db
        self.notification_service = notification_service

    async def send_offer_email(
        self,
        application: Application,
        offer: Offer,
    ) -> None:
        # Uses self.db directly from the instance
        student = await self.db.get(Student, application.student_id)
        if not student:
            raise ValueError(f"Student {application.student_id} not found")

        offers_link = f"{settings.PUBLIC_BASE_URL}/offers"
        formatted_expiry = offer.expires_at.strftime("%d %b %Y, %I:%M %p UTC")

        subject = f"Admission Offer — Round {offer.round_number}"
        html_content = dedent(
            f"""\
            <p>Dear {student.name},</p>
            <p>You've received an admission offer in round {offer.round_number}.</p>
            <p>Log in to your account and visit <a href="{offers_link}">your offers page</a> to accept or reject.</p>
            <p>This offer expires on {formatted_expiry}.</p>
            """
        )

        await send_brevo_email(
            to_email=student.email,
            to_name=student.name,
            subject=subject,
            html_content=html_content.strip(),
        )
        # after sending mail, we need to log it in the notification log
        # but first we need to create data according to NotificationLogCreate schema
        await self.notification_service.log_notification(
            NotificationLogCreate(
                application_id=application.id,
                recipient_email=student.email,
                type=NotificationType.SHORTLIST_OFFER,
                status=NotificationStatus.SENT,
            )
        )
