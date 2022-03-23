from rapid.hotel import HotelRequest, LocationRequest, PhotoRequest, HotelHandler, LocationHandler, PhotoHandler
from typing import List
from json import dump

loc_request = LocationRequest()
hotel_request = HotelRequest()
photo_request = PhotoRequest()


class RapidFacade():
    def __init__(self):
        self.location = LocationHandler(loc_request)
        self.hotels = HotelHandler(hotel_request)
        self.photo = PhotoHandler(photo_request)

    def handler(self, command: str, city: str, count_hotel: int, count_photo: int,  **kwargs) -> List:
        try:
            city_id = self.location.handler(query=city)
        except ValueError:
            raise ValueError('Город не найден')

        hotels_data = self.hotels.handler(count_hotel=count_hotel, command=command, destinationId=city_id, **kwargs)

        if count_photo:
            for hotel in hotels_data:
                hotel_id = hotel.get('id')
                photo_data = self.photo.handler(count_photo, id=hotel_id)

                hotel.update({'photo': photo_data})

        with open('result.txt', 'w', encoding='utf-8') as file:
            dump(hotels_data, file, ensure_ascii=False, indent=4)

        return hotels_data


if __name__ == '__main__':
    rapid_handler = RapidFacade()
    data = rapid_handler.handler('low_price', 'Лондон', 5, 2, checkIn='2022-03-25', checkOut='2022-03-26')
    print(data)

