from datetime import datetime
from django.db.models import (
    Model,
    CharField,
    UUIDField,
    DateTimeField,
    ForeignKey,
    PROTECT,
    TextField,
    Index,
)
from cryptography.hazmat.primitives.serialization.base import load_pem_public_key


class DeviceSession(Model):
    user_id = CharField(max_length=255, null=True)
    session_id = UUIDField(unique=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [Index(fields=["user_id", "session_id"])]

    def __str__(self):
        session_id = str(self.session_id).upper()
        return f"{self.user_id};{session_id.lower()}"


class Nonce(Model):
    value = CharField(max_length=255)
    device_session = ForeignKey(DeviceSession, on_delete=PROTECT)
    used_at = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def mark_used(self):
        self.used_at = datetime.now()
        self.save()


class Key(Model):
    device_session = ForeignKey(DeviceSession, on_delete=PROTECT)
    public_key_id = CharField(max_length=255)
    public_key = TextField()
    driver = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def load_pem(self):
        return load_pem_public_key(self.public_key.encode())
