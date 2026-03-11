import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailNotificationSender:
    
    
    def __init__(self) -> None:
        self.smtp_server = os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("GMAIL_SMTP_PORT", "587"))
        self.sender_email: str = str(os.getenv("GMAIL_SENDER_EMAIL"))
        self.sender_password: str = str(os.getenv("GMAIL_APP_PASSWORD"))

        if not self.sender_email or not self.sender_password:
            raise ValueError("GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD environment variables must be set")

    
    async def send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """Send email via Gmail SMTP"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email

            # Attach body
            part = MIMEText(body, "plain")
            message.attach(part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    recipient_email,
                    message.as_string(),
                )

            logger.info("Email sent successfully", extra={"recipient": recipient_email})
            return True
        except Exception as e:
            logger.error("Failed to send email", extra={"recipient": recipient_email, "error": str(e)})
            return False