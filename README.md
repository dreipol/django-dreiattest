# django-dreiattest

dreiattest leverages [pyttest](https://github.com/dreipol/pyattest) and integrates it into django. It handles
routing, different config options and persistence of tokens and public keys. To use dreiAttest you need to use the corresponing libraries for [iOS](https://github.com/dreipol/dreiAttest-ios) and [Android / Kotlin Multiplatform](https://github.com/dreipol/dreiAttest-android).

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

## Usage

In your settings.py, make sure to set the correct Apple AppId as well as the environment you want to test in.

```

DREIATTEST_APPLE_APPID = '5LVDC4HW22.ch.dreipol.dreiattestTestHost' DREIATTEST_PRODUCTION = False

```

There are more advanced settings you can find in dreiattest/settings.py

All that's left is to add the `signature_required` view decorator

```python
from dreiattest.decorators import signature_required


@signature_required()
def demo(request: WSGIRequest):
    return JsonResponse({'foo': 'bar'})

```
