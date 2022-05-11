from bot.decorator import CollectionCommand
from logger.logger import logger_all
from settings import DATABASE, COUNT_MAX_ACTION_HISTORY

from telegram import Update
from telegram.ext import CallbackContext


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

        DATABASE.create(
            user_id=update.message.from_user.id,
            key_table='users',
            user_name=update.message.from_user.first_name
        )
        update.message.reply_text(send_msg)


@logger_all()
@CollectionCommand('history', TelebotHandler.COMMANDS)
class History(TelebotHandler):
    """ Показать историю (последние 5 действия) """
    def __call__(self, update: Update, context: CallbackContext) -> None:
        data_requests = DATABASE.read_requests(user_id=update.message.from_user.id)

        if len(data_requests) < COUNT_MAX_ACTION_HISTORY:
            data_start = DATABASE.read_user(user_id=update.message.from_user.id)
            update.message.reply_text('Начало: {}'.format(data_start.date_request.strftime('%d.%m.%Y %H:%M')))

        for request in data_requests:
            update.message.reply_text(request, disable_web_page_preview=True, parse_mode='HTML')


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
