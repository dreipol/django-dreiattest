import base64
import uuid
from unittest.mock import patch
import pkgutil

from cryptography.hazmat.primitives import serialization
from cryptography.x509.base import load_pem_x509_certificate
from pyattest.configs.google import GoogleConfig

from dreiattest.key import key_from_request
from dreiattest.models import DeviceSession
from django.test import RequestFactory
from django.test import TestCase

from dreiattest.nonce import create_nonce
from tests.factory import google as google_factory
import dreiattest.settings as dreiattest_settings


class Plugins(TestCase):
    def setUp(self):
        self.root_cn = 'pyattest-testing-leaf.ch'
        self.root_ca = load_pem_x509_certificate(pkgutil.get_data('pyattest', 'testutils/fixtures/root_cert.pem'))
        self.root_ca_pem = self.root_ca.public_bytes(serialization.Encoding.PEM)
        self.rf = RequestFactory()

    @patch('dreiattest.key.GoogleConfig')
    def test_plugins_run(self, mock_config):
        dreiattest_settings.DREIATTEST_PLUGINS = ['dreiattest.plugins.DummyPlugin']
        device_session = DeviceSession(session_id=uuid.uuid4(), user_id='test')
        device_session.save()
        nonce = create_nonce(device_session)
        apk_cert_digest = bytes.fromhex('90f283bdab972dab7524b9208de4ef8f')

        attest, public_key = google_factory.get(apk_package_name='foo', nonce=nonce, device_session=device_session,
                                                apk_cert_digest=apk_cert_digest)
        mock_config.return_value = GoogleConfig(key_ids=[base64.b64encode(apk_cert_digest)], apk_package_name='foo',
                                                root_cn=self.root_cn, root_ca=self.root_ca_pem, production=False)

        data = {
            'driver': 'google',
            'public_key': base64.b64encode(public_key).decode(),
            'attestation': attest,
        }
        request = self.rf.post('/foo', data, content_type='application/json')

        key = key_from_request(request, nonce, device_session)
