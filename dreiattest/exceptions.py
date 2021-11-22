class DreiAttestException(Exception):
    pass


class InvalidDriverException(DreiAttestException):
    pass


class InvalidHeaderException(DreiAttestException):
    pass


class InvalidPayloadException(DreiAttestException):
    pass


class NoKeyForSessionException(DreiAttestException):
    pass


class UnsupportedEncryptionException(DreiAttestException):
    pass
