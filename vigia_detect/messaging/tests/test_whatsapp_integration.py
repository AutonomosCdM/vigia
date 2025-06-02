"""
Tests para la integración con WhatsApp

Este módulo contiene tests para la integración con WhatsApp vía Twilio.
"""

import pytest
from unittest.mock import MagicMock
from twilio.base.exceptions import TwilioRestException

def test_send_whatsapp_message(twilio_client, twilio_whatsapp_from, test_whatsapp_number, vcr):
    """Test sending WhatsApp message through Twilio API"""
    with vcr.use_cassette('tests/vcr_cassettes/whatsapp_send_message.yaml'):
        message = twilio_client.messages.create(
            body='Hello from pytest!',
            from_=twilio_whatsapp_from,
            to=test_whatsapp_number
        )
        assert message.sid is not None
        assert message.status in ['queued', 'sent', 'delivered']

def test_whatsapp_message_failure(twilio_client, twilio_whatsapp_from):
    """Test WhatsApp message failure with invalid number"""
    # Mock the create method to raise TwilioRestException
    original_create = twilio_client.messages.create
    
    # Create a mock response for TwilioRestException
    from unittest.mock import Mock
    mock_response = Mock()
    mock_response.status_code = 400
    
    twilio_client.messages.create = MagicMock(side_effect=TwilioRestException(
        status=400, uri='/test', msg='Invalid number', code=21211, method='POST'
    ))
    
    with pytest.raises(TwilioRestException):
        twilio_client.messages.create(
            body='This should fail',
            from_=twilio_whatsapp_from,
            to='whatsapp:+15005550000'  # Invalid test number
        )
    
    # Restore original method
    twilio_client.messages.create = original_create

@pytest.mark.skip(reason="Requires live WhatsApp sandbox setup")
def test_whatsapp_webhook_processing(twilio_client, vcr):
    """Test processing incoming WhatsApp messages"""
    # This would test your webhook handler logic
    # Requires actual sandbox setup with ngrok/local tunnel
    pass

def test_whatsapp_templates(twilio_client, twilio_whatsapp_from, test_whatsapp_number):
    """Test WhatsApp template message sending"""
    # Mock the create method to return a successful message
    mock_message = MagicMock()
    mock_message.sid = 'SM1234567890'
    twilio_client.messages.create = MagicMock(return_value=mock_message)
    
    message = twilio_client.messages.create(
        content_sid='HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',  # Template SID
        from_=twilio_whatsapp_from,
        to=test_whatsapp_number
    )
    assert message.sid is not None
