from datetime import datetime, timedelta


HEADERS = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': "8313b0a0bdmshe9cafbcdf42438bp19c8c0jsnbe34dcb1db94"
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
    'locale': 'ru_RU',
    'currency': 'RUB',
}

COUNT_MAX_PHOTO = 5


