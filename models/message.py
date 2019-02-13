from uuid import uuid4
from hashlib import sha256

from peewee import (
    CharField,
    IntegerField,
    UUIDField,
    DateTimeField,
    ForeignKeyField,
    CompositeKey,
    IntegrityError,
)
from playhouse.signals import (
    Model,
    pre_save
)

from .db import db
from .tag import Tag


class Message(Model):
    uuid = UUIDField(primary_key=True)
    content = CharField()
    content_hash = CharField(unique=True)
    date = DateTimeField()

    def save(self):
        try:
            super(Message, self).save(self)
        except IntegrityError:
            self = Message.get(content_hash=self.content_hash)
        for tag in Tag.select():
            if tag.tag.lower() in self.content.lower():
                try:
                    MessageToTags.create(message=self, tag=tag)
                except Exception:
                    pass

    class Meta:
        database = db


class MessageToTags(Model):
    message = ForeignKeyField(Message)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = db
        primary_key = CompositeKey('tag', 'message')


@pre_save(sender=Message)
def pre_save(sender, instance, created):
    instance.uuid = uuid4()
    _hash = sha256()
    _hash.update(instance.content.encode('utf8'))
    instance.content_hash = _hash.hexdigest()
