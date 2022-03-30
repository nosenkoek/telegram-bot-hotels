from settings import TODAY_DATE, FORMAT_DATE, BUTTON_HOTEL, BUTTON_PHOTO, BUTTON_PEOPLE

from bot.decorator import CollectionCommand
from db.db_handler import DataUsers
from logger.logger import logger_all

from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler
from time import sleep
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import datetime, timedelta

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


class Handler(ABC):
    """
     Базовый класс обработчик для 'диалога' с пользователем. Для цепочки обязанностей.
     Args:
         _successor: номер текущего обработчика
     """
    request_data = {}

    def __init__(self, successor: int):
        self._successor = successor

    @property
    def successor(self) -> int:
        return self._successor

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class BaseSearchHandler(Handler):
    """ Базовый класс для старта команд lowprice, highprice, bestdeal"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        super().request_data.clear()
        print(self.__class__.__name__, 'run')
        super().request_data.update({'command': self.__class__.__name__.lower()})

        send_msg = '{} запущен. \nВведите город, в который вы хотите поехать'.format(self.__class__.__name__)
        update.message.reply_text(send_msg)
        return self.successor


@logger_all()
@CollectionCommand('lowprice', TelebotHandler.COMMANDS)
class LowPrice(BaseSearchHandler):
    """ Поиск отелей по минимальной цене """
    pass


@logger_all()
@CollectionCommand('highprice', TelebotHandler.COMMANDS)
class HighPrice(BaseSearchHandler):
    """ Поиск отелей по максимальной цене """
    pass


@logger_all()
@CollectionCommand('bestdeal', TelebotHandler.COMMANDS)
class BestDeal(BaseSearchHandler):
    """ Поиск отелей по удаленности от центра """
    pass


@logger_all()
class CityHandle(Handler):
    """ Обработчик города"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода города пользователя """
        print('City run')
        city = update.message.text
        super().request_data.update({'query': city})
        print(super().request_data)

        calendar, step = DetailedTelegramCalendar(min_date=TODAY_DATE).build()
        send_msg = 'Введите дату начала поездки {}'.format(LSTEP[step])
        update.message.reply_text(send_msg, reply_markup=calendar)
        return self.successor


@logger_all()
class DateHandler(Handler):
    """ Обработчик даты заезда"""
    def min_date(self) -> (datetime, str):
        if 'checkIn' in super().request_data.keys():
            send_msg = 'Введите дату завершения поездки'
            check_in = super().request_data['checkIn']
            check_in = datetime.strptime(check_in, FORMAT_DATE)
            min_date = check_in.date() + timedelta(days=1)
        else:
            send_msg = 'Введите дату начала поездки'
            min_date = TODAY_DATE

        return min_date, send_msg

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода даты check in """
        print('Check in run')

        query = update.callback_query

        min_date, send_msg = self.min_date()

        result, key, step = DetailedTelegramCalendar(min_date=min_date).process(query.data)

        if not result and key:
            query.edit_message_text(f'{send_msg} {LSTEP[step]}', reply_markup=key)
        elif result:
            result_str = result.strftime(FORMAT_DATE)

            if 'checkIn' not in super().request_data.keys():
                super().request_data.update({'checkIn': result_str})

                calendar, step = DetailedTelegramCalendar(min_date=min_date).build()
                query.edit_message_text(f'Введите дату завершения поездки {LSTEP[step]}', reply_markup=calendar)
            else:
                super().request_data.update({'checkOut': result_str})
                markup = BUTTON_PEOPLE.keyboard()

                query.delete_message()
                query.message.reply_text('Введите количество проживающих в 1 номере (не больше 4)', reply_markup=markup)

            print(super().request_data)
            return self.successor
        else:
            raise ValueError


@logger_all()
class PeopleHandler(Handler):
    """ Обработчик количества людей, проживающих в номере"""
    @staticmethod
    def _answer() -> (str, InlineKeyboardMarkup):
        send_msg = 'Выберете кол-во отелей или введите другое значение (не больше 10)'
        markup = BUTTON_HOTEL.keyboard()
        return send_msg, markup

    def __call__(self, update: Update, context: CallbackContext) -> int:
        print('Count people run')
        query = update.callback_query
        super().request_data.update({'adults1': query.data})

        send_msg, markup = self._answer()
        query.message.edit_text(send_msg, reply_markup=markup)
        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        print('Count people message run')
        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1))
        count_people = update.message.text
        send_msg, markup = self._answer()
        try:
            count_people = int(count_people)
            if count_people > 4:
                raise ValueError
        except ValueError:
            markup = BUTTON_PEOPLE.keyboard()
            update.message.delete()
            update.message.reply_text(
                'Введено неверное значение. Введите количество проживающих в 1 номере (не больше 4)',
                reply_markup=markup
            )
        else:
            super().request_data.update({'adults1': count_people})
            print(super().request_data)
            update.message.reply_text(send_msg, reply_markup=markup)
            return self.successor


@logger_all()
class HotelCountHandler(Handler):
    """ Обработчик количества запрашиваемых отелей"""
    @staticmethod
    def _answer() -> (str, InlineKeyboardMarkup):
        send_msg = 'Выберете количество фото (не больше 5)'
        markup = BUTTON_PHOTO.keyboard()
        return send_msg, markup

    def __call__(self, update: Update, context: CallbackContext) -> int:
        print('Count hotel run')
        query = update.callback_query
        count_hotel = int(query.data)
        super().request_data.update({'count_hotel': count_hotel})
        print(super().request_data)

        send_msg, markup = self._answer()
        query.message.edit_text(send_msg, reply_markup=markup)
        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        print('Count hotel message run')
        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1))
        count_hotel = update.message.text
        try:
            count_hotel = int(count_hotel)
            if count_hotel > 10:
                raise ValueError
        except ValueError:
            markup = BUTTON_HOTEL.keyboard()
            update.message.delete()
            update.message.reply_text(
                'Введено неверное значение. Выберете кол-во отелей или введите другое значение (не больше 10)',
                reply_markup=markup
            )
        else:
            super().request_data.update({'count_hotel': count_hotel})
            print(super().request_data)

            send_msg, markup = self._answer()
            update.message.reply_text(send_msg, reply_markup=markup)
            return self.successor


@logger_all()
class PhotoCountHandler(Handler):
    """ Обработчик количества фото отелей"""
    def _answer(self):
        try:
            data = [
                'Город: {}'.format(super().request_data['query']),
                'Даты: {} - {}'.format(super().request_data['checkIn'], super().request_data['checkOut']),
                'Количество проживающих: {}'.format(super().request_data['adults1']),
                'Количество отелей: {}'.format(super().request_data['count_hotel']),
                'Количество фото: {}'.format(super().request_data['count_photo']),
            ]
        except ValueError:
            raise ValueError

        data_msg = '\n'.join(data)
        send_msg = 'Проверьте данные:\n{}'.format(data_msg)
        button_yes = InlineKeyboardButton('Yes', callback_data=1)
        button_no = InlineKeyboardButton('No', callback_data=0)
        markup = InlineKeyboardMarkup([[button_yes, button_no]])
        return send_msg, markup

    def __call__(self, update: Update, context: CallbackContext) -> int:
        print('Count photo run')
        query = update.callback_query

        count_photo = int(query.data)

        super().request_data.update({'count_photo': count_photo})
        print(super().request_data)

        if super().request_data['command'] in ['lowprice', 'highprice']:
            send_msg, markup = self._answer()

            query.delete_message()
            query.message.reply_text(send_msg)
            query.message.reply_text('Начать поиск?', reply_markup=markup)

        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        print('Count message photo run')
        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1))
        count_photo = update.message.text
        try:
            count_photo = int(count_photo)
            if count_photo > 5:
                raise ValueError
        except ValueError:
            markup = BUTTON_PHOTO.keyboard()
            update.message.delete()
            update.message.reply_text(
                'Введено неверное значение. Выберете количество фото (не больше 5)',
                reply_markup=markup
            )
        else:
            super().request_data.update({'count_photo': count_photo})
            print(super().request_data)

            if super().request_data['command'] in ['lowprice', 'highprice']:
                send_msg, markup = self._answer()
                update.message.reply_text(send_msg)
                update.message.reply_text('Начать поиск?', reply_markup=markup)

            return self.successor


@logger_all()
class SearchHandler(Handler):
    """ Обработка полученных данных от пользователя и поиск отелей """
    def __call__(self, update: Update, context: CallbackContext) -> int:
        print('SearchHandler run')
        query = update.callback_query
        answer = query.data

        if answer == '1':
            send_msg = 'Ищем отели'
            query.edit_message_text(send_msg)
            sleep(3)
            query.delete_message()
            query.message.reply_text('Отель 1')
            query.message.reply_text('Отель 2')
            query.message.reply_text('Отель 3')
        else:
            send_msg = 'До связи! '
            query.edit_message_text(send_msg)


        # TODO сюда запрос от отелей, подумать как скормить без обработки, кваргами + вытаскивание аргов

        # data = f"command={self.__class__.__name__.lower()}, city= {self.request_data['query']}, " \
        #        f"count_hotel={self.request_data['count_hotel']}, count_photo={self.request_data['count_photo']}," \
        #        f"adults={self.request_data['count_people']}, checkIn={self.request_data['checkIn']}," \
        #        f"checkOut={self.request_data['checkOut']}"
        #
        # print(data)
        # update.message.reply_text(f'{send_msg} \n {data}')
        return self.successor

# TODO добавить хэндлеры для БЕСТДИЛ диапазон цен и удаленность от города

@logger_all()
class Cancel(Handler):
    def __call__(self, *args, **kwargs):
        print('Cancel run')
        return ConversationHandler.END
