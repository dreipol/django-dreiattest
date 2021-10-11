from django.conf import settings

# Our different endpoints like /key and /nonce will be bellow this slug
DREIATTEST_BASE_URL = getattr(settings, 'DREIATTEST_BASE_URL', 'dreiattest/')

# Header containing the DeviceSession uid
DREIATTEST_UID_HEADER = getattr(settings, 'DREIATTEST_UID_HEADER', 'HTTP_DREIATTEST_UID')

# Header containing the assertion
DREIATTEST_ASSERTION_HEADER = getattr(settings, 'DREIATTEST_ASSERTION_HEADER', 'HTTP_DREIATTEST_SIGNATURE')

# Header containing the list of comma separated headers that are included in the assertion
DREIATTEST_USER_HEADERS_HEADER = getattr(settings, 'DREIATTEST_USER_HEADERS_HEADER', 'HTTP_DREIATTEST_USER_HEADERS')

# Header containing the server nonce that was used inside the attestation
DREIATTEST_NONCE_HEADER = getattr(settings, 'DREIATTEST_NONCE_HEADER', 'HTTP_DREIATTEST_NONCE')

# Header containing the shared secret to bypass the verification process. Helpfull for debugging
DREIATTEST_BYPASS_HEADER = getattr(settings, 'DREIATTEST_BYPASS_HEADER', 'HTTP_DREIATTEST_SHARED_SECRET')

# Header containing the apple app id
DREIATTEST_APPLE_APPID = getattr(settings, 'DREIATTEST_APPLE_APPID', None)

# Header containing the google apk name
DREIATTEST_GOOGLE_APK_NAME = getattr(settings, 'DREIATTEST_GOOGLE_APK_NAME', None)

# Indicating if we're in a production environment or not. Some extra verifications are made if this is true.
DREIATTEST_PRODUCTION = getattr(settings, 'DREIATTEST_PRODUCTION', True)

# SHA256 hex of the Google APK Certificate
DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST = getattr(settings, 'DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST', None)

# If this is set and DREIATTEST_BYPASS_HEADER is sent by the client, the veirification is skipped.
DREIATTEST_BYPASS_SECRET = getattr(settings, 'DREIATTEST_BYPASS_SECRET', None)
