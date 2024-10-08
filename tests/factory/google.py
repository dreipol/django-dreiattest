import base64
import datetime
import pkgutil
from hashlib import sha256

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization.base import load_pem_private_key
from cryptography.x509.base import load_pem_x509_certificate
from cryptography.x509.oid import NameOID

from pyattest.testutils.factories.certificates import key_usage

from dreiattest.models import DeviceSession, Nonce


def get(
    apk_package_name: str,
    nonce: Nonce,
    device_session: DeviceSession,
    basic_integrity: bool = True,
    cts_profile: bool = True,
    apk_cert_digest: bytes = None,
):
    """Helper to create a fake google attestation."""

    root_key = load_pem_private_key(
        pkgutil.get_data("pyattest", "testutils/fixtures/root_key.pem"), b"123"
    )
    root_cert = load_pem_x509_certificate(
        pkgutil.get_data("pyattest", "testutils/fixtures/root_cert.pem")
    )

    apk_cert_digest = apk_cert_digest or b"foobar"
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER, format=serialization.PublicFormat.PKCS1
    )

    subject = x509.Name(
        [x509.NameAttribute(NameOID.ORGANIZATION_NAME, "pyattest-testing-leaf")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(root_cert.subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=10))
        .add_extension(key_usage, critical=False)
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("pyattest-testing-leaf.ch")]),
            critical=False,
        )
        .sign(root_key, hashes.SHA256())
    )

    nonce = str(device_session) + base64.b64encode(public_key).decode() + nonce.value
    nonce = sha256(nonce.encode()).digest()

    data = {
        "timestampMs": 9860437986543,
        "nonce": base64.b64encode(nonce).decode(),
        "apkPackageName": apk_package_name,
        "apkCertificateDigestSha256": [base64.b64encode(apk_cert_digest).decode()],
        "ctsProfileMatch": cts_profile,
        "basicIntegrity": basic_integrity,
        "evaluationType": "BASIC",
    }

    headers = {
        "x5c": [
            cert.public_bytes(serialization.Encoding.PEM)
            .decode()
            .replace("-----BEGIN CERTIFICATE-----\n", "")
            .replace("\n-----END CERTIFICATE-----\n", ""),
            root_cert.public_bytes(serialization.Encoding.PEM)
            .decode()
            .replace("-----BEGIN CERTIFICATE-----\n", "")
            .replace("\n-----END CERTIFICATE-----\n", ""),
        ]
    }

    return jwt.encode(data, private_key, algorithm="RS256", headers=headers), public_key
