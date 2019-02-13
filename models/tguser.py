from peewee import (
    Model,
    CharField,
    ForeignKeyField,
    IntegerField,
    CompositeKey
)

from .message import Message
from .tag import Tag
from .db import db


class TGUserSettings:
    CLASSIFIED_DAYS = [1, 5, 10, 15]


class TGUser(Model):
    handle = CharField(unique=True)
    classified_expiry_days = IntegerField(choices=TGUserSettings.CLASSIFIED_DAYS, default=15)

    @property
    def tags(self):
        return Tag.select().join(TGUserToTag).where(TGUserToTag.user == self)

    @property
    def received_messages(self):
        return Message.select().join(TGUserToMessage).where(TGUserToMessage.user == self)

    class Meta:
        database = db


class TGUserToTag(Model):
    user = ForeignKeyField(TGUser)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = db
        primary_key = CompositeKey('user', 'tag')


class TGUserToMessage(Model):
    user = ForeignKeyField(TGUser)
    message = ForeignKeyField(Message)

    class Meta:
        database = db
        primary_key = CompositeKey('user', 'message')
