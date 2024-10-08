import base64
import datetime
import os
import pkgutil
import struct
from hashlib import sha256
from pathlib import Path

from _cbor2 import dumps as cbor_encode
from asn1crypto.core import OctetString
from cryptography import x509
from cryptography.hazmat._oid import ObjectIdentifier
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.serialization.base import load_pem_private_key
from cryptography.x509.base import load_pem_x509_certificate
from cryptography.x509.extensions import UnrecognizedExtension
from cryptography.x509.oid import NameOID

from pyattest.testutils.factories.certificates import key_usage

from dreiattest.models import Nonce, DeviceSession


def get(
    app_id: str,
    nonce: Nonce,
    device_session: DeviceSession,
    aaguid: bytes = b"appattestdevelop",
    counter: int = 0,
    wrong_public_key: bool = False,
):
    """Helper to create a fake apple attestation."""
    root_key = load_pem_private_key(
        pkgutil.get_data("pyattest", "testutils/fixtures/root_key.pem"), b"123"
    )
    root_cert = load_pem_x509_certificate(
        pkgutil.get_data("pyattest", "testutils/fixtures/root_cert.pem")
    )

    private_key = ec.generate_private_key(ec.SECP384R1())

    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    auth_data_public_key = public_key if not wrong_public_key else "XXXXX".encode()

    auth_data = (
        sha256(app_id.encode()).digest()
        + b"\x00"  # Flag, we'll fill it with zero
        + struct.pack("!I", counter)
        + aaguid  # TODO: Fillup to ensure 16 bytes
        + struct.pack("!H", 32)  # Our SHA-256 digest is always 32bytes
        + sha256(auth_data_public_key).digest()
    )

    public_key_base64 = base64.b64encode(sha256(public_key).digest())
    attest_nonce = (
        str(device_session) + public_key_base64.decode() + nonce.value
    ).encode()
    nonce = sha256(auth_data + sha256(attest_nonce).digest())

    # When comparing this nonce with the one calculated on the server, we'll strip 6 bytes which are normally
    # used to indicated an ASN1 envelope sequence. See the verify_nonce method in the apple verifier.
    der_nonce = bytes(6) + OctetString(nonce.digest()).native

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
            UnrecognizedExtension(
                ObjectIdentifier("1.2.840.113635.100.8.2"), der_nonce
            ),
            critical=False,
        )
        .sign(root_key, hashes.SHA256())
    )

    data = {
        "fmt": "apple-appattest",
        "attStmt": {
            "x5c": [
                cert.public_bytes(serialization.Encoding.DER),
                root_cert.public_bytes(serialization.Encoding.DER),
            ],
            "receipt": b"",
        },
        "authData": auth_data,
    }

    return cbor_encode(data), public_key
