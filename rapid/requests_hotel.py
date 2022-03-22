from requests import get as get_request
from json import loads, dumps, dump, load
from typing import List, Dict, Any
from rapid.func_search import search_substruct

# TODO отловить ошибки в реквестах (обратить внимание на 'result')

# TODO в запросах локаций есть тип для результатов, если взять "type": "CITY" можно получить id города
#  и в дальнейшем получить удаленность от центра


class Requests():
    response_result = {}

    def get_request(self, url: str, query: Dict[str, Any]) -> None:
        """
        Метод для сохранения ответа на запрос
        :param url: url-адрес для запроса
        :param query: словарь с параметрами запроса
        """
        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': "8313b0a0bdmshe9cafbcdf42438bp19c8c0jsnbe34dcb1db94"
        }

        response = get_request(url, headers=headers, params=query)
        # TODO try except
        print('Был реквест', self.__class__.__name__)
        self.response_result.update(loads(response.text))

        file_name = f'{self.__class__.__name__}.json'

        data_hotel = loads(response.text)
        with open(file_name, 'w', encoding='utf-8') as file:
            dump(data_hotel, file, ensure_ascii=False, indent=4)

    @staticmethod
    def get_result(request_name: str, query: Dict[str, Any]) -> List[Dict[str, str]]:
        requests = {
            'location': Location(),
            'hotel': Hotels(),
            'photo': HotelPhoto()
        }

        urls = {
            'location': 'https://hotels4.p.rapidapi.com/locations/v2/search',
            'hotel': 'https://hotels4.p.rapidapi.com/properties/list',
            'photo': 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
        }

        requests.get(request_name).get_request(urls.get(request_name), query)
        result = requests.get(request_name).result()
        return result


class Location(Requests):
    """ Класс для обработки запроса локации """
    def result(self) -> List[Dict[str, str]]:
        """
        Метод для обработки запроса
        :return locales: - список с названием и id для локаций
        """
        locations = []

        data_response = self.response_result

        # with open('Location.json', 'r', encoding='utf-8') as file:
        #     data_response = load(file)

        suggestions = search_substruct(data_response, 'entities')

        if not isinstance(suggestions, list):
            raise ValueError('Ошибка в структуре ответа на запрос локации')

        for location in suggestions:
            locations.append({
                'destination_id': location.get('destinationId'),
                'name': location.get('name')
            })

        with open('result.txt', 'w', encoding='utf-8') as file:
            file.write('Отклик на запрос локаций:')
            dump(locations, file, ensure_ascii=False, indent=4)
        return locations


class Hotels(Requests):
    """ Класс для обработки запроса отеля """
    def result(self) -> List[Dict[str, str]]:
        """
        Метод для обработки запроса
        :return locales: - список с id отеля, названия отеля, звездности,
                        рейтинга, url миниатюры, удаленности от центра и цены.
        """
        hotels = []

        data_response = self.response_result

        # with open('Hotels.json', 'r', encoding='utf-8') as file:
        #     data_response = load(file)

        hotels_response = search_substruct(data_response, 'results')

        if not isinstance(hotels_response, list):
            raise ValueError('Ошибка в структуре ответа на запрос отелей')

        for hotel in hotels_response:
            # TODO По ТЗ вывод информации об отеле:
            # ● название отеля,
            # ● адрес,
            # ● как далеко расположен от центра,
            # ● цена,
            # ● N фотографий отеля (если пользователь счёл необходимым их вывод)

            hotels.append({
                'id': hotel.get('id'),
                'name': hotel.get('name'),
                'miniature': hotel.get('optimizedThumbUrls').get('srpDesktop'),
                'star': hotel.get('starRating'),
                'rating': hotel.get('guestReviews').get('unformattedRating'),
                'landmarks': hotel.get('landmarks')[0],
                'price': hotel.get('ratePlan').get('price').get('exactCurrent')
            })

        with open('result.txt', 'a', encoding='utf-8') as file:
            file.write('\n\nОтклик на запрос отелей:')
            dump(hotels, file, ensure_ascii=False, indent=4)

        return hotels


class HotelPhoto(Requests):
    """
    Класс для получения фото конкретного отеля
    на входе: id
    на выходе: фото
    """
    """ Класс для обработки запроса отеля """
    def result(self) -> List[Dict[str, str]]:
        """
         Метод для обработки запроса
         :return photo: - список с url-адрессами для отеля
         """
        photo = []
        # TODO перенести в settings
        COUNT_MAX_PHOTO = 5
        count = 0

        data_response = self.response_result

        # with open('HotelPhoto.json', 'r', encoding='utf-8') as file:
        #     data_response = load(file)

        photo_response = search_substruct(data_response, 'hotelImages')

        if not isinstance(photo_response, list):
            raise ValueError('Ошибка в структуре ответа на запроса фото отеля')

        for photo_item in photo_response:
            count += 1

            if count > COUNT_MAX_PHOTO:
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

            # TODO подумать как можно полезно использовать ключ
            photo.append({'url': url_photo_item})

        with open('result.txt', 'a', encoding='utf-8') as file:
            file.write('\n\nОтклик на запрос фото отеля:')
            dump(photo, file, ensure_ascii=False, indent=4)

        return photo


if __name__ == '__main__':
    args_location = {
        'query': 'Лондон',
        'locale': 'ru_RU',
        'currency': 'RUB'
    }

    # TODO продумать кто формирует этот словарь
    args_hotel = {
        'destinationId': '1762415',
        'pageNumber': '1',
        'pageSize': '5',
        'checkIn': '2022-03-18',
        'checkOut': '2022-03-20',
        'adults1': '2',
        'children1': None,
        'sortOrder': 'PRICE', # PRICE_HIGHEST_FIRST, PRICE
        'locale': 'ru_RU',
        'currency': 'RUB',
        'priceMin': None, # для
        'priceMax': None  # best deal
    }

    args_photo = {
        'id': 286143,
    }

    reqs = Requests()
    # hotel_obj = Hotels()
    print('Отработка запроса локации')
    data = reqs.get_result('location', args_location)
    print(data)

    print('Отработка запроса отелей')
    data = reqs.get_result('hotel', args_hotel)
    print(data)

    print('Отработка запроса фото отеля:')
    data = reqs.get_result('photo', args_photo)
    print(data)



    # loc_reg = Location()
    # data = loc_reg.result()
    # print(data)

    # photo_req = HotelPhoto()
    # # data = photo_req.get_result('photo', args_photo)
    # data = photo_req.result()
    # print(data)
