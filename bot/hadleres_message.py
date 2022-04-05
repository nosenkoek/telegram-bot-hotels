from settings import TODAY_DATE, FORMAT_DATE, BUTTON_HOTEL, BUTTON_PHOTO, BUTTON_PEOPLE

from bot.decorator import CollectionCommand
from bot.registry_request import Registry
from bot.command_handler import TelebotHandler
from logger.logger import logger_all, my_logger
from rapid.hotel_handler import RapidFacade

from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler
from time import sleep
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import datetime, timedelta
from re import findall


class Handler(ABC):
    """
     Базовый класс обработчик для 'диалога' с пользователем. Для цепочки обязанностей.
     Args:
         successor: номер текущего обработчика
     """
    registry = Registry()

    def __init__(self, successor: int):
        self.successor = successor

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class BaseSearchHandler(Handler):
    """ Базовый класс для старта команд lowprice, highprice, bestdeal"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        print(self.__class__.__name__, 'run')
        user_id = update.message.from_user.id

        super().registry.add_new_id(user_id)
        super().registry.update_data(user_id, {'command': self.__class__.__name__.lower()})

        send_msg = '{} запущен. Для отмены введите cancel' \
                   '\nВведите город, в который вы хотите поехать'.format(self.__class__.__name__.lower())
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
        city = update.message.text
        user_id = update.message.from_user.id

        super().registry.update_data(user_id, {'query': city})

        calendar, step = DetailedTelegramCalendar(min_date=TODAY_DATE).build()
        send_msg = 'Введите дату начала поездки {}'.format(LSTEP[step])
        update.message.reply_text(send_msg, reply_markup=calendar)
        return self.successor


@logger_all()
class CheckInHandler(Handler):
    """ Обработчик даты заезда"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода даты заезда """
        query = update.callback_query
        user_id = query.from_user.id

        result, key, step = DetailedTelegramCalendar(min_date=TODAY_DATE).process(query.data)

        if not result and key:
            query.edit_message_text(f'Введите дату начала поездки {LSTEP[step]}', reply_markup=key)
        elif result:
            result_str = result.strftime(FORMAT_DATE)
            super().registry.update_data(user_id, {'checkIn': result_str})

            min_date = result + timedelta(days=1)
            calendar, step = DetailedTelegramCalendar(min_date=min_date).build()
            query.edit_message_text(f'Введите дату окончания поездки {LSTEP[step]}', reply_markup=calendar)
            return self.successor
        else:
            print('Нажата пустая кнопка')


@logger_all()
class CheckOutHandler(Handler):
    """ Обработчик даты выезда"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода даты выезда """
        query = update.callback_query
        user_id = query.from_user.id

        check_in = super().registry.get_data(user_id).get('checkIn')
        check_in = datetime.strptime(check_in, FORMAT_DATE)
        min_date = check_in.date() + timedelta(days=1)

        result, key, step = DetailedTelegramCalendar(min_date=min_date).process(query.data)

        if not result and key:
            query.edit_message_text(f'Введите дату окончания поездки {LSTEP[step]}', reply_markup=key)
        elif result:
            result_str = result.strftime(FORMAT_DATE)
            super().registry.update_data(user_id, {'checkOut': result_str})
            markup = BUTTON_PEOPLE.keyboard()

            query.delete_message()
            query.message.reply_text('Введите количество проживающих в 1 номере (не больше 4)', reply_markup=markup)

            return self.successor
        else:
            print('Нажата пустая кнопка')


@logger_all()
class PeopleHandler(Handler):
    """ Обработчик количества людей, проживающих в номере"""
    @staticmethod
    def _answer() -> (str, InlineKeyboardMarkup):
        """
        Метод для создания кнопок и сообщения для пользователя.
        :return: send_msg - сообщение для пользователя, markup - объект кнопок
        """
        send_msg = 'Выберете кол-во отелей или введите другое значение (не больше 10)'
        markup = BUTTON_HOTEL.keyboard()
        return send_msg, markup

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки нажатия кнопок """
        query = update.callback_query
        user_id = query.from_user.id
        super().registry.update_data(user_id, {'adults1': query.data})

        send_msg, markup = self._answer()
        query.message.edit_text(send_msg, reply_markup=markup)
        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текстового сообщения """
        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1))
        count_people = update.message.text
        user_id = update.message.from_user.id
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
            super().registry.update_data(user_id, {'adults1': count_people})
            update.message.reply_text(send_msg, reply_markup=markup)
            return self.successor


@logger_all()
class HotelCountHandler(Handler):
    """ Обработчик количества запрашиваемых отелей"""
    @staticmethod
    def _answer() -> (str, InlineKeyboardMarkup):
        """
        Создание кнопок и сообщения пользователю.
        :return: send_msg - сообщение, markup - объект кнопок
        """
        send_msg = 'Выберете количество фото (не больше 5)'
        markup = BUTTON_PHOTO.keyboard()
        return send_msg, markup

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки нажатия кнопок """
        query = update.callback_query
        count_hotel = int(query.data)
        user_id = query.from_user.id
        super().registry.update_data(user_id, {'count_hotel': count_hotel})

        send_msg, markup = self._answer()
        query.message.edit_text(send_msg, reply_markup=markup)
        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текстового сообщения  """
        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1))
        count_hotel = update.message.text
        user_id = update.message.from_user.id
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
            super().registry.update_data(user_id, {'count_hotel': count_hotel})

            send_msg, markup = self._answer()
            update.message.reply_text(send_msg, reply_markup=markup)
            return self.successor


class CheckDataMixin():
    @staticmethod
    def _answer(request_data: dict) -> (str, InlineKeyboardMarkup):
        """
        Создание кнопок и формирование сообщения пользователю.
        :return: send_msg - сообщение, markup - объект кнопок
        """
        try:
            data = [
                'Город: {}'.format(request_data.get('query')),
                'Даты: {} - {}'.format(request_data.get('checkIn'),
                                       request_data.get('checkOut')),
                'Количество проживающих: {}'.format(request_data.get('adults1')),
                'Количество отелей: {}'.format(request_data.get('count_hotel')),
                'Количество фото: {}'.format(request_data.get('count_photo')),
            ]
            if request_data.get('command') == 'bestdeal':
                data.append('Диапазон цен: {} - {}'.format(request_data.get('priceMin'), request_data.get('priceMax')))
                data.append('Удаленность от центра: {}'.format(request_data.get('distance')))
        except ValueError:
            raise ValueError

        data_msg = '\n'.join(data)
        send_msg = 'Проверьте данные:\n{}'.format(data_msg)
        button_yes = InlineKeyboardButton('Yes', callback_data=1)
        button_no = InlineKeyboardButton('No', callback_data=0)
        markup = InlineKeyboardMarkup([[button_yes, button_no]])
        return send_msg, markup


@logger_all()
class PhotoCountHandler(Handler, CheckDataMixin):
    """ Обработчик количества фото отелей"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки нажатия кнопок """
        query = update.callback_query
        count_photo = int(query.data)
        user_id = query.from_user.id

        super().registry.update_data(user_id, {'count_photo': count_photo})

        if super().registry.get_data(user_id).get('command') in ['lowprice', 'highprice']:
            send_msg, markup = self._answer(super().registry.get_data(user_id))
            print(super().registry.get_data(user_id))

            query.delete_message()
            query.message.reply_text(send_msg)
            query.message.reply_text('Начать поиск?', reply_markup=markup)

        if super().registry.get_data(user_id).get('command') == 'bestdeal':
            query.delete_message()
            query.message.reply_text('Введите диапазон цен, руб.')

        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текстового сообщения """
        update.message.bot.delete_message(chat_id=update.message.chat_id, message_id=(update.message.message_id - 1))
        count_photo = update.message.text
        user_id = update.message.from_user.id
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
            super().registry.update_data(user_id, {'count_photo': count_photo})
            if super().registry.get_data(user_id).get('command') in ['lowprice', 'highprice']:
                send_msg, markup = self._answer(super().registry.get_data(user_id))
                print(super().registry.get_data(user_id))
                update.message.reply_text(send_msg)
                update.message.reply_text('Начать поиск?', reply_markup=markup)

            if super().registry.get_data(user_id).get('command') == 'bestdeal':
                update.message.reply_text('Введите диапазон цен, руб.')

            return self.successor


@logger_all()
class PricesHandler(Handler):
    """ Обработчик диапазона цен"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текста """
        prices = update.message.text
        user_id = update.message.from_user.id

        try:
            prices = findall(r'\d+', prices)
            if len(prices) != 2:
                raise ValueError
        except ValueError:
            update.message.bot.delete_message(chat_id=update.message.chat_id,
                                              message_id=(update.message.message_id - 1))
            update.message.delete()
            update.message.reply_text('Введено неверное значение. Введите диапазон цен, руб.')
        else:
            super().registry.update_data(user_id, {'priceMin': min(prices)})
            super().registry.update_data(user_id, {'priceMax': max(prices)})

            update.message.reply_text('Введите максимальную удаленность от центра')
            return self.successor


@logger_all()
class DistanceHandler(Handler, CheckDataMixin):
    """ Обработчик удаленность от центра"""
    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текста """
        distance = update.message.text
        user_id = update.message.from_user.id

        distance = distance.replace(',', '.')
        try:
            distance = float(distance)
        except ValueError:
            update.message.bot.delete_message(chat_id=update.message.chat_id,
                                              message_id=(update.message.message_id - 1))
            update.message.delete()
            update.message.reply_text('Введено неверное значение. Введите максимальную удаленность от центра')
        else:
            super().registry.update_data(user_id, {'distance': distance})
            send_msg, markup = self._answer(super().registry.get_data(user_id))
            print(super().registry.get_data(user_id))
            update.message.reply_text(send_msg)
            update.message.reply_text('Начать поиск?', reply_markup=markup)
            return self.successor


@logger_all()
class SearchHandler(Handler):
    """ Заглушка для телеграмма. Обработка полученных данных от пользователя и поиск отелей """
    # TODO не забыть убрать в завершающей стадии
    def __call__(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        user_id = query.from_user.id
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

        super().registry.delete_data(user_id)
        return self.successor


@logger_all()
class SearchHotelHandler(Handler):
    """ Обработка полученных данных от пользователя и поиск отелей """
    def __call__(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        user_id = query.from_user.id
        answer = query.data

        request_data = super().registry.get_data(user_id).copy()
        super().registry.delete_data(user_id)

        if answer == '1':
            hotel_handler = RapidFacade()
            send_msg = 'Ищем отели'    # todo сюда добавить что-нибудь красивое
            query.edit_message_text(send_msg)
            try:
                command = request_data.get('command')
                city = request_data.get('query')
                count_hotels = request_data.get('count_hotel')
                count_photo = request_data.get('count_photo')
                # todo как "скормить" словарь вместо kwargs
                check_in = request_data.get('checkIn')
                check_out = request_data.get('checkOut')
                people = request_data.get('adults1')

                if command == 'bestdeal':
                    price_min = request_data.get('priceMin')
                    price_max = request_data.get('priceMax')
                    distance = request_data.get('distance')

                    hotels = hotel_handler.handler(command, city, count_hotels, count_photo,
                                                   checkIn=check_in, checkOut=check_out, adults1=people,
                                                   priceMin=price_min, priceMax=price_max, distance=distance)
                else:

                    hotels = hotel_handler.handler(command, city, count_hotels, count_photo,
                                                   checkIn=check_in, checkOut=check_out, adults1=people)

            except NameError as err:
                my_logger.exception('Ошибка в запросе {}'.format(err))
                query.delete_message()
                query.message.reply_text('Ошибка запроса. Попробуйте позднее.')
            except ValueError as err:
                my_logger.exception('Ошибка - отели не найдены {}'.format(err))
                query.delete_message()
                query.message.reply_text('По вашему запросу не найдено отелей')
            else:
                query.delete_message()

                for hotel in hotels:
                    # TODO навести красоту для вывода
                    query.message.reply_text(hotel)
        else:
            send_msg = 'До связи! '
            query.edit_message_text(send_msg)
        return self.successor


class HandlerFactory():
    """ Фабрика обработчиков """

    handlers = {
        'city': CityHandle,
        # 'date': DateHandler,
        'check_in': CheckInHandler,
        'check_out': CheckOutHandler,
        'people': PeopleHandler,
        'hotel': HotelCountHandler,
        'photo': PhotoCountHandler,
        'prices': PricesHandler,
        'distance': DistanceHandler,
        # 'search': SearchHandler,   # - без прямого запроса на рапид, заглушка для телеграмма
        'search': SearchHotelHandler,
    }

    def create_handler(self, name_handler: str, number: int):
        handler_cls = self.handlers[name_handler]
        return handler_cls(number)


@logger_all()
class Cancel():
    def __call__(self, update: Update, context: CallbackContext):
        print('Cancel run')
        update.message.bot.delete_message(chat_id=update.message.chat_id,
                                          message_id=(update.message.message_id - 1))
        update.message.reply_text('Отмена')
        return ConversationHandler.END
