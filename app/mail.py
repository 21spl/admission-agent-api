import logging

import httpx
from pydantic import BaseModel, EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)

BREVO_SEND_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


class EmailRequest(BaseModel):
    to_email: EmailStr
    to_name: str
    subject: str
    html_content: str


async def send_brevo_email(
    to_email: str, to_name: str, subject: str, html_content: str
) -> bool:
    """
    Sends one transactional email via Brevo. Returns True/False rather than
    raising, so a failed email never breaks the caller's loop (e.g. one bad
    address in a batch of offer emails shouldn't abort the whole round).
    """
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": settings.SENDER_NAME, "email": settings.SENDER_EMAIL},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                BREVO_SEND_EMAIL_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            logger.info(
                "Email sent to %s | Brevo message id: %s",
                to_email,
                response.json().get("messageId"),
            )
            return True
        except httpx.HTTPStatusError as exc:
            logger.error("Brevo API error for %s: %s", to_email, exc.response.text)
        except httpx.RequestError as exc:
            logger.error("Network error emailing %s: %s", to_email, exc)
        return False
