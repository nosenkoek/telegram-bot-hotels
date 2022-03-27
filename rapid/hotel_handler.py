from rapid.hotel import HotelRequest, LocationRequest, PhotoRequest, HotelHandler, LocationHandler, PhotoHandler
from typing import List
from json import dump
from logger.logger import logger_all
import logging

loc_request = LocationRequest()
hotel_request = HotelRequest()
photo_request = PhotoRequest()


@logger_all()
class RapidFacade():
    """ Внешний класс для работы с модулем. Паттерн Фасад. """
    def __init__(self):
        self.location = LocationHandler(loc_request)
        self.hotels = HotelHandler(hotel_request)
        self.photo = PhotoHandler(photo_request)

    def handler(self, command: str, city: str, count_hotel: int, count_photo: int,  **kwargs) -> List:
        try:
            city_id = self.location.handler(query=city)
        except ValueError:
            print('Город не найден')
            logging.error('City not found')
            # todo добавить ошибку для передачи ее пользователю
            raise

        try:
            hotels_data = self.hotels.handler(count_hotel=count_hotel,
                                              command=command,
                                              destinationId=city_id,
                                              **kwargs)
        except ValueError:
            print('Ошибка в поиске отелей')
            logging.exception('Error search hotel')
            # todo добавить ошибку для передачи ее пользователю
            raise

        if count_photo:
            for hotel in hotels_data:
                hotel_id = hotel.get('id')
                try:
                    photo_data = self.photo.handler(count_photo, id=hotel_id)
                except ValueError:
                    print('Фото не найдены')
                    logging.error('Photo not found')
                    # todo добавить ошибку для передачи ее пользователю
                    raise

                hotel.update({'photo': photo_data})

        with open('result.txt', 'w', encoding='utf-8') as file:
            dump(hotels_data, file, ensure_ascii=False, indent=4)

        logging.info('SUCCESS handling hotels')
        return hotels_data


if __name__ == '__main__':
    rapid_handler = RapidFacade()
    # Работа с милями (с eu_US) и км (с ru_RU) Причем правильная стоимость именно в eu_US
    data = rapid_handler.handler('bestdeal', 'Париж', 7, 0,
                                 checkIn='2022-03-27', checkOut='2022-03-30',
                                 priceMin='25000', priceMax='50000', distance=0.2)

    # data = rapid_handler.handler('highprice', 'Мюнхен', 5, 0,
    #                              adults1='3',
    #                              checkIn='2022-03-27', checkOut='2022-03-30')
    print(data)

