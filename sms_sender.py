import asyncio
import logging
import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

logger = logging.getLogger(__name__)


class SMSNotificationSender:
    """Send SMS messages via Twilio. Designed to support multiple channels (SMS, WhatsApp, etc.)."""

    def __init__(self) -> None:
        """Initialize Twilio client with credentials from environment variables."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

        if not self.account_sid or not self.auth_token or not self.from_number:
            raise ValueError(
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables must be set"
            )

        self.client = Client(self.account_sid, self.auth_token)

    async def send_sms(self, recipient_phone: str, message: str) -> bool:
        """
        Send SMS message via Twilio.

        Args:
            recipient_phone: Phone number in E.164 format (e.g., '+1234567890')
            message: Message body (max 160 characters for single SMS, or 1600 for multi-part)

        Returns:
            True if successful, False otherwise

        Note:
            Future channel support pattern for WhatsApp:
            - recipient_phone can include channel prefix: 'whatsapp:+1234567890'
            - This method will route to appropriate Twilio API based on prefix
        """
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=recipient_phone,
            )

            logger.info(
                "SMS sent successfully",
                extra={
                    "recipient": recipient_phone,
                    "message_id": msg.sid,
                    "length": len(message),
                },
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send SMS",
                extra={
                    "recipient": recipient_phone,
                    "length": len(message),
                },
            )
            return False


async def main() -> None:
    sender = SMSNotificationSender()
    recepient_phone = os.getenv("RECEPIENT_PHONE_NUMBER")
    await sender.send_sms(recipient_phone=recepient_phone, message="sms_event_notifications")


if __name__ == "__main__":
    # Run main function with default arguments
    from oz_shared import load_op_secrets
    asyncio.run(load_op_secrets())
    asyncio.run(main())