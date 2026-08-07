from app.mail import send_brevo_email  # adjust import path to wherever you saved the file above
from app.models.domain import Application, Offer, Student
from app.core.config import settings


#========================================= SEND OFFER MAIL TO STUDENT ===============================

async def send_offer_email(db, application: Application, offer: Offer) -> None:
    student = await db.get(Student, application.student_id)
    offers_link = f"{settings.PUBLIC_BASE_URL}/offers"

    subject = f"Admission Offer — Round {offer.round_number}"
    html_content = f"""
    <p>Dear {student.name},</p>
    <p>You've received an admission offer in round {offer.round_number}.</p>
    <p>Log in to your account and visit <a href="{offers_link}">your offers page</a> to accept or reject.</p>
    <p>This offer expires on {offer.expires_at.strftime('%d %b %Y, %I:%M %p UTC')}.</p>
    """

    await send_brevo_email(
        to_email=student.email,
        to_name=student.name,
        subject=subject,
        html_content=html_content,
    )