from bot.decorator import CollectionCommand
from db.db_handler import DataUsers
from logger.logger import logger_all

from telegram import Update
from telegram.ext import CallbackContext


database = DataUsers()


class TelebotHandler():
    """ Базовый класс со словарем команд """
    COMMANDS = {}


@logger_all()
@CollectionCommand('start', TelebotHandler.COMMANDS)
class Welcome(TelebotHandler):
    """ Начало работы """
    def __call__(self, update: Update, context: CallbackContext):
        send_msg = 'Привет {}! Здесь ты найдешь лучшие предложения по поиску отелей ' \
                   'Для начала посмотри, что я умею /help'.format(update.message.from_user.first_name)

        database.create(user_id=update.message.from_user.id, user_name=update.message.from_user.first_name)
        update.message.reply_text(send_msg)


@logger_all()
@CollectionCommand('history', TelebotHandler.COMMANDS)
class History(TelebotHandler):
    """ Показать историю (последние 5 действия) """
    def __call__(self, update: Update, context: CallbackContext) -> None:
        data = database.read(update.message.from_user.id)
        update.message.reply_text(data)


@logger_all()
@CollectionCommand('help', TelebotHandler.COMMANDS)
class Help(TelebotHandler):
    """ Показать возможности """
    def __call__(self, update: Update, context: CallbackContext):
        send_msg = ['/{}: {}'.format(text_command, obj_command.__doc__)
                    for text_command, obj_command in TelebotHandler.COMMANDS.items()
                    ]
        send_msg = '\n'.join(send_msg)
        return update.message.reply_text(send_msg)
