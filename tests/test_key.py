# import os
# from hashlib import sha256
# from pathlib import Path
#
# from cryptography.hazmat.primitives import serialization
# from cryptography.x509.base import load_pem_x509_certificate
# from pytest import raises
#
# import tests.factories.attestation.apple
# from pyattest.attestation import Attestation
# from pyattest.configs.apple import AppleConfig
# from pyattest.exceptions import InvalidAaguidException, InvalidNonceException, InvalidKeyIdException, \
#     InvalidAppIdException, InvalidCounterException, InvalidCredentialIdException
# from tests.factories import attestation as attest_factory
#
# root_ca = load_pem_x509_certificate(Path('tests/fixtures/root_cert.pem').read_bytes())
# root_ca_pem = root_ca.public_bytes(serialization.Encoding.PEM)
# nonce = os.urandom(32)
#
#
# def test_happy_path():
#     """ Test the basic attest verification where everything works like it should :) """
#     attest, public_key = tests.factories.attestation.apple.get(app_id='foo', nonce=nonce)
#     key_id = sha256(public_key).digest()
#     config = AppleConfig(key_id=key_id, app_id='foo', root_ca=root_ca_pem)
#
#     attestation = Attestation(attest, nonce, config)
#     attestation.verify()
