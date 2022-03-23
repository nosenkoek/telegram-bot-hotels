from settings import BASE_REQUEST_HOTELS_API, BASE_REQUEST_LOCATION_API, HEADERS, COUNT_MAX_PHOTO, COUNT_MAX_HOTEL
from rapid.func_search import search_substruct

from abc import ABC, abstractmethod
import requests
from json import loads, dumps, dump, load, JSONDecodeError
from typing import List, Dict, Any


class BodyRequestHotel(ABC):
    REQUEST = {}

    def request_hotel(self, **kwargs) -> requests.Response:
        self.REQUEST.update(BASE_REQUEST_HOTELS_API)
        self.REQUEST.update(**kwargs)
        print(self.REQUEST)
        try:
            response = requests.get('https://hotels4.p.rapidapi.com/properties/list',
                                    headers=HEADERS, params=self.REQUEST)
        except requests.HTTPError as http_err:
            print('Ошибка HTTP:', http_err)
            raise
        except Exception as err:
            print('Произошла ошибка:', err)
            raise
        else:
            print('Success')
        return response


class LowPriceRequestHotel(BodyRequestHotel):
    REQUEST = {'sortOrder': 'PRICE'}


class HighPriceRequestHotel(BodyRequestHotel):
    BodyRequestHotel.REQUEST.update({'sortOrder': 'PRICE_HIGHEST_FIRST'})


class BestDealRequestHotel(BodyRequestHotel):
    pass


class BaseRequest(ABC):
    @abstractmethod
    def context_request(self, *args, **kwargs):
        pass


class HotelRequest(BaseRequest):
    COMMANDS = {
        'best_deal': BestDealRequestHotel(),
        'low_price': LowPriceRequestHotel(),
        'high_price': HighPriceRequestHotel(),
    }

    def context_request(self, command: str, **kwargs) -> requests.Response:
        result = self.COMMANDS.get(command)
        print(result)
        print(result.REQUEST)
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
            raise
        except Exception as err:
            print('Произошла ошибка:', err)
            raise
        else:
            print('Success')
        return response


class PhotoRequest(BaseRequest):
    @staticmethod
    def context_request(**kwargs) -> requests.Response:
        try:
            response = requests.get('https://hotels4.p.rapidapi.com/properties/get-hotel-photos',
                                    headers=HEADERS, params=kwargs)
        except requests.HTTPError as http_err:
            print('Ошибка HTTP:', http_err)
            raise
        except Exception as err:
            print('Произошла ошибка:', err)
            raise
        else:
            print('Success')
        return response


class HotelHandler():
    def __init__(self, request: HotelRequest):
        self._request = request

    def handler(self, command: str, count_hotel=COUNT_MAX_HOTEL, **kwargs) -> List[Dict[str, Any]]:
        data = self._request.context_request(command, **kwargs)

        if data.status_code != 200:
            raise ValueError('Ошибка кода отклика')

        data = loads(data.text)
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
        return hotels


class LocationHandler():
    def __init__(self, request: LocationRequest):
        self._request = request

    def handler(self, **kwargs) -> int:
        data = self._request.context_request(**kwargs)

        if data.status_code != 200:
            raise ValueError('Ошибка кода отклика', data.status_code)

        data = loads(data.text)
        print(data)

        suggestions = search_substruct(data, 'entities')

        if not isinstance(suggestions, list):
            raise ValueError('Ошибка в структуре ответа на запрос локации')

        for location in suggestions:
            if location.get('type') == 'CITY':
                print(location.get('name'))
                return location.get('destinationId')
            else:
                raise ValueError('Город не найден')


class PhotoHandler():
    def __init__(self, request: PhotoRequest):
        self._request = request

    def handler(self, count_photo=COUNT_MAX_PHOTO, **kwargs) -> List[str]:
        data = self._request.context_request(**kwargs)

        if data.status_code != 200:
            raise ValueError('Ошибка кода отклика', data.status_code)

        try:
            data_response = loads(data.text)
        except JSONDecodeError:
            print('Нет фото')
            return ['нет фото']

        photo = []
        photo_response = search_substruct(loads(data.text), 'hotelImages')

        if not isinstance(photo_response, list):
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
        return photo


if __name__ == '__main__':
    loc_request = LocationRequest()
    loc_handler = LocationHandler(loc_request)

    data_loc = loc_handler.handler(query='Лондон')
    print(data_loc)
