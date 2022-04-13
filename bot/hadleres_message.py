from settings import TODAY_DATE, FORMAT_DATE, BUTTON_HOTEL, BUTTON_PHOTO, BUTTON_PEOPLE, DATABASE

from bot.decorator import CollectionCommand
from bot.registry_request import Registry
from bot.command_handler import TelebotHandler
from logger.logger import logger_all, my_logger
from rapid.hotel_handler import RapidFacade

from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery
from telegram.ext import CallbackContext, ConversationHandler
from telegram.error import BadRequest
from time import sleep
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import datetime, timedelta
from re import findall
from json import dumps
from typing import List

# todo посмотреть создание модулей


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
        count_people = int(query.data)
        user_id = query.from_user.id
        super().registry.update_data(user_id, {'adults1': count_people})

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
    def _answer(request_data: dict) -> (str, InlineKeyboardMarkup, str):
        """
        Создание кнопок и формирование сообщения пользователю для проверки введенных данных.
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
            data.append('Диапазон цен: {} - {}'.format(request_data.get('priceMin'), request_data.get('priceMax')))
            data.append('Удаленность от центра: {} км'.format(request_data.get('distance')))

        data_msg = '\n'.join(data)
        send_msg = 'Проверьте данные:\n{}'.format(data_msg)
        button_yes = InlineKeyboardButton('Yes', callback_data=1)
        button_no = InlineKeyboardButton('No', callback_data=0)
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

        if super().registry.get_data(user_id).get('command') in ['lowprice', 'highprice']:
            send_msg, markup, msg_start = self._answer(super().registry.get_data(user_id))
            print(super().registry.get_data(user_id))

            query.delete_message()
            query.message.reply_text(send_msg)
            query.message.reply_text(msg_start, reply_markup=markup)

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
                send_msg, markup, msg_start = self._answer(super().registry.get_data(user_id))
                print(super().registry.get_data(user_id))
                update.message.reply_text(send_msg)
                update.message.reply_text(msg_start, reply_markup=markup)

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

            update.message.reply_text('Введите максимальную удаленность от центра, км')
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
        except ValueError:
            update.message.bot.delete_message(chat_id=update.message.chat_id,
                                              message_id=(update.message.message_id - 1))
            update.message.delete()
            update.message.reply_text('Введено неверное значение. Введите максимальную удаленность от центра, км')
        else:
            super().registry.update_data(user_id, {'distance': distance})
            send_msg, markup, msg_start = self._answer(super().registry.get_data(user_id))
            print(super().registry.get_data(user_id))
            update.message.reply_text(send_msg)
            update.message.reply_text(msg_start, reply_markup=markup)
            return self.successor


@logger_all()
class SearchHandler(Handler):
    """ Заглушка для телеграмма. Обработка полученных данных от пользователя и поиск отелей """

    # TODO не забыть убрать в завершающей стадии

    @staticmethod
    def _data_hotel_for_msg(hotel: dict) -> str:
        stars = '\u2b50\ufe0f' * int(hotel.get("star"))
        msg = [
            f'{hotel.get("name")}\t\t\t {stars}',
            hotel.get('address'),
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
        photo_group = []
        photo_url = hotel.get('photo')

        if photo_url[0] == 'нет фото':
            raise ValueError('Нет фото')

        for url in hotel.get('photo'):
            photo_group.append(InputMediaPhoto(media=url))
        return photo_group

    def __call__(self, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        user_id = query.from_user.id
        answer = query.data
        count_photo = super().registry.get_data(user_id).get('count_photo')

        if answer == '1':
            query.delete_message()
            try:
                query.message.reply_animation(
                    animation='https://tenor.com/view/where-are-you-chick-searching-looking-gif-14978088',
                )
            except BadRequest as err:
                query.message.reply_text('Ищем отели')
                print('Ошибка. Не найден файл по URL', err)
                my_logger.warning('Ошибка. Не найден файл по URL {}'.format(err))

            sleep(5)
            query.bot.delete_message(chat_id=query.message.chat_id, message_id=(query.message.message_id + 1))

            hotels = [
                {
                    "id": 233832,
                    "name": "CYAN HOTEL ROISSY VILLEPINTE PARC DES EXPOSITIONS",
                    "address": "53 Avenue des Nations",
                    "star": 2.0,
                    "rating": 6.6,
                    "distance": "11 miles",
                    "price": 2963.05,
                    "total_price": 5926.1,
                    "url": "https://uk.hotels.com/ho233832",
                    "photo": [
                        "https://exp.cdn-hotels.com/hotels/2000000/1180000/1179300/1179215/bfceb608_b.jpg",
                        "https://exp.cdn-hotels.com/hotels/2000000/1180000/1179300/1179215/w3226h2693x391y129-42ea75b6_b.jpg",
                        "https://exp.cdn-hotels.com/hotels/2000000/1180000/1179300/1179215/06649975_b.jpg"
                    ]
                },
                {
                    "id": 1251140384,
                    "name": "Chambre privée à Drancy",
                    "address": "7 rue Michelet",
                    "star": 0.0,
                    "rating": 6.6,
                    "distance": "6.3 miles",
                    "price": 3292.44,
                    "total_price": 6584.88,
                    "url": "https://uk.hotels.com/ho1251140384",
                    "photo": [
                        "https://exp.cdn-hotels.com/hotels/40000000/39070000/39066900/39066887/6657f572_b.jpg",
                        "https://exp.cdn-hotels.com/hotels/40000000/39070000/39066900/39066887/2e846005_b.jpg",
                        "https://exp.cdn-hotels.com/hotels/40000000/39070000/39066900/39066887/2d5a1e29_b.jpg"
                    ]
                },
                {
                    "id": 252423,
                    "name": "Première Classe Versailles - St Cyr l'Ecole",
                    "address": "Rue du Pont de Dreux",
                    "star": 0.0,
                    "rating": 7.2,
                    "distance": "14 miles",
                    "price": 3414.21,
                    "total_price": 6828.42,
                    "url": "https://uk.hotels.com/ho252423",
                    "photo": [
                        "https://exp.cdn-hotels.com/hotels/2000000/1620000/1619900/1619807/e093b457_b.jpg",
                        "https://exp.cdn-hotels.com/hotels/2000000/1620000/1619900/1619807/a93fdd16_b.jpg",
                        "https://exp.cdn-hotels.com/hotels/2000000/1620000/1619900/1619807/6c82b100_b.jpg"
                    ]
                }
            ]

            for hotel in hotels:
                send_msg = self._data_hotel_for_msg(hotel)
                query.message.reply_text(send_msg, disable_web_page_preview=True, parse_mode='HTML')

                if count_photo:
                    try:
                        photo_group = self._photo_hotel(hotel)
                    except ValueError as err:
                        my_logger.warning('Ошибка. Не найдено фото {}'.format(err))
                        query.message.reply_text('Для этого отеля фото не найдено')
                    else:
                        query.message.reply_media_group(media=photo_group)

        else:
            send_msg = 'До связи! '
            query.edit_message_text(send_msg)

        super().registry.delete_data(user_id)
        return self.successor


@logger_all()
class SearchHotelHandler(Handler):
    """ Обработка полученных данных от пользователя и поиск отелей """
    @staticmethod
    def _send_msg_waiting(query: CallbackQuery) -> None:
        """
        Отправка сообщения об ожидании ответа пользователю.
        :param query: callback_query
        """
        try:
            query.message.reply_animation(
                animation='https://tenor.com/view/where-are-you-chick-searching-looking-gif-14978088',
            )
        except BadRequest as err:
            query.message.reply_text('Ищем отели')
            print('Ошибка. Не найден файл по URL', err)
            my_logger.warning('Ошибка. Не найден файл по URL {}'.format(err))

    @staticmethod
    def _request_hotel(request_data: dict, hotel_handler) -> list:
        """
        Формирование аргументов для запроса и получение списка отелей.
        :param request_data: словарь с данными, полученными от пользователя,
        :param hotel_handler: модуль для запроса отелей.
        :return: список найденных отелей с данными
        """
        param_request = request_data.copy()
        command = param_request.pop('command')
        city = param_request.pop('query')
        count_hotels = param_request.pop('count_hotel')
        count_photo = param_request.pop('count_photo')

        hotels = hotel_handler.handler(command, city, count_hotels, count_photo, **param_request)
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

        if photo_url[0] == 'нет фото':
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
            query.message.reply_media_group(media=photo_group)

    @staticmethod
    def _add_request_db(user_id, request_data, hotels):
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

    def _valid_hotels(self, query, user_id, request_data):
        """
        Запрос отелей и отправка сообщений пользователю в случае ошибки, в случае успеха - запись в БД.
        :param query: callback_query,
        :param user_id: уникальный id пользователя,
        :param request_data: словарь с данными запроса пользователя,
        :return: обработанный список отелей от rapid
        """
        hotel_handler = RapidFacade()
        hotels = []

        try:
            hotels = self._request_hotel(request_data, hotel_handler)
        except NameError as err:
            my_logger.exception('Ошибка в запросе {}'.format(err))
            query.message.reply_text('Ошибка запроса. Попробуйте позднее.')
        except ValueError as err:
            print('Ошибка - отели не найдены {}'.format(err))
            my_logger.exception('Ошибка - отели не найдены {}'.format(err))
            if 'Город не найден' in err.args:
                query.message.reply_text(str(err))
            else:
                query.message.reply_text('По вашему запросу не найдено отелей')
        else:
            self._add_request_db(user_id, request_data, hotels)
        finally:
            query.bot.delete_message(chat_id=query.message.chat_id, message_id=(query.message.message_id + 1))

        return hotels

    def __call__(self, update: Update, context: CallbackContext) -> int:
        """ Обрабатывает ответ на вопрос о поиске ответа и отправляет список отелей """
        query = update.callback_query
        user_id = query.from_user.id
        answer = query.data

        request_data = super().registry.get_data(user_id).copy()
        super().registry.delete_data(user_id)

        count_photo = request_data.get('count_photo')
        query.delete_message()

        if answer == '1':
            self._send_msg_waiting(query)
            hotels = self._valid_hotels(query, user_id, request_data)

            for hotel in hotels:
                send_msg = self._data_hotel_for_msg(hotel)
                query.message.reply_text(send_msg, disable_web_page_preview=True, parse_mode='HTML')

                if count_photo:
                    self._send_photo(query, hotel)
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
        # 'search': SearchHandler,  # - без прямого запроса на рапид, заглушка для телеграмма
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
        update.message.bot.delete_message(chat_id=update.message.chat_id,
                                          message_id=(update.message.message_id - 1))
        update.message.reply_text('Отмена')
        return ConversationHandler.END
