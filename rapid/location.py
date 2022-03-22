from settings import BASE_REQUEST_LOCATION_API, HEADERS
import requests
from rapid.func_search import search_substruct
from json import loads, dumps, dump, load
from typing import List, Dict, Any


class Location():
    REQUEST = BASE_REQUEST_LOCATION_API

    def request_loc(self, **kwargs) -> requests.Response:
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

    @staticmethod
    def get_result(data: requests.Response) -> int:
        if data.status_code != 200:
            raise ValueError('Ошибка кода отклика', data.status_code)

        data = loads(data.text)

        with open('location.json', 'w', encoding='utf-8') as file:
            dump(data, file, ensure_ascii=False, indent=4)

        suggestions = search_substruct(data, 'entities')

        if not isinstance(suggestions, list):
            raise ValueError('Ошибка в структуре ответа на запрос локации')

        for location in suggestions:
            if location.get('type') == 'CITY':
                return location.get('destinationId')
            else:
                raise ValueError('Город не найден')


if __name__ == '__main__':
    loc = Location()
    response = loc.request_loc(query='Лондон')
    result = loc.get_result(response)
    print(result)
