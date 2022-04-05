class SingletonMeta(type):
    """ Паттерн Одиночка. Создание мета класса"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, *kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Data():
    """ Класс для сбора и хранения данных о запросах пользователя"""
    def __init__(self):
        self._request_data = {}

    def update_data(self, info: dict):
        self._request_data.update(info)

    @property
    def request_data(self):
        return self._request_data


class Registry(metaclass=SingletonMeta):
    """
    Создание Реестра запросов пользователей. Паттерн Registry.
    _datas: dict, словарь id - Data() Каждому id свой экземпляр.
    """
    _datas = {}

    def add_new_id(self, user_id):
        self._datas.update({user_id: Data()})

    def get_data(self, user_id) -> dict:
        try:
            request_data = self._datas[user_id].request_data
        except KeyError:
            print('неверный user_id')
            raise
        else:
            return request_data

    def delete_data(self, user_id):
        try:
            self._datas.pop(user_id)
        except KeyError:
            print('неверный user_id')
            raise

    def update_data(self, user_id, info: dict):
        self._datas[user_id].update_data(info)
