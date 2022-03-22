from settings import HEADERS, COUNT_MAX_PHOTO
import requests
from rapid.func_search import search_substruct
from json import loads, dumps, dump, load, JSONDecodeError
from typing import List, Dict, Any


class Photo():
    @staticmethod
    def request_photo(**kwargs) -> requests.Response:
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

    @staticmethod
    def get_result(data: requests.Response, count_photo=COUNT_MAX_PHOTO):
        if data.status_code != 200:
            raise ValueError('Ошибка кода отклика', data.status_code)

        try:
            data_response = loads(data.text)
        except JSONDecodeError:
            print('Нет фото')
            return ['нет фото']

        photo = []
        count = 0

        with open('photo.json', 'w', encoding='utf-8') as file:
            dump(data_response, file, ensure_ascii=False, indent=4)

        photo_response = search_substruct(loads(data.text), 'hotelImages')

        if not isinstance(photo_response, list):
            raise ValueError('Ошибка в структуре ответа на запроса фото отеля')

        for photo_item in photo_response:
            count += 1

            if count > count_photo:
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


# if __name__ == '__main__':
#     loc = Photo()
#     response = loc.request_photo(id=1968677568)
#     result = loc.get_result(response)
