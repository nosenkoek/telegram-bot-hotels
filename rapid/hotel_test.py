from rapid.hotel import RequestHandler
from rapid.location import Location
from rapid.photo import Photo
from typing import List
from json import dump


class RapidFacade():
    def __init__(self):
        self.location = Location()
        self.hotels = RequestHandler()
        self.photo = Photo()

    def handler(self, command: str, city: str, count_photo: int,  **kwargs) -> List:
        city_response = self.location.request_loc(query=city)
        city_id = self.location.get_result(city_response)

        hotels_response = self.hotels.get_request(command=command, destinationId=city_id, **kwargs)
        hotels_data = self.hotels.get_hotels(hotels_response)

        if count_photo:
            for hotel in hotels_data:
                hotel_id = hotel.get('id')

                photo_response = self.photo.request_photo(id=hotel_id)
                photo_data = self.photo.get_result(photo_response, count_photo)

                hotel.update({'photo': photo_data})

        with open('result.txt', 'w', encoding='utf-8') as file:
            dump(hotels_data, file, ensure_ascii=False, indent=4)

        return hotels_data


if __name__ == '__main__':
    rapid_handler = RapidFacade()
    data = rapid_handler.handler('low_price', 'Лондон', 0, checkIn='2022-03-25', checkOut='2022-03-26')
    print(data)

