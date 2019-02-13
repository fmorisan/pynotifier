from peewee import (
    Model,
    CharField,
)

from .db import db


class Tag(Model):
    tag = CharField()

    class Meta:
        database = db
