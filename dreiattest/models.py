from datetime import datetime

from django.db.models import Model, CharField, UUIDField, DateTimeField, ForeignKey, PROTECT, TextField


class User(Model):
    identifier = CharField(max_length=255, null=True)
    uuid = UUIDField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.identifier};{self.uuid}'


class Nonce(Model):
    value = CharField(max_length=255)
    user = ForeignKey(User, on_delete=PROTECT)
    used_at = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def mark_used(self):
        self.used_at = datetime.now()
        self.save()


class Key(Model):
    user = ForeignKey(User, on_delete=PROTECT)
    public_key_id = CharField(max_length=255)
    public_key = TextField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
