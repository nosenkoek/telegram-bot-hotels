from abc import ABC, abstractmethod


class BaseRequest(ABC):
    @abstractmethod
    def context_request(self):
        pass


class HotelRequest(BaseRequest): # класс RequestHandler с фабрикой
    def context_request(self):
        # тут код запроса для отелей
        pass

class LocationRequest(BaseRequest):
    def context_request(self):
        # тут код запроса для отелей
        pass

class PhotoRequest(BaseRequest):
    def context_request(self):
        # тут код запроса для отелей
        pass

class HotelHandler():
    def __init__(self, request: HotelRequest):
        self._request = request

    def handler(self):
        data = self._request.context_request()
        # и далее обработка

# то же для Location и Photo

