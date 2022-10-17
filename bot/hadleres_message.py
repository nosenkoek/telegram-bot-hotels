import requests

from settings import TODAY_DATE, FORMAT_DATE, BUTTON_HOTEL, BUTTON_PHOTO, \
    BUTTON_PEOPLE, DATABASE, \
    COUNT_MAX_PHOTO, COUNT_MAX_HOTEL

from bot.decorator import CollectionCommand
from bot.registry_request import Registry
from bot.command_handler import TelebotHandler
from logger.logger import logger_all, my_logger
from rapid.hotel_handler import RapidFacade

from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, \
    InputMediaPhoto, CallbackQuery
from telegram.ext import CallbackContext, ConversationHandler
from telegram.error import BadRequest
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import datetime, timedelta
from re import findall
from json import dumps
from typing import List


class Handler(ABC):
    """
     Базовый класс обработчик для 'диалога' с пользователем.
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
        super().registry.update_data(user_id, {
            'command': self.__class__.__name__.lower()
        })

        send_msg = '{} запущен. Для отмены введите cancel' \
                   '\nВведите город, в который вы хотите поехать'\
            .format(self.__class__.__name__.lower())
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

        calendar, step = DetailedTelegramCalendar(
            min_date=TODAY_DATE, locale='ru').build()
        send_msg = 'Введите дату начала поездки'
        msg_send = update.message.reply_text(send_msg, reply_markup=calendar)

        super().registry.update_data(user_id,
                                     {'query': city,
                                      'id_message_send': msg_send.message_id})
        return self.successor


@logger_all()
class CheckInHandler(Handler):
    """ Обработчик даты заезда"""

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Функция для чтения ввода даты заезда """
        query = update.callback_query
        user_id = query.from_user.id

        result, key, step = DetailedTelegramCalendar(min_date=TODAY_DATE,
                                                     locale='ru').process(
            query.data)

        if not result and key:
            query.edit_message_text('Введите дату начала поездки',
                                    reply_markup=key)
        elif result:
            result_str = result.strftime(FORMAT_DATE)
            super().registry.update_data(user_id, {'checkIn': result_str})

            min_date = result + timedelta(days=1)
            calendar, step = DetailedTelegramCalendar(min_date=min_date,
                                                      locale='ru').build()
            query.edit_message_text('Введите дату окончания поездки',
                                    reply_markup=calendar)
            return self.successor
        else:
            my_logger.warning('Нажата пустая кнопка')


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

        result, key, step = DetailedTelegramCalendar(min_date=min_date,
                                                     locale='ru').process(
            query.data)

        if not result and key:
            query.edit_message_text('Введите дату окончания поездки',
                                    reply_markup=key)
        elif result:
            result_str = result.strftime(FORMAT_DATE)
            super().registry.update_data(user_id, {'checkOut': result_str})
            markup = BUTTON_PEOPLE.keyboard()

            query.delete_message()
            msg_send = query.message.reply_text(
                'Введите количество проживающих в 1 номере (не больше 4)',
                reply_markup=markup)
            super().registry.update_data(user_id, {
                'id_message_send': msg_send.message_id})
            return self.successor
        else:
            my_logger.warning('Нажата пустая кнопка')


@logger_all()
class PeopleHandler(Handler):
    """ Обработчик количества людей, проживающих в номере"""

    @staticmethod
    def _answer() -> (str, InlineKeyboardMarkup):
        """
        Метод для создания кнопок и сообщения для пользователя.
        :return: send_msg - сообщение для пользователя, markup - объект кнопок
        """
        send_msg = 'Выберете количество отелей или ' \
                   'введите другое значение (не больше 10)'
        markup = BUTTON_HOTEL.keyboard()
        return send_msg, markup

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки нажатия кнопок """
        query = update.callback_query
        count_people = int(query.data)
        user_id = query.from_user.id
        super().registry.update_data(user_id, {'adults1': count_people})

        send_msg, markup = self._answer()
        query.message.edit_text(send_msg, reply_markup=markup)
        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текстового сообщения """
        user_id = update.message.from_user.id
        id_msg_send = super().registry.get_data(user_id).get('id_message_send')
        update.message.bot.delete_message(chat_id=update.message.chat_id,
                                          message_id=id_msg_send)
        count_people = update.message.text
        send_msg, markup = self._answer()
        try:
            count_people = int(count_people)
            if count_people < 0:
                count_people = abs(count_people)

            if count_people > 4 or not count_people:
                raise ValueError('Введен 0 или больше 4')
        except ValueError as err:
            markup = BUTTON_PEOPLE.keyboard()
            update.message.delete()
            msg_send = update.message.reply_text(
                'Введено неверное значение. '
                'Введите количество проживающих в 1 номере (не больше 4)',
                reply_markup=markup
            )
            super().registry.update_data(user_id, {
                'id_message_send': msg_send.message_id})
            my_logger.warning(f'Введено неверное значение {err}')
        else:
            msg_send = update.message.reply_text(send_msg, reply_markup=markup)
            super().registry.update_data(user_id,
                                         {'adults1': count_people,
                                          'id_message_send':
                                              msg_send.message_id})
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
        user_id = update.message.from_user.id
        id_msg_send = super().registry.get_data(user_id).get('id_message_send')
        update.message.bot.delete_message(chat_id=update.message.chat_id,
                                          message_id=id_msg_send)
        count_hotel = update.message.text
        try:
            count_hotel = int(count_hotel)
            if count_hotel < 0:
                count_hotel = abs(count_hotel)

            if count_hotel > COUNT_MAX_HOTEL or not count_hotel:
                raise ValueError('Введен 0 или больше 10')
        except ValueError as err:
            markup = BUTTON_HOTEL.keyboard()
            update.message.delete()
            msg_send = update.message.reply_text(
                'Введено неверное значение. Выберете кол-во отелей '
                'или введите другое значение (не больше 10)',
                reply_markup=markup
            )
            super().registry.update_data(user_id, {
                'id_message_send': msg_send.message_id})
            my_logger.warning(f'Введено неверное значение {err}')
        else:
            send_msg, markup = self._answer()
            msg_send = update.message.reply_text(send_msg, reply_markup=markup)
            super().registry.update_data(user_id,
                                         {'count_hotel': count_hotel,
                                          'id_message_send':
                                              msg_send.message_id})
            return self.successor


class CheckDataMixin():
    @staticmethod
    def _answer(request_data: dict) -> (str, InlineKeyboardMarkup, str):
        """
        Создание кнопок и формирование сообщения пользователю
        для проверки введенных данных.
        :return: send_msg - сообщение, markup - объект кнопок
        """
        data = [
            'Город: {}'.format(request_data.get('query')),
            'Даты: {} - {}'.format(request_data.get('checkIn'),
                                   request_data.get('checkOut')),
            'Количество проживающих: {}'.format(request_data.get('adults1')),
            'Количество отелей: {}'.format(request_data.get('count_hotel')),
            'Количество фото: {}'.format(request_data.get('count_photo')),
        ]

        if request_data.get('command') == 'bestdeal':
            data.append(
                'Диапазон цен: {} - {}'.format(request_data.get('priceMin'),
                                               request_data.get('priceMax')))
            data.append('Удаленность от центра: {} км'.format(
                request_data.get('distance')))

        data_msg = '\n'.join(data)
        send_msg = 'Проверьте данные:\n{}'.format(data_msg)
        button_yes = InlineKeyboardButton('Да', callback_data=1)
        button_no = InlineKeyboardButton('Нет', callback_data=0)
        markup = InlineKeyboardMarkup([[button_yes, button_no]])

        msg_start = 'Начать поиск?'
        return send_msg, markup, msg_start


@logger_all()
class PhotoCountHandler(Handler, CheckDataMixin):
    """ Обработчик количества фото отелей"""

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки нажатия кнопок """
        query = update.callback_query
        count_photo = int(query.data)
        user_id = query.from_user.id

        super().registry.update_data(user_id, {'count_photo': count_photo})
        query.delete_message()

        if super().registry.get_data(user_id).get('command') in ['lowprice',
                                                                 'highprice']:
            send_msg, markup, msg_start = self._answer(
                super().registry.get_data(user_id))
            print(super().registry.get_data(user_id))

            query.message.reply_text(send_msg)
            msg_send = query.message.reply_text(msg_start, reply_markup=markup)

        else:
            msg_send = query.message.reply_text(
                'Введите диапазон цен за сутки, руб.')

        super().registry.update_data(user_id,
                                     {'id_message_send': msg_send.message_id})
        return self.successor

    def message(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текстового сообщения """
        user_id = update.message.from_user.id
        id_msg_send = super().registry.get_data(user_id).get('id_message_send')
        update.message.bot.delete_message(chat_id=update.message.chat_id,
                                          message_id=id_msg_send)
        count_photo = update.message.text

        try:
            count_photo = int(count_photo)
            if count_photo < 0:
                count_photo = -count_photo

            if count_photo > COUNT_MAX_PHOTO:
                raise ValueError('Введено больше 5')
        except ValueError as err:
            markup = BUTTON_PHOTO.keyboard()
            update.message.delete()
            msg_send = update.message.reply_text(
                'Введено неверное значение. '
                'Выберете количество фото (не больше 5)',
                reply_markup=markup
            )
            super().registry.update_data(user_id, {
                'id_message_send': msg_send.message_id})
            my_logger.warning(f'Введено неверное значение {err}')
        else:
            super().registry.update_data(user_id, {'count_photo': count_photo})
            if super().registry.get_data(user_id).get('command') \
                    in ['lowprice', 'highprice']:
                send_msg, markup, msg_start = self._answer(
                    super().registry.get_data(user_id))
                print(super().registry.get_data(user_id))
                update.message.reply_text(send_msg)
                update.message.reply_text(msg_start, reply_markup=markup)
            else:
                update.message.reply_text('Введите диапазон  за сутки, руб.')
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

            prices = [int(price) for price in prices]
        except ValueError as err:
            my_logger.warning(f'Введено неверное значение {err}')
            update.message.reply_text(
                'Введено неверное значение. '
                'Введите диапазон цен за сутки, руб.')
        else:
            super().registry.update_data(user_id, {'priceMin': min(prices)})
            super().registry.update_data(user_id, {'priceMax': max(prices)})

            update.message.reply_text(
                'Введите максимальную удаленность от центра, км')
            return self.successor


@logger_all()
class DistanceHandler(Handler, CheckDataMixin):
    """ Обработчик удаленности от центра"""

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Хэндлер для обработки текста """
        distance = update.message.text
        user_id = update.message.from_user.id

        distance = distance.replace(',', '.')
        try:
            distance = float(distance)
            if distance < 0:
                distance = abs(distance)

            if not distance:
                raise ValueError('Введен 0')
        except ValueError as err:
            my_logger.warning(f'Введено неверное значение {err}')
            update.message.reply_text(
                'Введено неверное значение. '
                'Введите максимальную удаленность от центра, км')
        else:
            super().registry.update_data(user_id, {'distance': distance})
            send_msg, markup, msg_start = self._answer(
                super().registry.get_data(user_id))
            print(super().registry.get_data(user_id))
            update.message.reply_text(send_msg)
            update.message.reply_text(msg_start, reply_markup=markup)
            return self.successor


@logger_all()
class SearchHotelHandler(Handler):
    """ Обработка полученных данных от пользователя и поиск отелей """

    @staticmethod
    def _send_msg_waiting(query: CallbackQuery) -> int:
        """
        Отправка сообщения об ожидании ответа пользователю.
        :param query: callback_query
        :return: id отправленного сообщения для дальнейшего его удаления
        """
        try:
            msg_send = query.message.reply_animation(
                animation='https://tenor.com/view/'
                          'where-are-you-chick-searching-looking-gif-14978088',
            )
        except BadRequest as err:
            msg_send = query.message.reply_text('Ищем отели')
            print('Ошибка. Не найден файл по URL', err)
            my_logger.warning('Ошибка. Не найден файл по URL {}'.format(err))
        return msg_send.message_id

    @staticmethod
    def _request_hotel(request_data: dict, hotel_handler) -> list:
        """
        Формирование аргументов для запроса и получение списка отелей.
        :param request_data: словарь с данными, полученными от пользователя,
        :param hotel_handler: модуль для запроса отелей.
        :return: список найденных отелей с данными
        """
        param_request = request_data.copy()
        param_request.pop('id_message_send')
        command = param_request.pop('command')
        city = param_request.pop('query')
        count_hotels = param_request.pop('count_hotel')
        count_photo = param_request.pop('count_photo')

        hotels = hotel_handler.handler(command, city, count_hotels,
                                       count_photo, **param_request)
        return hotels

    @staticmethod
    def _add_request_db(user_id: int, request_data: dict, hotels: list):
        """
        Добавление строки в БД.
        :param user_id: уникальный id пользователя,
        :param request_data: запрос пользователя
        :param hotels: список отелей.
        """
        hotels_dict = {}

        for hotel in hotels:
            hotels_dict.update({hotel.get('name'): hotel.get('url')})

        hotel_json = dumps(hotels_dict)

        DATABASE.create(
            user_id=user_id,
            key_table='user_requests',
            command_request=request_data.get('command'),
            city_request=request_data.get('query'),
            hotels=hotel_json
        )

    def _valid_hotels(self, query: CallbackQuery, user_id: int,
                      request_data: dict, id_msg_send: int):
        """
        Запрос отелей и отправка сообщений пользователю в случае ошибки,
        в случае успеха - запись в БД.
        :param query: callback_query,
        :param user_id: уникальный id пользователя,
        :param request_data: словарь с данными запроса пользователя,
        :param id_msg_send: id сообщения для удаления,
        :return: обработанный список отелей от rapid
        """
        hotel_handler = RapidFacade()
        hotels = []

        try:
            hotels = self._request_hotel(request_data, hotel_handler)
        except ValueError as err:
            print('Ошибка - отели не найдены {}'.format(err))
            my_logger.warning('Ошибка - отели не найдены {}'.format(err))
            if 'Город не найден' in err.args:
                query.message.reply_text(str(err))
            else:
                query.message.reply_text('По вашему запросу не найдено отелей')
        else:
            self._add_request_db(user_id, request_data, hotels)
        finally:
            query.bot.delete_message(chat_id=query.message.chat_id,
                                     message_id=id_msg_send)

        return hotels

    @staticmethod
    def _data_hotel_for_msg(hotel: dict) -> str:
        """
        Формирование описания отеля для пользователя.
        :param hotel: данные об отеле,
        :return: полный текст сообщения.
        """
        stars = '\u2b50\ufe0f' * int(hotel.get("star"))
        msg = [
            f'<b>{hotel.get("name")}</b>\t\t\t {stars}',
            str(hotel.get('address')),
            f'Рейтинг: {hotel.get("rating")}',
            f'Удаленность от центра: {hotel.get("distance")}',
            f'Цена за ночь: {int(hotel.get("price"))} руб. \t\t\t '
            f'Общая стоимость: <b>{int(hotel.get("total_price"))} руб.</b>',
            f'Сайт: {hotel.get("url")}'
        ]

        send_msg = '\n'.join(msg)
        return send_msg

    @staticmethod
    def _photo_hotel(hotel: dict) -> List[InputMediaPhoto]:
        """
        Формирование медиа группы отеля для отправки пользователю.
        :param hotel: данные об отеле,
        :return: список с подготовленными фото для отправки.
        """
        photo_group = []
        photo_url = hotel.get('photo')

        if not photo_url:
            raise ValueError('Нет фото')

        for url in hotel.get('photo'):
            photo_group.append(InputMediaPhoto(media=url))
        return photo_group

    def _send_photo(self, query: CallbackQuery, hotel: dict) -> None:
        """
        Отправка фото для отелей.
        :param query: callback_query,
        :param hotel: данные отеля.
        """
        try:
            photo_group = self._photo_hotel(hotel)
        except ValueError as err:
            my_logger.warning('Ошибка. Не найдено фото {}'.format(err))
            query.message.reply_text('Для этого отеля фото не найдено')
        else:
            try:
                query.message.reply_media_group(media=photo_group)
            except BadRequest as err:
                query.message.reply_text(
                    'Ошибка сервера. Фото можно посмотреть на сайте')
                my_logger.error(
                    'Ошибка. Не создана медиа-группа. {}'.format(err))

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Обрабатывает ответ на вопрос о поиске ответа
        и отправляет список отелей """
        query = update.callback_query
        user_id = query.from_user.id
        answer = query.data

        request_data = super().registry.get_data(user_id).copy()
        super().registry.delete_data(user_id)

        count_photo = request_data.get('count_photo')
        query.delete_message()

        if answer == '1':
            id_msg_send = self._send_msg_waiting(query)

            try:
                hotels = self._valid_hotels(query, user_id, request_data,
                                            id_msg_send)

                for hotel in hotels:
                    send_msg = self._data_hotel_for_msg(hotel)
                    query.message.reply_text(send_msg,
                                             disable_web_page_preview=True,
                                             parse_mode='HTML')

                    if count_photo:
                        self._send_photo(query, hotel)
            except requests.ReadTimeout as timeout_err:
                my_logger.exception(
                    'Ошибка ReadTimeout: {}'.format(timeout_err))
                print('Ошибка ReadTimeout:', timeout_err)
                query.message.reply_text(
                    'Долгое ожидание ответа с сервера. Попробуйте позднее')
            except requests.HTTPError as http_err:
                my_logger.exception('Ошибка HTTP: {}'.format(http_err))
                print('Ошибка HTTP:', http_err)
                query.message.reply_text('Ошибка запроса. Попробуйте позднее')
            except NameError as err:
                my_logger.warning('Ошибка в запросе {}'.format(err))
                query.message.reply_text('Ошибка запроса. Попробуйте позднее.')
        else:
            query.message.reply_text('До связи!')
        return self.successor


class HandlerFactory():
    """ Фабрика обработчиков """

    handlers = {
        'city': CityHandle,
        'check_in': CheckInHandler,
        'check_out': CheckOutHandler,
        'people': PeopleHandler,
        'hotel': HotelCountHandler,
        'photo': PhotoCountHandler,
        'prices': PricesHandler,
        'distance': DistanceHandler,
        'search': SearchHotelHandler,
    }

    def create_handler(self, name_handler: str, number: int):
        handler_cls = self.handlers[name_handler]
        return handler_cls(number)


@logger_all()
class Cancel():
    """ Класс для отмены выполнения команды """

    def __call__(self, update: Update, context: CallbackContext):
        print('Cancel run')
        user_id = update.message.from_user.id
        try:
            id_msg_send = Handler.registry.get_data(user_id).pop(
                'id_message_send')
        except KeyError as err:
            print('Cancel. Нет сообщения для удаления', err)
            my_logger.warning(f'Cancel. Нет сообщения для удаления. {err}')
        else:
            update.message.bot.delete_message(chat_id=update.message.chat_id,
                                              message_id=id_msg_send)
        update.message.reply_text('Отмена')
        Handler.registry.delete_data(user_id)
        return ConversationHandler.END
