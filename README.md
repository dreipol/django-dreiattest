# django-dreiattest

dreiattest leverages [pyttest](https://github.com/dreipol/pyattest) and integrates it into django. It handles routing, different config options and persistence of tokens and public keys. To use dreiAttest you need to use the corresponing libraries for [iOS](https://github.com/dreipol/dreiAttest-ios) and [Android / Kotlin Multiplatform](https://github.com/dreipol/dreiAttest-android).

## Installation

dreiAttest is available on PyPI and can be installed via `$ python -m pip install dreiattest-django`.

After the installation make sure to add `dreiattest` to your `INSTALLED_APPS` and trigger all migrations
with `python manage.py migrate dreiattest`. Also, you need to register the default endpoints in your urls.py

```
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dreiattest.urls')),
    ...
]
```

## Config

There are multiple settings you can and or have to set in your settings.py. The following are mandatory:

- **Apple**: `DREIATTEST_APPLE_APPID` 
- **Google**: `DREIATTEST_GOOGLE_APK_NAME`, `DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST`

These are all the possible config values and what they do.

- DREIATTEST_BASE_URL: Our different endpoints like /key and /nonce will be bellow this slug
- DREIATTEST_UID_HEADER: Header containing the DeviceSession uid
- DREIATTEST_ASSERTION_HEADER: Header containing the assertion
- DREIATTEST_USER_HEADERS_HEADER: Header containing the list of comma separated headers that are included in the assertion
- DREIATTEST_NONCE_HEADER: Header containing the server nonce that was used inside the attestation
- DREIATTEST_BYPASS_HEADER: Header containing the shared secret to bypass the verification process. Helpfull for debugging
- DREIATTEST_APPLE_APPID: Header containing the apple app id
- DREIATTEST_GOOGLE_APK_NAME: Header containing the google apk name
- DREIATTEST_PRODUCTION: Indicating if we're in a production environment or not. Some extra verifications are made if this is true. Those are described in the [pyttest](https://github.com/dreipol/pyattest) readme.
- DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST: SHA256 hex of the Google APK Certificate
- DREIATTEST_PLUGINS: List of classes implementing `BasePlugin` - gives you the option to handle extra verification
- DREIATTEST_BYPASS_SECRET: **DANGERZONE** If this is set and DREIATTEST_BYPASS_HEADER is sent by the client, the veirification is skipped.

You can find the default value (if any) for each of them in the [settings.py](https://github.com/dreipol/django-dreiattest/blob/master/dreiattest/settings.py)

## Usage

All that's left is to add the `signature_required` view decorator.

```python
from dreiattest.decorators import signature_required

@signature_required()
def demo(request: WSGIRequest):
    return JsonResponse({'foo': 'bar'})
```

## Error Handling

The main two exceptions that should be handled by you are `PyAttestException` and `DreiAttestException`. dreiattest ships with the `HandleDreiattestExceptionsMiddleware` you could use if you don't want to handle those errors by yourself. The middleware only catches those two exception classes and returns a `JsonResponse` with status code 400. 

```
MIDDLEWARE = [
    ...
    'dreiattest.middlewares.HandleDreiattestExceptionsMiddleware',
]
```

## Typical Flow

1. CLIENT (could be android or google) makes a request to dreiattest/nonce with a device session identifier to obtain a server nonce. The session id as well as the nonce are persisted on the server.
2. CLIENT sends an attestation to dreiattest/key. This request again holds the device session identifier as well as the nonce from step 1. The nonce will be marked as "used" and used to verify the attestation. The public key from the client is then assigned to the device session and also persisted in the database. 
3. CLIENT sends a request to any view decorated with `@signature_required`. The request holds an assertion which will be verified before the actual django view is executed.

## Publishing / Contributing

- Create a branch from `master` for possible pull requests
- To publish a new version to pypi:
  - Update the version in `__version__.py` 
  - Trigger `$ pipenv run upload` - This will automatically create and push the correct tag in git and upload that version to pypi
