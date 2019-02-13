from grab.el_dia_grabber import(
    ElDiaGrabber,
    THREE_DORMS,
    TWO_DORMS,
    ONE_DORM,
)

from models.db import db
from models import (
    TGUser,
    Message,
    Tag,
    TGUserToMessage,
    TGUserToTag,
    MessageToTags,
)

db.connect()
db.create_tables([
    TGUser,
    Message,
    Tag,
    TGUserToMessage,
    TGUserToTag,
    MessageToTags,
])

for tag in [ONE_DORM, TWO_DORMS, THREE_DORMS]:
    Tag.get_or_create(tag=tag)


grabber = ElDiaGrabber(ONE_DORM)
grabber.grab()
grabber = ElDiaGrabber(TWO_DORMS)
grabber.grab()
grabber = ElDiaGrabber(THREE_DORMS)
grabber.grab()
