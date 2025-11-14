"""Tests for src.notifier module."""

import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.notifier import Notifier


class TestNotifier:
    """Tests for Notifier class."""

    @pytest.fixture
    def notifier(self):
        """Create a Notifier instance for testing."""
        return Notifier(
            account_sid='test_sid',
            auth_token='test_token',
            from_number='+1234567890',
            to_number='+0987654321',
            use_whatsapp=True
        )

    def test_init_with_parameters(self):
        """Test initialization with provided parameters."""
        notifier = Notifier(
            account_sid='sid',
            auth_token='token',
            from_number='+111',
            to_number='+222',
            use_whatsapp=False
        )
        assert notifier.account_sid == 'sid'
        assert notifier.auth_token == 'token'
        assert notifier.from_number == '+111'
        assert notifier.to_number == '+222'
        assert notifier.use_whatsapp is False

    @patch('src.notifier.config')
    def test_init_without_parameters(self, mock_config):
        """Test initialization without parameters uses config."""
        mock_config.TWILIO_ACCOUNT_SID = 'config_sid'
        mock_config.TWILIO_AUTH_TOKEN = 'config_token'
        mock_config.TWILIO_PHONE_NUMBER = '+config_from'
        mock_config.MY_PHONE_NUMBER = '+config_to'

        notifier = Notifier()

        assert notifier.account_sid == 'config_sid'
        assert notifier.auth_token == 'config_token'
        assert notifier.from_number == '+config_from'
        assert notifier.to_number == '+config_to'

    @patch('src.notifier.Client')
    def test_client_property_lazy_initialization(self, mock_client_class, notifier):
        """Test that client is lazily initialized."""
        assert notifier._client is None

        # Access client property
        client = notifier.client

        assert client is not None
        mock_client_class.assert_called_once_with('test_sid', 'test_token')

    @patch('src.notifier.config')
    @patch('src.notifier.Client')
    def test_client_property_returns_none_without_credentials(self, mock_client_class, mock_config):
        """Test that client returns None without credentials."""
        mock_config.TWILIO_ACCOUNT_SID = None
        mock_config.TWILIO_AUTH_TOKEN = None
        mock_config.TWILIO_PHONE_NUMBER = None
        mock_config.MY_PHONE_NUMBER = None

        notifier = Notifier(account_sid=None, auth_token=None)

        assert notifier.client is None
        mock_client_class.assert_not_called()

    @patch('src.notifier.Client')
    def test_send_message_whatsapp_success(self, mock_client_class, notifier):
        """Test successful WhatsApp message sending."""
        mock_message = Mock()
        mock_message.sid = 'SM123456'
        mock_client_class.return_value.messages.create.return_value = mock_message

        result = notifier.send_message("Test message")

        assert result is True
        mock_client_class.return_value.messages.create.assert_called_once_with(
            body="Test message",
            from_="whatsapp:+1234567890",
            to="whatsapp:+0987654321"
        )

    @patch('src.notifier.Client')
    def test_send_message_sms_success(self, mock_client_class):
        """Test successful SMS message sending."""
        notifier = Notifier(
            account_sid='test_sid',
            auth_token='test_token',
            from_number='+1234567890',
            to_number='+0987654321',
            use_whatsapp=False
        )
        mock_message = Mock()
        mock_message.sid = 'SM123456'
        mock_client_class.return_value.messages.create.return_value = mock_message

        result = notifier.send_message("Test SMS")

        assert result is True
        mock_client_class.return_value.messages.create.assert_called_once_with(
            body="Test SMS",
            from_="+1234567890",
            to="+0987654321"
        )

    @patch('src.notifier.config')
    def test_send_message_no_credentials(self, mock_config):
        """Test sending message without credentials."""
        mock_config.TWILIO_ACCOUNT_SID = None
        mock_config.TWILIO_AUTH_TOKEN = None
        mock_config.TWILIO_PHONE_NUMBER = None
        mock_config.MY_PHONE_NUMBER = None

        notifier = Notifier(account_sid=None, auth_token=None)

        result = notifier.send_message("Test message")

        assert result is False

    @patch('src.notifier.Client')
    def test_send_message_twilio_exception(self, mock_client_class, notifier):
        """Test handling of Twilio exceptions."""
        mock_client_class.return_value.messages.create.side_effect = Exception("Twilio error")

        result = notifier.send_message("Test message")

        assert result is False

    @patch('src.notifier.Client')
    def test_send_message_empty_body(self, mock_client_class, notifier):
        """Test sending message with empty body."""
        mock_message = Mock()
        mock_message.sid = 'SM123456'
        mock_client_class.return_value.messages.create.return_value = mock_message

        result = notifier.send_message("")

        assert result is True
        mock_client_class.return_value.messages.create.assert_called_once()

    @patch('src.notifier.Client')
    def test_send_message_long_body(self, mock_client_class, notifier):
        """Test sending message with long body."""
        long_message = "A" * 2000
        mock_message = Mock()
        mock_message.sid = 'SM123456'
        mock_client_class.return_value.messages.create.return_value = mock_message

        result = notifier.send_message(long_message)

        assert result is True
        call_kwargs = mock_client_class.return_value.messages.create.call_args[1]
        assert call_kwargs['body'] == long_message
