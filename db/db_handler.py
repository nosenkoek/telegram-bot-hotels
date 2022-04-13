from abc import ABC, abstractmethod
from db.models_db import conn_db, Users, UserRequests
from peewee import IntegrityError
from json import loads
from typing import List

""" Модуль работы с базой данных """


class Strategy(ABC):
    """ Интерфейс стратегии """
    @abstractmethod
    def __call__(self, user_id,  table, **kwargs):
        pass


class ReadUsers(Strategy):
    """ Реализация стратегии чтения БД таблицы user_requests"""
    def __call__(self, user_id, table, **kwargs) -> str:
        """
        Чтение БД таблицы users.
        :param table: таблица для чтения,
        :param user_id: уникальный id пользователя,
        :return: сообщение о начале общения с пользователем
        """
        with conn_db.atomic():
            query = table.get(table.user_id == user_id)

        send_msg = 'Начало: {}'.format(query.date_request.strftime('%d.%m.%Y %H:%M'))
        return send_msg


class ReadRequests(Strategy):
    """ Реализация стратегии чтения БД таблицы user_requests"""
    def __call__(self, user_id, table, **kwargs) -> List[str]:
        """
        Чтение БД БД таблицы user_requests.
        :param table: таблица для чтения,
        :param user_id: уникальный id пользователя,
        :return: ModelSelect
        """
        result = []
        with conn_db.atomic():
            query = (table
                     .select()
                     .where(table.user_id == user_id)
                     .order_by(table.id.desc())
                     .limit(5))

        for request in query.order_by(table.id):
            data = [
                '{} - {}'.format(request.date_request.strftime('%d.%m.%Y %H:%M'), request.command_request),
                '<b>{}</b>'.format(request.city_request)
            ]

            for name, url in loads(request.hotels).items():
                data.append('{}\n{}'.format(name, url))

            data = '\n'.join(data)
            result.append(data)
        return result


class Create(Strategy):
    """ Реализация стратегии создания строки БД"""
    def __call__(self, table, user_id, **kwargs) -> None:
        """
        Создание новой строки.
        :param table: таблица БД,
        :param user_id: уникальный id пользователя
        :param kwargs: название колонок и их значения для создания строки.
        """
        with conn_db.atomic():
            try:
                table.create(
                    user_id=user_id,
                    **kwargs
                )
            except IntegrityError as err:
                if 'UNIQUE' in str(err):
                    print('Данный пользователь есть в БД')
                else:
                    print('Ошибка в создании строки БД.', err)


class Database():
    """
    Итоговая модель для работы с БД
    Args:
        strategy: выбор стратегии
    """
    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    def __call__(self, table, user_id, **kwargs):
        """
        Вызов необходимой стратегии.
        :param key_table: ключ для работы с таблицей,
        :param user_id: уникальный id пользователя,
        :param kwargs: название колонок и их значения для создания строки,
        :return: возвращает результат чтения таблицы из БД или None при создании строки.
        """
        result = self.strategy.__call__(
            user_id=user_id,
            table=table,
            **kwargs
        )
        return result


class DatabaseHandler():
    """
    Внешний интерфейс взаимодействия с базой данных
    """
    def __init__(self):
        self._create_strategy = Create()
        self._read_users_strategy = ReadUsers()
        self._read_requests_strategy = ReadRequests()
        self._STRATEGY = {
            0: Database(self._create_strategy),
            1: Database(self._read_users_strategy),
            2: Database(self._read_requests_strategy)
        }
        self._TABLE = {
            'users': Users,
            'user_requests': UserRequests
        }

    def create(self, user_id, key_table, **kwargs) -> None:
        """
        Создание строки в выбранной таблице
        :param user_id: уникальный id пользователя
        :param key_table: ключ выбора таблицы
        :param kwargs: параметры дл создания строки
        """
        self._STRATEGY[0].__call__(user_id=user_id, table=self._TABLE.get(key_table), **kwargs)

    def read_user(self, user_id) -> str:
        """
        Получение данных о пользователе.
        :param user_id: уникальный id пользователя,
        :return: строка о начале работы пользователя с ботом
        """
        result = self._STRATEGY[1].__call__(user_id=user_id, table=self._TABLE.get('users'))
        return result

    def read_requests(self, user_id) -> List[str]:
        """
        Получение 5 последних записей в БД о запросах пользователя.
        :param user_id: уникальный id пользователя,
        :return: список подготовленных сообщений, с временем, командой и городом запроса, а также отелей и их url
        """
        result = self._STRATEGY[2].__call__(user_id=user_id, table=self._TABLE.get('user_requests'))
        return result

