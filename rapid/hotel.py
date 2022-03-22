from settings import BASE_REQUEST_HOTELS_API, HEADERS
from rapid.func_search import search_substruct

from abc import ABC
import requests
from json import loads, dumps, dump, load
from typing import List, Dict, Any


class RequestBody(ABC):
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


class LowPriceRequest(RequestBody):
    REQUEST = {'sortOrder': 'PRICE'}


class HighPriceRequest(RequestBody):
    RequestBody.REQUEST.update({'sortOrder': 'PRICE_HIGHEST_FIRST'})


class BestDealRequest(RequestBody):
    pass


class RequestHandler():
    COMMANDS = {
        'best_deal': BestDealRequest(),
        'low_price': LowPriceRequest(),
        'high_price': HighPriceRequest(),
    }

    def get_request(self, command: str, **kwargs) -> requests.Response:
        result = self.COMMANDS.get(command)
        print(result)
        print(result.REQUEST)
        return result.request_hotel(**kwargs)

    # TODO подумать куда этот обработчик
    @staticmethod
    def get_hotels(data: requests.Response) -> List[Dict[str, Any]]:
        if data.status_code != 200:
            raise ValueError('Ошибка кода отклика')

        data = loads(data.text)
        with open('hotel_low.json', 'w', encoding='utf-8') as file:
            dump(data, file, ensure_ascii=False, indent=4)

        hotels = []
        hotels_response = search_substruct(data, 'results')

        for hotel in hotels_response:
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
                'miniature': search_substruct(hotel, 'srpDesktop'),
                'star': search_substruct(hotel, 'starRating'),
                'rating': search_substruct(hotel, 'unformattedRating'),
                'distance': distance,
                'price': search_substruct(hotel, 'exactCurrent')
            })
        return hotels




# if __name__ == '__main__':
#     req_handler = RequestHandler()
#     data = req_handler.get_request('low_price',
#                                    destinationId='549499',
#                                    checkIn='2022-03-21', checkOut='2022-03-22',
#                                    adults1='2')
#
#     result = req_handler.get_hotels(data)
#     print(result)


