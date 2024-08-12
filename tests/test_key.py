import base64
import uuid
from hashlib import sha256
from unittest.mock import patch
import pkgutil

from cryptography.hazmat.primitives import serialization
from cryptography.x509.base import load_pem_x509_certificate
from pyattest.configs.apple import AppleConfig
from pyattest.configs.google import GoogleConfig

from dreiattest.exceptions import InvalidDriverException
from dreiattest.key import key_from_request, get_key_id
from dreiattest.models import DeviceSession
from django.test import RequestFactory
from django.test import TestCase

from dreiattest.nonce import create_nonce
from tests.factory import apple as apple_factory
from tests.factory import google as google_factory


class PublicKey(TestCase):
    def setUp(self):
        self.root_cn = "pyattest-testing-leaf.ch"
        self.root_ca = load_pem_x509_certificate(
            pkgutil.get_data("pyattest", "testutils/fixtures/root_cert.pem")
        )
        self.root_ca_pem = self.root_ca.public_bytes(serialization.Encoding.PEM)
        self.rf = RequestFactory()

    @patch("dreiattest.key.AppleConfig")
    def test_can_create_key_with_apple_driver(self, mock_config):
        """Mock the apple config so we can inject our custom root_ca which is also used in the apple_factory."""
        device_session = DeviceSession(session_id=uuid.uuid4(), user_id="test")
        device_session.save()
        nonce = create_nonce(device_session)

        attest, public_key = apple_factory.get(
            app_id="foo", nonce=nonce, device_session=device_session
        )
        key_id = sha256(public_key).digest()
        mock_config.return_value = AppleConfig(
            key_id=key_id, app_id="foo", production=False, root_ca=self.root_ca_pem
        )

        data = {
            "driver": "apple",
            "key_id": base64.b64encode(key_id).decode("utf-8"),
            "attestation": base64.b64encode(attest).decode("utf-8"),
        }
        request = self.rf.post("/foo", data, content_type="application/json")

        key = key_from_request(request, nonce, device_session)
        nonce.refresh_from_db()
        self.assertEqual(key.public_key_id, base64.b64encode(key_id).decode())
        self.assertEqual(key.driver, "apple")
        self.assertTrue(bool(nonce.used_at))

    @patch("dreiattest.key.GoogleConfig")
    def test_can_create_key_with_google_driver(self, mock_config):
        """Mock the google config so we can inject our custom root_ca which is also used in the apple_factory."""
        device_session = DeviceSession(session_id=uuid.uuid4(), user_id="test")
        device_session.save()
        nonce = create_nonce(device_session)
        apk_cert_digest = bytes.fromhex("90f283bdab972dab7524b9208de4ef8f")

        attest, public_key = google_factory.get(
            apk_package_name="foo",
            nonce=nonce,
            device_session=device_session,
            apk_cert_digest=apk_cert_digest,
        )
        mock_config.return_value = GoogleConfig(
            key_ids=[base64.b64encode(apk_cert_digest)],
            apk_package_name="foo",
            root_cn=self.root_cn,
            root_ca=self.root_ca_pem,
            production=False,
        )

        data = {
            "driver": "google",
            "public_key": base64.b64encode(public_key).decode(),
            "attestation": attest,
        }
        request = self.rf.post("/foo", data, content_type="application/json")

        public_key = serialization.load_der_public_key(public_key)
        public_key = public_key.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        key_id = get_key_id(public_key.decode())
        key = key_from_request(request, nonce, device_session)
        nonce.refresh_from_db()

        self.assertEqual(key.driver, "google")
        self.assertEqual(key.public_key_id, key_id)
        self.assertTrue(bool(nonce.used_at))

    def test_invalid_driver(self):
        device_session = DeviceSession(session_id=uuid.uuid4(), user_id="test")
        device_session.save()
        nonce = create_nonce(device_session)
        data = {"driver": "invalid"}
        request = self.rf.post("/foo", data, content_type="application/json")

        with self.assertRaises(InvalidDriverException):
            key = key_from_request(request, nonce, device_session)
