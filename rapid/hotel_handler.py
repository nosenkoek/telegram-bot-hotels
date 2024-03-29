from rapid.hotel import HotelRequest, LocationRequest, PhotoRequest, \
    HotelHandler, LocationHandler, PhotoHandler
from logger.logger import logger_all

from typing import List
from json import dump
from os import path


@logger_all()
class RapidFacade():
    """ Внешний класс для работы с модулем. Паттерн Фасад. """
    def __init__(self):
        self.loc_request = LocationRequest()
        self.hotel_request = HotelRequest()
        self.photo_request = PhotoRequest()
        self.location = LocationHandler(self.loc_request)
        self.hotels = HotelHandler(self.hotel_request)
        self.photo = PhotoHandler(self.photo_request)

    def handler(self, command: str, city: str, count_hotel: int,
                count_photo: int,  **kwargs) -> List:
        city_id = self.location.handler(query=city)
        if city_id is None:
            raise ValueError('Отель не найден')

        hotels_data = self.hotels.handler(count_hotel=count_hotel,
                                          command=command,
                                          destinationId=city_id,
                                          **kwargs)
        if not hotels_data:
            raise ValueError('Отели не найдены')

        if count_photo:
            for hotel in hotels_data:
                hotel_id = hotel.get('id')
                photo_data = self.photo.handler(count_photo, id=hotel_id)
                if photo_data is None:
                    raise ValueError('Фото не найдены')

                hotel.update({'photo': photo_data})

        abs_path = path.dirname(path.abspath(__file__))
        path_result = path.join(abs_path, '../rapid/result.txt')

        with open(path_result, 'w', encoding='utf-8') as file:
            dump(hotels_data, file, ensure_ascii=False, indent=4)

        return hotels_data
