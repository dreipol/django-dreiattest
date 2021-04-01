# django-dreiattest

dreiattest leverages the [pyttest](https://github.com/dreipol/pyattest) and integrating it to django. It handles
routing, different config options and persistence of tokens and public keys

## Installation

pyattest is available on PyPI and can be installed via `$ python -m pip install dreiattest-django`.

After the installation make sure to add `dreiattest` to your `INSTALLED_APPS` and trigger all migrations
with `python manage.py migrate dreiattest`

## Usage

In your settings.py, make sure to set the correct Apple AppId as well as the environment you want to test in.

```
DREIATTEST_APPLE_APPID = '5LVDC4HW22.ch.dreipol.dreiattestTestHost'
DREIATTEST_PRODUCTION = False
```

There are more advanced settings you can find in dreiattest/settings.py

All that's left is to add the `signature_required` view decorator

```python
from dreiattest.decorators import signature_required


@signature_required()
def demo(request: WSGIRequest):
    return JsonResponse({'foo': 'bar'})

```
