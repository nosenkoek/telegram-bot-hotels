from settings import BASE_REQUEST_HOTELS_API, BASE_REQUEST_LOCATION_API, HEADERS, COUNT_MAX_PHOTO, COUNT_MAX_HOTEL
from rapid.func_search import search_substruct

from abc import ABC, abstractmethod
import requests
from json import loads, dumps, dump, load, JSONDecodeError
from typing import List, Dict, Any
from logger.logger import LoggerMixin


class BodyRequestHotel(ABC, LoggerMixin):
    REQUEST = {}

    def request_hotel(self, **kwargs) -> requests.Response:
        self.REQUEST.update(BASE_REQUEST_HOTELS_API)
        self.REQUEST.update(**kwargs)
        self.logger().info('request{}'.format(self.REQUEST))
        print(self.REQUEST)
        try:
            response = requests.get('https://hotels4.p.rapidapi.com/properties/list',
                                    headers=HEADERS, params=self.REQUEST)
        except requests.HTTPError as http_err:
            print('Ошибка HTTP:', http_err)
            self.logger().exception(http_err)
            raise
        except Exception as err:
            print('Произошла ошибка:', err)
            self.logger().exception(err)
            raise
        else:
            if response.status_code != 200:
                self.logger().error('code {}'.format(response.status_code))
                raise ValueError('Ошибка кода отклика')

            print('Success Hotels', response.status_code)
            self.logger().info('Success Hotels {}'.format(response.status_code))
            return response


class LowPriceRequestHotel(BodyRequestHotel):
    REQUEST = {'sortOrder': 'PRICE'}


class HighPriceRequestHotel(BodyRequestHotel):
    REQUEST = {'sortOrder': 'PRICE_HIGHEST_FIRST'}


class BestDealRequestHotel(BodyRequestHotel):
    REQUEST = {'sortOrder': 'DISTANCE_FROM_LANDMARK'}


class BaseRequest(ABC, LoggerMixin):
    @abstractmethod
    def context_request(self, *args, **kwargs):
        pass


class HotelRequest(BaseRequest):
    COMMANDS = {
        'bestdeal': BestDealRequestHotel(),
        'lowprice': LowPriceRequestHotel(),
        'highprice': HighPriceRequestHotel(),
    }

    def context_request(self, command: str, **kwargs) -> requests.Response:
        result = self.COMMANDS.get(command)
        return result.request_hotel(**kwargs)


class LocationRequest(BaseRequest):
    REQUEST = BASE_REQUEST_LOCATION_API

    def context_request(self, **kwargs) -> requests.Response:
        self.REQUEST.update(**kwargs)
        try:
            response = requests.get('https://hotels4.p.rapidapi.com/locations/v2/search',
                                    headers=HEADERS, params=self.REQUEST)
        except requests.HTTPError as http_err:
            print('Ошибка HTTP:', http_err)
            self.logger().exception(http_err)
            raise
        except Exception as err:
            print('Произошла ошибка:', err)
            self.logger().exception(err)
            raise
        else:
            if response.status_code != 200:
                self.logger().error('code {}'.format(response.status_code))
                raise ValueError('Ошибка кода отклика')

            print('Success Location', response.status_code)
            self.logger().info('Success Location {}'.format(response.status_code))
            return response


class PhotoRequest(BaseRequest):
    def context_request(self, **kwargs) -> requests.Response:
        try:
            response = requests.get('https://hotels4.p.rapidapi.com/properties/get-hotel-photos',
                                    headers=HEADERS, params=kwargs)
        except requests.HTTPError as http_err:
            print('Ошибка HTTP:', http_err)
            self.logger().exception(http_err)
            raise
        except Exception as err:
            print('Произошла ошибка:', err)
            self.logger().exception(err)
            raise
        else:
            if response.status_code != 200:
                self.logger().error('code {}'.format(response.status_code))
                raise ValueError('Ошибка кода отклика')

            print('Success Photo', response.status_code)
            self.logger().info('Success Photo {}'.format(response.status_code))
            return response


class HotelHandler(LoggerMixin):
    def __init__(self, request: HotelRequest):
        self._request = request

    def handler(self, command: str, count_hotel=COUNT_MAX_HOTEL, **kwargs) -> List[Dict[str, Any]]:
        data = self._request.context_request(command, **kwargs)

        data = loads(data.text)
        with open('bestdeal.json', 'w', encoding='utf-8') as file:
            dump(data, file, ensure_ascii=False, indent=4)

        hotels = []
        hotels_response = search_substruct(data, 'results')

        for hotel in hotels_response:
            if len(hotels) >= count_hotel:
                break

            landmarks = search_substruct(hotel, 'landmarks')
            for landmark in landmarks:
                if landmark.get('label') in ['Центр города', 'City center']:
                    distance = landmark.get('distance')
                    break
            else:
                distance = None

            hotels.append({
                'id': search_substruct(hotel, 'id'),
                'name': search_substruct(hotel, 'name'),
                'address': search_substruct(hotel, 'streetAddress'),
                'star': search_substruct(hotel, 'starRating'),
                'rating': search_substruct(hotel, 'unformattedRating'),
                'distance': distance,
                'price': search_substruct(hotel, 'exactCurrent')
            })

        self.logger().info('success handle hotels')
        return hotels


class LocationHandler(LoggerMixin):
    def __init__(self, request: LocationRequest):
        self._request = request

    def handler(self, **kwargs) -> int:
        data = self._request.context_request(**kwargs)
        data = loads(data.text)
        suggestions = search_substruct(data, 'entities')

        if not isinstance(suggestions, list):
            self.logger().error('Not entities. Wrong structure')
            raise ValueError('Ошибка в структуре ответа на запрос локации')

        for location in suggestions:
            if location.get('type') == 'CITY':
                self.logger().info('success city = {}'.format(location.get('name')))
                print('success city = {}'.format(location.get('name')))
                return location.get('destinationId')
            else:
                self.logger().error('Not found city')
                raise ValueError('Город не найден')


class PhotoHandler(LoggerMixin):
    def __init__(self, request: PhotoRequest):
        self._request = request

    def handler(self, count_photo=COUNT_MAX_PHOTO, **kwargs) -> List[str]:
        data = self._request.context_request(**kwargs)

        photo = []

        try:
            photo_response = search_substruct(loads(data.text), 'hotelImages')
        except JSONDecodeError:
            self.logger().warning('No photo {}'.format(kwargs))
            print('Нет фото')
            return ['нет фото']

        if not isinstance(photo_response, list):
            self.logger().error('Not hotelImages. Wrong structure')
            raise ValueError('Ошибка в структуре ответа на запроса фото отеля')

        for photo_item in photo_response:
            if len(photo) >= count_photo:
                break

            base_url = photo_item.get('baseUrl')
            sizes = photo_item.get('sizes')
            sorted_sizes = sorted(sizes, key=lambda item: item['type'])
            for size in sorted_sizes:
                if size.get('type') >= 3:
                    size_suffix = size.get('suffix')
                    break
            else:
                size_suffix = sorted_sizes[0]

            url_photo_item = base_url.format(size=size_suffix)
            photo.append(url_photo_item)

        self.logger().info('success photo')
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


