import asyncio
import os

from dotenv import load_dotenv

from sms_sender import SMSNotificationSender

load_dotenv()


async def main() -> None:
    phone_number = input("Phone number (E.164 format, e.g. +1234567890): ").strip()
    message = input("Message:\n")

    if not phone_number:
        raise SystemExit("Phone number is required.")
    if not message:
        raise SystemExit("Message is required.")

    sender = SMSNotificationSender()
    success = await sender.send_sms(phone_number, message)

    if success:
        print(f"SMS sent successfully to {phone_number}")
    else:
        print(f"Failed to send SMS to {phone_number}")


if __name__ == "__main__":
    asyncio.run(main())
