from settings import STATES_BASE

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, ConversationHandler, Filters
from bot.decorator import CollectionCommand
from db.db_handler import DataUsers
from rapid.hotel_handler import RapidFacade
from logger.logger import LoggerMixin

database = DataUsers()
hotel_handler = RapidFacade()
RUN = 'Run'


class TelebotHandler(LoggerMixin):
    """ Базовый класс со словарем команд """
    COMMANDS = {}


@CollectionCommand('start', TelebotHandler.COMMANDS)
class Welcome(TelebotHandler):
    """ Начало работы """
    def __call__(self, update: Update, context: CallbackContext):
        send_msg = 'Привет {}! Здесь ты найдешь лучшие предложения по поиску отелей ' \
                   'Для начала посмотри, что я умею /help'.format(update.message.from_user.first_name)

        database.create(user_id=update.message.from_user.id, user_name=update.message.from_user.first_name)
        update.message.reply_text(send_msg)

        self.logger().info(RUN)


@CollectionCommand('history', TelebotHandler.COMMANDS)
class History(TelebotHandler):
    """ Показать историю (последние 5 действия) """
    def __call__(self, update: Update, context: CallbackContext) -> None:
        data = database.read(update.message.from_user.id)
        update.message.reply_text(data)

        self.logger().info(RUN)


@CollectionCommand('help', TelebotHandler.COMMANDS)
class Help(TelebotHandler):
    """ Показать возможности """
    def __call__(self, update: Update, context: CallbackContext):
        send_msg = ['/{}: {}'.format(text_command, obj_command.__doc__)
                    for text_command, obj_command in TelebotHandler.COMMANDS.items()
                    ]
        send_msg = '\n'.join(send_msg)

        self.logger().info(RUN)
        return update.message.reply_text(send_msg)


class BaseSearchHotel(TelebotHandler):
    """ Базовый класс для команд поиска отелей. Реализация разговора с пользователем"""
    request_data = {}

    # TODO продумать проверку на верно введеные данные
    #  + реализовать календарь в check_in и check_out
    #  + перевод в int для числа фото и отелей
    #  + продумать как реализовать ввод взрослых и детей

    def city(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода города пользователя """
        print('City run')
        city = update.message.text
        self.request_data.update({'query': city})
        print(self.request_data)

        send_msg = 'Введите дату начала поездки'
        update.message.reply_text(send_msg)

        self.logger().info(RUN)
        return STATES_BASE['check_in']

    def check_in(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода даты check in """
        print('Check in run')
        check_in = update.message.text
        self.request_data.update({'checkIn': check_in})
        print(self.request_data)

        send_msg = 'Введите дату завершения поездки'
        update.message.reply_text(send_msg)

        self.logger().info(RUN)
        return STATES_BASE['check_out']

    def check_out(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода даты check in """
        print('Check out run')
        check_out = update.message.text
        self.request_data.update({'checkOut': check_out})
        print(self.request_data)

        send_msg = 'Введите кол-во взрослых, проживающих в 1 номере'
        update.message.reply_text(send_msg)

        self.logger().info(RUN)
        return STATES_BASE['count_people']

    def people(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода числа взрослых """
        print('Count people run')
        count_people = update.message.text
        self.request_data.update({'adults': count_people})
        print(self.request_data)

        send_msg = 'Введите кол-во отелей'
        update.message.reply_text(send_msg)

        self.logger().info(RUN)
        return STATES_BASE['count_hotel']

    def hotel(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода числа отелей """
        print('Count hotel run')
        count_hotel = update.message.text
        self.request_data.update({'count_hotel': count_hotel})
        print(self.request_data)

        send_msg = 'Введите кол-во фото'
        update.message.reply_text(send_msg)

        self.logger().info(RUN)
        return STATES_BASE['count_photo']

    def photo(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода числа фото """
        print('Count photo run')
        count_photo = update.message.text
        self.request_data.update({'count_photo': count_photo})
        print(self.request_data)
        # TODO продумать разветвление на bestdeal (будет другой ретерн на цены и удаленость от центра)
        # todo отсюда идет запрос для отелей + добавление в БД

        # data = hotel_handler.handler(
        #     command=self.__class__.__name__.lower(),
        #     city=self.request_data['query'],
        #     count_hotel=self.request_data['count_hotel'],
        #     count_photo=self.request_data['count_photo'],
        #     adults=self.request_data['count_people'],
        #     checkIn=self.request_data['checkIn'],
        #     checkOut=self.request_data['checkOut']
        # )

        self.logger().info(RUN)
        return ConversationHandler.END

    @staticmethod
    def cancel(update: Update, context: CallbackContext):
        return ConversationHandler.END

    def __call__(self, update: Update, context: CallbackContext):
        print(self.__class__.__name__, 'run')
        self.request_data.update({'command': self.__class__.__name__})

        send_msg = '{} запущен. \nВведите город, в который вы хотите поехать'.format(self.__class__.__name__)
        update.message.reply_text(send_msg)

        self.logger().info(RUN)
        return STATES_BASE['city']


@CollectionCommand('lowprice', TelebotHandler.COMMANDS)
class LowPrice(BaseSearchHotel):
    """ Поиск отелей по минимальной цене """
    pass


@CollectionCommand('highprice', TelebotHandler.COMMANDS)
class HighPrice(BaseSearchHotel):
    """ Поиск отелей по максимальной цене """
    pass


@CollectionCommand('bestdeal', TelebotHandler.COMMANDS)
class HighPrice(BaseSearchHotel):
    """ Поиск отелей по удаленности от центра """
    pass
