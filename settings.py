from datetime import datetime, timedelta
from bot.buttons import ButtonOneLine, ButtonTwoLines
from db.db_handler import DatabaseHandler

TOKEN = '5113338503:AAFtsZUu5UYQGTFl2PC6SfpoTbrsrGNa6EY'

TODAY_DATE = datetime.date(datetime.now())
FORMAT_DATE = '%Y-%m-%d'

HEADERS = {
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
        "X-RapidAPI-Key": "8313b0a0bdmshe9cafbcdf42438bp19c8c0jsnbe34dcb1db94"
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

KOEFF_MILES_KM = 1.60934

BUTTON_PEOPLE = ButtonOneLine(1, 2, 3, 4)
BUTTON_HOTEL = ButtonOneLine(3, 5, 7)
BUTTON_PHOTO = ButtonTwoLines(1, 2, 3, 4, 5, no_photo=0)

DATABASE = DatabaseHandler()
