from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, Filters
from bot.decorator import CollectionCommand
from db.db_handler import DataUsers

database = DataUsers()


class TelebotHandler():
    """ Базовый класс со словарем команд """
    COMMANDS = {}


@CollectionCommand('start', TelebotHandler.COMMANDS)
class Welcome(TelebotHandler):
    """ Класс команды start - печатать приветствия """
    # TODO docstring описание
    def __str__(self) -> str:
        """ Описание команды """
        return 'Начало работы'

    def __call__(self, update: Update, context: CallbackContext):
        send_msg = 'Привет {}! Здесь ты найдешь лучшие предложения по поиску отелей ' \
                   'Для начала посмотри, что я умею /help'.format(update.message.from_user.first_name)

        database.create(user_id=update.message.from_user.id, user_name=update.message.from_user.first_name)
        update.message.reply_text(send_msg)


@CollectionCommand('history', TelebotHandler.COMMANDS)
class History(TelebotHandler):
    """ Класс команды history - печать истории действий (последних 5) """
    # сейчас печатается начало работы с ботом (дата первой команды start)
    def __str__(self) -> str:
        """ Описание команды """
        return 'Показать историю (последние 5 действия)'

    def __call__(self, update: Update, context: CallbackContext) -> None:
        data = database.read(update.message.from_user.id)
        update.message.reply_text(data)


@CollectionCommand('help', TelebotHandler.COMMANDS)
class Help(TelebotHandler):
    """ Класс команды help - печать списка команд и их описание """
    def __str__(self) -> str:
        """ Описание команды """
        return 'Показать возможности'

    def __call__(self, update: Update, context: CallbackContext):
        send_msg = ['/{}: {}'.format(text_command, obj_command())
                    for text_command, obj_command in TelebotHandler.COMMANDS.items()
                    ]
        send_msg = '\n'.join(send_msg)

        return update.message.reply_text(send_msg)


class BaseSearchHotel(TelebotHandler):
    """ Базовый класс для команд поиска отелей """
    CITY, CHECKIN, CHECKOUT, COUNT_PEOPLE, COUNT_HOTEL, COUNT_PHOTO = range(6)
    # TODO продумать как использовать м.б. в сеттинг?

    # TODO доделать и реализовать все запросы в текстовом формате
    #  CITY, CHECKIN, CHECKOUT, COUNT_PEOPLE, COUNT_HOTEL, COUNT_PHOTO

    @staticmethod
    def city(update: Update, context: CallbackContext):
        print('City run')
        city = update.message.text
        print(city)
        send_msg = 'Введите дату начала поездки'
        update.message.reply_text(send_msg)
        return BaseSearchHotel.CHECKIN

    @staticmethod
    def check_in(update: Update, context: CallbackContext):
        print('Check in run')
        check_in = update.message.text
        print(check_in)
        return ConversationHandler.END

    @staticmethod
    def cancel(update: Update, context: CallbackContext):
        return ConversationHandler.END

    def __call__(self, update: Update, context: CallbackContext):
        print(self.__class__.__name__, 'run')
        send_msg = '{} запущен. \nВведите город, в который вы хотите поехать'.format(self.__class__.__name__)
        update.message.reply_text(send_msg)
        return self.CITY


@CollectionCommand('lowprice', TelebotHandler.COMMANDS)
class LowPrice(BaseSearchHotel):
    def __str__(self) -> str:
        """ Описание команды """
        return 'Поиск отелей по минимальной цене'


@CollectionCommand('highprice', TelebotHandler.COMMANDS)
class HighPrice(BaseSearchHotel):
    def __str__(self) -> str:
        """ Описание команды """
        return 'Поиск отелей по максимальной цене'
