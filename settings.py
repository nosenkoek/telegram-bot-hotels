from datetime import datetime, timedelta


HEADERS = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': "a9aad8794fmsh039fe95526d7dccp1b6e21jsn4ac292303c66"
}

BASE_REQUEST_LOCATION_API = {
    'query': None,
    'locale': 'ru_RU',
    'currency': 'RUB',
}

BASE_REQUEST_HOTELS_API = {
    'destinationId': None,
    'pageNumber': '1',
    'pageSize': '10',
    'checkIn': datetime.now().strftime('%Y-%m-%d'),
    'checkOut': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
    'adults1': '1',
    'locale': 'en_US',
    'currency': 'RUB',
}

COUNT_MAX_HOTEL = 10

COUNT_MAX_PHOTO = 5

STATES_BASE = {
    'city': 0,
    'check_in': 1,
    'check_out': 2,
    'count_people': 3,
    'count_hotel': 4,
    'count_photo': 5
}

