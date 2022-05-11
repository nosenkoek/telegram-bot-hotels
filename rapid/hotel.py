from settings import BASE_REQUEST_HOTELS_API, BASE_REQUEST_LOCATION_API, HEADERS, \
    KOEFF_MILES_KM, COUNT_MAX_PHOTO, COUNT_MAX_HOTEL

from logger.logger import logger_all, my_logger

from abc import ABC, abstractmethod
import requests
from re import search
from json import loads, dump, JSONDecodeError
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from os import path

import logging


class RequestMixin():
    """ Миксин для запросов по url и параметрам """

    @staticmethod
    def request_get(url: str, request: dict) -> requests.Response:
        """
        Метод запроса
        :param url: url-адрес для запроса,
        :param request: словарь параметров для запроса,
        :return: отклик в виде объекта Response
        """

        response = requests.get(url=url, headers=HEADERS, params=request, timeout=15)

        if response.status_code != 200:
            raise NameError('Ошибка кода отклика', response.status_code)
        return response


class SearchValueMixin():
    """ Миксин для поиска подструктуры по ключу"""

    def _search_substruct(self, struct: Union[Dict, List], key_result: str) -> Union[None, List, str]:
        """ Функция для поиска подструктуры по ключу """
        if isinstance(struct, dict):
            if key_result in struct.keys():
                return struct[key_result]

            values = struct.values()
        else:
            values = struct

        for sub_struct in values:
            if isinstance(sub_struct, dict) or isinstance(sub_struct, list):
                result = self._search_substruct(sub_struct, key_result)
                if result:
                    break
        else:
            result = None
        return result


class BodyRequestHotel(ABC, RequestMixin):
    """ Базовый класс для запросов отелей (Фабричный метод) """
    REQUEST = {}

    def request_hotel(self, **kwargs) -> requests.Response:
        """
        Метод для запроса списка отелей.
        :param kwargs: дополнительные настраиваемые параметры для поиска,
        :return: response
        """
        self.REQUEST.update(BASE_REQUEST_HOTELS_API)
        self.REQUEST.update(**kwargs)

        print(self.REQUEST)
        response = self.request_get('https://hotels4.p.rapidapi.com/properties/list', self.REQUEST)
        print('Success Hotels |', response.status_code)
        return response


@logger_all()
class LowPriceRequestHotel(BodyRequestHotel):
    """ Дочерний класс запроса lowprice"""

    def __init__(self):
        self.REQUEST = {'sortOrder': 'PRICE'}


@logger_all()
class HighPriceRequestHotel(BodyRequestHotel):
    """ Дочерний класс запроса highprice"""

    def __init__(self):
        self.REQUEST = {'sortOrder': 'PRICE_HIGHEST_FIRST'}


@logger_all()
class BestDealRequestHotel(BodyRequestHotel):
    """ Дочерний класс запроса bestdeal. Сортировка по DISTANCE_FROM_LANDMARK"""

    def __init__(self):
        self.REQUEST = {'sortOrder': 'DISTANCE_FROM_LANDMARK'}


class BaseRequest(ABC):
    """ Абстрактный класс для запросов (DIP - принцип инверсии зависимостей) """

    @abstractmethod
    def context_request(self, *args, **kwargs):
        pass


class HotelRequest(BaseRequest):
    """ Фабрика запросов отелей. Изменяется сортировка."""
    COMMANDS = {
        'bestdeal': BestDealRequestHotel(),
        'lowprice': LowPriceRequestHotel(),
        'highprice': HighPriceRequestHotel(),
    }

    def context_request(self, command: str, **kwargs) -> requests.Response:
        result = self.COMMANDS.get(command)
        return result.request_hotel(**kwargs)


@logger_all()
class LocationRequest(BaseRequest, RequestMixin):
    """ Класс запроса локации """

    def __init__(self):
        self.REQUEST = BASE_REQUEST_LOCATION_API

    def context_request(self, **kwargs) -> requests.Response:
        """
        Метод для запроса списка локаций.
        :param kwargs: дополнительный настраиваемый параметр для поиска (query),
        :return: response
        """
        self.REQUEST.update(**kwargs)
        response = self.request_get('https://hotels4.p.rapidapi.com/locations/v2/search', self.REQUEST)
        return response


@logger_all()
class PhotoRequest(BaseRequest, RequestMixin):
    """ Класс запроса фото """

    def context_request(self, **kwargs) -> requests.Response:
        """
        Метод для запроса фото.
        :param kwargs: параметр для поиска фото (id отеля),
        :return: response
        """
        response = self.request_get('https://hotels4.p.rapidapi.com/properties/get-hotel-photos', kwargs)
        print('Success Photo |', response.status_code)
        return response


@logger_all()
class HotelHandler(SearchValueMixin):
    """
    Класс обработчик отелей
    Args:
        request(HotelRequest): экземпляр класса HotelRequest для запроса отелей
    """

    def __init__(self, request: HotelRequest):
        self._request = request

    @staticmethod
    def _count_nights(kwargs) -> int:
        """
        Расчет количества ночей
        :param kwargs: параметры запроса
        :return: количество ночей
        """
        check_in, check_out = kwargs.get('checkIn'), kwargs.get('checkOut')
        check_in, check_out = datetime.strptime(check_in, '%Y-%m-%d'), datetime.strptime(check_out, '%Y-%m-%d')

        count_night = check_out - check_in
        count_night = count_night.days
        return count_night

    def _price(self, hotel: dict, count_night: int) -> (float, float):
        """
        Расчет цены для отелей.
        :param hotel: словарь с параметрами отеля,
        :param count_night: количество ночей,
        :return: цена за 1 ночь и общая цена
        """
        price_one_night = self._search_substruct(hotel, 'exactCurrent')
        total_price = price_one_night * count_night
        return price_one_night, total_price

    def _distance(self, hotel: dict, city: str) -> Optional[float]:
        """
        Поиск удаленности от центра.
        :param hotel: словарь с параметрами отеля,
        :return: удаленность от центра или None при отсутствии этого параметра
        """
        landmarks = self._search_substruct(hotel, 'landmarks')
        landmarks_filter = list(filter(
            lambda item: item.get('label') in ['Центр города', 'City center', city], landmarks)
        )

        if len(landmarks_filter):
            distance = landmarks_filter[0].get('distance')
            dimension = search(r'[a-z]+', distance).group(0)

            distance_hotel = search(r'(\d+[., ]\d*)', distance).group(0)
            distance_float = float(distance_hotel.replace(',', '.'))

            if dimension == 'miles':
                distance_float *= KOEFF_MILES_KM
        else:
            distance_float = None
        return distance_float

    @staticmethod
    def _valid_distance(distance: Optional[float], kwargs) -> bool:
        """
        Проверка отеля по удаленности от центра при команде bestdeal
        :param distance: определенная дистанция
        :param kwargs: параметры для поиска отелей
        :return: True или False подходит/ не подходит
        """
        distance_user = kwargs.get('distance')

        if distance_user < distance:
            return False
        return True

    def handler(self, command: str, count_hotel=COUNT_MAX_HOTEL, **kwargs) -> List[Dict[str, Any]]:
        """
        Обработчик отклика с сайта отелей. Внешний интерфейс.
        :param command: команда по сортировке отеля (bestdeal, highprice, lowprice),
        :param count_hotel: количество отелей введенное пользователем,
        :param kwargs: дополнительные параметры для поиска отеля. обязательно destinationId
        :return hotels: подготовленный список отелей для отправки

        """
        data = self._request.context_request(command, **kwargs)

        if data is None:
            raise TypeError('Ошибка запроса отелей')

        data = loads(data.text)

        abs_path = path.dirname(path.abspath(__file__))
        path_result = path.join(abs_path, '../rapid/hotels.json')

        with open(path_result, 'w', encoding='utf-8') as file_hotel:
            dump(data, file_hotel, ensure_ascii=False, indent=4)

        hotels = []

        hotels_response = self._search_substruct(data, 'results')

        if hotels_response is None:
            return hotels

        hotels_filter = filter(lambda item: self._search_substruct(item, 'exactCurrent'), hotels_response)

        for hotel in hotels_filter:
            if len(hotels) >= count_hotel:
                break

            id_hotel = self._search_substruct(hotel, 'id')
            count_night = self._count_nights(kwargs)
            price, total_price = self._price(hotel, count_night)
            name_city = self._search_substruct(data, 'header')
            name_city = search(r'[^,]+', name_city).group(0)

            distance = self._distance(hotel, name_city)

            if command == 'bestdeal':
                hotel_is_valid = self._valid_distance(distance, kwargs)
            else:
                hotel_is_valid = True

            if hotel_is_valid:
                hotels.append({
                    'id': id_hotel,
                    'name': self._search_substruct(hotel, 'name'),
                    'address': self._search_substruct(hotel, 'streetAddress'),
                    'star': self._search_substruct(hotel, 'starRating'),
                    'rating': self._search_substruct(hotel, 'unformattedRating'),
                    'distance': f'{distance:.1f} км',
                    'price': price,
                    'total_price': total_price,
                    'url': 'https://uk.hotels.com/ho{}'.format(id_hotel)
                })
        return hotels


@logger_all()
class LocationHandler(SearchValueMixin):
    def __init__(self, request: LocationRequest):
        self._request = request

    def handler(self, **kwargs) -> int:
        """
        Обработчик отклика с сайта отелей. Поиск города. Внешний интерфейс.
        :param kwargs: параметр необходимый для поиска города (query),
        :return: id города
        """

        data = self._request.context_request(**kwargs)

        if data is None:
            raise ValueError('Ошибка в запросе')

        data = loads(data.text)
        suggestions = self._search_substruct(data, 'entities')

        if not isinstance(suggestions, list):
            logging.error('Not entities. Wrong structure')
            raise ValueError('Ошибка в структуре ответа на запрос локации')

        for location in suggestions:
            if location.get('type') == 'CITY':
                logging.info('success city = {}'.format(location.get('name')))
                print('success city = {}'.format(location.get('name')))
                return location.get('destinationId')
            else:
                logging.error('Not found city')
                raise ValueError('Город не найден')


@logger_all()
class PhotoHandler(SearchValueMixin):
    def __init__(self, request: PhotoRequest):
        self._request = request

    def handler(self, count_photo=COUNT_MAX_PHOTO, **kwargs) -> Optional[List[str]]:
        """
        Обработчик отклика с сайта отелей. Поиск фото отеля. Внешний интерфейс.
        :param count_photo: число фото, вводимое пользователем,
        :param kwargs: дополнительный параметр для поиска фото (id)
        :return: список с url-адресами фото отеля
        """

        data = self._request.context_request(**kwargs)
        photo = []

        try:
            photo_response = self._search_substruct(loads(data.text), 'hotelImages')
        except JSONDecodeError as err:
            my_logger.exception('Ошибка - фото не найдено {}'.format(err))
            return None

        if not isinstance(photo_response, list):
            raise ValueError('Ошибка в структуре ответа на запроса фото отеля')

        for photo_item in photo_response:
            if len(photo) >= count_photo:
                break

            base_url = photo_item.get('baseUrl')
            sizes = photo_item.get('sizes')
            sorted_sizes = sorted(sizes, key=lambda item: item['type'])
            for size in sorted_sizes:
                if size.get('type') >= 2:
                    size_suffix = size.get('suffix')
                    break
            else:
                size_suffix = sorted_sizes[0]

            url_photo_item = base_url.format(size=size_suffix)
            photo.append(url_photo_item)

        logging.info('success photo')
        return photo


if __name__ == '__main__':
    loc_request = LocationRequest()
    loc_handler = LocationHandler(loc_request)

    city_id = loc_handler.handler(query='Париж')
    print(city_id)

    hotel_request = HotelRequest()
    hotel_handler = HotelHandler(hotel_request)

    data_hotel = hotel_handler.handler(command='bestdeal', count_hotel=10, destinationId=city_id)

    with open('result.txt', 'w', encoding='utf-8') as file:
        dump(data_hotel, file, ensure_ascii=False, indent=4)
