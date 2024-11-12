# django-dreiattest

dreiattest leverages [pyattest](https://github.com/dreipol/pyattest) and integrates it into django. It handles routing, different config options and persistence of tokens and public keys. To use dreiAttest you need to use the corresponing libraries for [iOS](https://github.com/dreipol/dreiAttest-ios) and [Android / Kotlin Multiplatform](https://github.com/dreipol/dreiAttest-android).

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

- **Apple**: `DREIATTEST_APPLE_APPIDS` - A list of Apple App IDs that are allowed to connect to your server. You can find the App ID in the Apple Developer Portal under Certificates, Identifiers & Profiles > Identifiers > App IDs. The App ID is the `Identifier` field.
- **Google (Legacy: Safety Net)**: `DREIATTEST_GOOGLE_APK_NAME`, `DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST`
- **Google Play Integrity API**: `DREIATTEST_GOOGLE_APK_NAME`, `DREIATTEST_GOOGLE_DECRYPTION_KEY`, `DREIATTEST_GOOGLE_VERIFICATION_KEY` which can be generated as described [here](https://developer.android.com/google/play/integrity/setup#switch-google-managed)

These are all the possible config values and what they do.

- DREIATTEST_BASE_URL: Our different endpoints like /key and /nonce will be bellow this slug
- DREIATTEST_UID_HEADER: Header containing the DeviceSession uid
- DREIATTEST_ASSERTION_HEADER: Header containing the assertion
- DREIATTEST_USER_HEADERS_HEADER: Header containing the list of comma separated headers that are included in the assertion
- DREIATTEST_NONCE_HEADER: Header containing the server nonce that was used inside the attestation
- DREIATTEST_BYPASS_HEADER: Header containing the shared secret to bypass the verification process. Helpfull for debugging
- DREIATTEST_APPLE_APPID: Header containing the apple app id
- DREIATTEST_GOOGLE_APK_NAME: Header containing the google apk name
- DREIATTEST_GOOGLE_DECRYPTION_KEY: A Base64 encoded AES key secret as described [here](https://developer.android.com/google/play/integrity/verdict#decrypt-verify)
- DREIATTEST_GOOGLE_VERIFICATION_KEY: A Base64 encoded public key as described [here](https://developer.android.com/google/play/integrity/verdict#decrypt-verify)
- DREIATTEST_PRODUCTION: Indicating if we're in a production environment or not. Some extra verifications are made if this is true. Those are described in the [pyttest](https://github.com/dreipol/pyattest) readme.
- DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST: SHA256 hex of the Google APK Certificate
- DREIATTEST_GOOGLE_ALLOW_NON_PLAY_INSTALLS: Allow apps that were not installed via the Play Store to connect to your server. These will be verified via the signing certificate instead. (`DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST` must be set)
- DREIATTEST_GOOGLE_REQUIRED_DEVICE_VERDICT: The minimum device [integrty](https://developer.android.com/google/play/integrity/setup#optional_device_information) verdict that must be present.
- DREIATTEST_PLUGINS: List of classes implementing `BasePlugin` - gives you the option to handle extra verification
- DREIATTEST_BYPASS_SECRET: **DANGERZONE** If this is set and DREIATTEST_BYPASS_HEADER is sent by the client, the verification is skipped.

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

## Common issues

If you are using Play Integrity and your app is distributed via the Play Store you do not need to provide the `DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST` as the signing key is already checked by the Play Store. If you do provide a value for `DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST` both the key and the verdict from the Play Integrity API are checked. Note in that case that the Play Store re-signs your app with a different key before distributing it. You can find the relevant digest in the play console under Setup > App signing.

## Debugging Advice

- Setting `DREIATTEST_PRODUCTION = False`
  - **Android**: Only the package identifier is checked. Note that this does not provide any security guarantees since anyone can build an app with a specific package identifier.
  - **iOS**: Allows dev and production builds to connect to your server. Since iOS requires you to register an App Id to use App Attest this provides some weakened security guarantees. The checks are performed normally but a different environment is used for Apple's attestation api. This should be sufficient to validate your configuration.
  - Additionally it is possible to connect to the server using the `DREIATTEST_BYPASS_SECRET`.
 
- Setting `DREIATTEST_GOOGLE_ALLOW_NON_PLAY_INSTALLS = True`
  - Allows Android apps to connect even if they were not distributed via the Play Store (e.g. dev builds). All the checks are run but instead of letting the Play Store verify your build and signing key the `DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST` is checked. This can be a useful intermediate step to verify your configuration before publishing on the Play Store. Note that once you publish your app on the Play Store you shuld set the value back to `DREIATTEST_GOOGLE_ALLOW_NON_PLAY_INSTALLS = False` and remove or adjust your `DREIATTEST_GOOGLE_APK_CERTIFICATE_DIGEST` (see [Common issues](#common-issues) above).

Before publishing your app on the App Store / Play Store you should validate your setup using a Test Flight / Testing Channel Build. These behave the same as production builds.

## Publishing / Contributing

- Create a branch from `master` for possible pull requests
- To publish a new version to pypi:
  - Update the version in `__version__.py` 
  - Trigger `$ pipenv run upload` - This will automatically create and push the correct tag in git and upload that version to pypi
