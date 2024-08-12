from abc import ABC, abstractmethod

from django.core.handlers.wsgi import WSGIRequest
from pyattest.attestation import Attestation


class BasePlugin(ABC):
    @abstractmethod
    def run(self, request: WSGIRequest, attestation: Attestation): ...
