"""
Notification module.

Handles sending alerts via WhatsApp or SMS using Twilio.
"""

import logging
from typing import Optional
from twilio.rest import Client

from .config import config

logger = logging.getLogger(__name__)


class Notifier:
    """Sends notifications via WhatsApp or SMS using Twilio."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        use_whatsapp: bool = True
    ):
        """
        Initialize Notifier.

        Args:
            account_sid: Twilio Account SID. If None, uses config value.
            auth_token: Twilio Auth Token. If None, uses config value.
            from_number: Sender phone number. If None, uses config value.
            to_number: Recipient phone number. If None, uses config value.
            use_whatsapp: If True, send via WhatsApp; otherwise SMS.
        """
        self.account_sid = account_sid or config.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or config.TWILIO_AUTH_TOKEN
        self.from_number = from_number or config.TWILIO_PHONE_NUMBER
        self.to_number = to_number or config.MY_PHONE_NUMBER
        self.use_whatsapp = use_whatsapp

        self._client: Optional[Client] = None

    @property
    def client(self) -> Optional[Client]:
        """Get or create Twilio client."""
        if self._client is None and self.account_sid and self.auth_token:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client

    def send_message(self, message_body: str) -> bool:
        """
        Send an alert message via WhatsApp or SMS.

        Args:
            message_body: Content of the message

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not configured, skipping message send")
            return False

        try:
            # Prepare phone numbers based on message type
            if self.use_whatsapp:
                from_number = f"whatsapp:{self.from_number}"
                to_number = f"whatsapp:{self.to_number}"
                msg_type = "WhatsApp"
            else:
                from_number = self.from_number
                to_number = self.to_number
                msg_type = "SMS"

            logger.debug(f"Sending {msg_type} message to {to_number}")

            message = self.client.messages.create(
                body=message_body,
                from_=from_number,
                to=to_number
            )

            logger.info(f"{msg_type} message sent successfully (SID: {message.sid})")
            return True

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)
            return False
