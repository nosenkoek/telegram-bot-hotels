from datetime import datetime, timedelta
from bot.buttons import ButtonOneLine, ButtonTwoLines

TODAY_DATE = datetime.date(datetime.now())
FORMAT_DATE = '%Y-%m-%d'

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
    'checkIn': datetime.now().strftime(FORMAT_DATE),
    'checkOut': (datetime.now() + timedelta(days=1)).strftime(FORMAT_DATE),
    'adults1': '1',
    'locale': 'en_US',
    'currency': 'RUB',
}

COUNT_MAX_HOTEL = 10

COUNT_MAX_PHOTO = 5

BUTTON_PEOPLE = ButtonOneLine(1, 2, 3, 4)
BUTTON_HOTEL = ButtonOneLine(3, 5, 7)
BUTTON_PHOTO = ButtonTwoLines(1, 2, 3, 4, 5, no_photo=0)

