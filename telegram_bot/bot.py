import logging

from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
)

from peewee import fn as sqlfn

from models import (
    Tag,
    TGUser,
    TGUserToTag,
    TGUserToMessage,
    Message,
    MessageToTags,
)

from models.tguser import (
    TGUserSettings
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

TAGBUTTON = 'tagbutton'
REMOVETAG = 'rmtag'
CANCEL_ACTION = 'cancelaction'
USERSETTINGS = 'usersettings'


def require_user_registered(f):
    def wrapped(bot, update):
        if not TGUser.select().where(TGUser.handle == update.message.from_user.username):
            update.message.reply_text("You must /start")
            return
        f(bot, update)
    return wrapped


def require_superuser(f):
    def wrapped(bot, update):
        if not update.message.from_user.username.lower() == 'zzmori':
            update.message.reply_text("You can't do this!")
            return
        f(bot, update)
    return wrapped


def start(bot, update):
    update.message.reply_text("Subscribed to classifieds! Use /select_tags to select some tags")
    TGUser.create(handle=update.message.from_user.username)


@require_user_registered
def stop(bot, update):
    update.message.reply_text("Deleted your subscription.")
    user = TGUser.get(handle=update.message.from_user.username)
    TGUserToTag.delete().where(TGUserToTag.user == user).execute()
    user.delete_instance()


@require_user_registered
def select_tags(bot, update):
    user = TGUser.get(handle=update.message.from_user.username)
    buttons = [
        [InlineKeyboardButton(tag.tag, callback_data=f'{TAGBUTTON}:{user.handle}:{tag.id}')]
        for tag in Tag.select()
    ]
    buttons.append([
        InlineKeyboardButton("Cancel", callback_data=CANCEL_ACTION)
    ])
    keyboard = InlineKeyboardMarkup(buttons, one_time_keyboard=True)
    update.message.reply_text("Choose a tag to subscribe to:", reply_markup=keyboard)


@require_user_registered
def remove_tag(bot, update):
    user = TGUser.get(handle=update.message.from_user.username)
    buttons = [
        [InlineKeyboardButton(tag.tag, callback_data=f'{REMOVETAG}:{user.handle}:{tag.id}')]
        for tag in Tag.select().join(TGUserToTag).where(TGUserToTag.user == user)
    ]
    buttons.append([
        InlineKeyboardButton("Cancel", callback_data=CANCEL_ACTION)
    ])
    keyboard = InlineKeyboardMarkup(buttons, one_time_keyboard=True)
    update.message.reply_text("Choose a tag to remove:", reply_markup=keyboard)


@require_user_registered
def select_expiry(bot, update):
    user = TGUser.get(handle=update.message.from_user.username)
    buttons = [
        [InlineKeyboardButton(day_amount, callback_data=f'{USERSETTINGS}:{user.handle}:{day_amount}')]
        for day_amount in TGUserSettings.CLASSIFIED_DAYS
    ]
    buttons.append([
        InlineKeyboardButton("Cancel", callback_data=CANCEL_ACTION)
    ])
    keyboard = InlineKeyboardMarkup(buttons, one_time_keyboard=True)
    update.message.reply_text("Choose how old classifieds sent to you can be:", reply_markup=keyboard)


@require_user_registered
def list_tags(bot, update):
    user = TGUser.get(handle=update.message.from_user.username)
    tags = Tag.select().join(TGUserToTag).where(TGUserToTag.user == user)
    update.message.reply_text(f"Your tags: {[t.tag for t in tags]}")


@require_user_registered
def get_classifieds(bot, update):
    user = TGUser.get(handle=update.message.from_user.username)
    tags = Tag.select().join(TGUserToTag).where(TGUserToTag.user == user)
    messages = Message.select().join(MessageToTags).where(MessageToTags.tag << tags)
    for message in messages:
        mtts = message.messagetotags_set
        message_tags = [mtt.tag for mtt in mtts]
        # query = MessageToTags.select(MessageToTags, Tag).join(Message).where(Message.uuid == message)
        # if query:
        # TODAS las tags del usuario estan contenidas en el set de tags del mensaje
        if all(tag in message_tags for tag in tags):
            update.message.reply_text(message.content)



def button_pressed(bot, update):
    query = update.callback_query.data.split(':')
    message = {
        TAGBUTTON: tag_button_callback,
        CANCEL_ACTION: lambda x, y, z: "Action canceled.",
        USERSETTINGS: user_settings_callback,
        REMOVETAG: remove_tag_callback,
    }[query[0]](bot, update, query[1:])
    if message:
        bot.edit_message_text(
            message,
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )


def remove_tag_callback(bot, update, data):
    # data = [user handle, id, ]
    tag_id = int(data[1])
    user = TGUser.get(
        handle=data[0]
    )
    tag = Tag.get(id=tag_id)
    TGUserToTag.get(
        user=user,
        tag=tag
    ).delete_instance()
    return f"Removed {tag.tag}"


def tag_button_callback(bot, update, data):
    # data = [user handle, id, ]
    tag_id = int(data[1])
    user = TGUser.get(
        handle=data[0]
    )
    tag = Tag.get(id=tag_id)
    TGUserToTag.get_or_create(
        user=user,
        tag=tag
    )
    return f"Selected {tag.tag}"


def user_settings_callback(bot, update, data):
    # data = [user handle, id, ]
    day_amount = int(data[1])
    user = TGUser.get(
        handle=data[0]
    )
    user.classified_expiry_days = day_amount
    user.save()
    return "Preferences saved."


@require_user_registered
@require_superuser
def add_tag(bot, update):
    user = TGUser.get(
        handle=update.message.from_user.username
    )
    update.message.reply_text("Updating tags of all messages, this may take a minute or two....")
    import ipdb; ipdb.set_trace()
    tag = Tag.create(tag=update.message.text.split()[1])
    for message in Message.select().where(sqlfn.LOWER(Message.content).contains(tag.tag.lower())):
        MessageToTags.create(
            message=message,
            tag=tag
        )
    TGUserToTag.create(
        user=user,
        tag=tag,
    )
    update.message.reply_text("Done!")


def main():
    updater = Updater("624089546:AAFWKz03M8DdZykJRhXtSDzsTJnaCIKHbFo")

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("stop", stop))
    updater.dispatcher.add_handler(CommandHandler("select_tags", select_tags))
    updater.dispatcher.add_handler(CommandHandler("tags", list_tags))
    updater.dispatcher.add_handler(CommandHandler("rmtags", remove_tag))
    updater.dispatcher.add_handler(CommandHandler("addtag", add_tag))
    updater.dispatcher.add_handler(CommandHandler("settings", select_expiry))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, get_classifieds))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_pressed))

    updater.start_polling()
    updater.idle()


main()
