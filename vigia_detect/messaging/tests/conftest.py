import os
import pytest
from twilio.rest import Client
import vcr

@pytest.fixture(scope='module')
def vcr_config():
    return {
        'filter_headers': ['authorization'],
        'filter_post_data_parameters': ['From', 'To'],
        'record_mode': 'once'
    }

@pytest.fixture(scope='module')
def twilio_client():
    account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'ACtesttesttesttesttest')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'testtesttesttesttest')
    return Client(account_sid, auth_token)

@pytest.fixture(scope='module')
def twilio_number():
    return os.getenv('TWILIO_NUMBER', '+15005550006')

@pytest.fixture(scope='module')
def twilio_whatsapp_from():
    return os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

@pytest.fixture(scope='module')
def test_number():
    return os.getenv('TEST_NUMBER', '+15005550007')

@pytest.fixture(scope='module')
def test_whatsapp_number():
    return os.getenv('TEST_WHATSAPP_NUMBER', 'whatsapp:+15551234567')

@pytest.fixture(scope='module')
def vcr(vcr):
    vcr.match_on = ['method', 'scheme', 'host', 'port', 'path', 'query']
    return vcr
