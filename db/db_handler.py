from abc import ABC, abstractmethod
from db.models_db import conn_db, Users
from peewee import IntegrityError
from datetime import datetime

""" Модуль работы с базой данных """


class DatabaseFactory():
    """ Базовый класс для обработки БД (ФМ). Интерфейс CRUD - create, read, update(может быть в будущем)"""
    @staticmethod
    def activate(table_name: str):
        data = {
            'users': DataUsers()
        }
        return data.get(table_name)

    @abstractmethod
    def create(self, *args):
        pass

    @abstractmethod
    def read(self, *args):
        pass


class DataUsers(DatabaseFactory):
    """ Класс для работы с таблицей users"""
    def create(self, user_id: str, user_name: str):
        """
        Функция добавление нового пользователя в БД
        Обрабатывается ошибка уникального user_id.

        :param user_id: id пользователя в Telegram при вызове команды 'start'
        :param user_name: Имя пользователя в Telegram
        """

        with conn_db.atomic():
            try:
                Users.create(
                    user_id=f'{user_id}',
                    user_name=f'{user_name}',
                    data_registration=datetime.now()
                )
            except IntegrityError:
                print('Данный пользователь есть в БД')

    def read(self, user_id: str) -> str:
        # TODO добавить вывод историй запросов (5 строк) если запросов меньше 5 + выводить дату первого сообщения
        """
        Функция печати истории действий пользователя. Сейчас - даты регистрации.

        :param user_id: id пользователя в Telegram передается при вызове команды 'history'
        :return: строка с последними действиями пользователя
        """
        with conn_db.atomic():
            row = Users.get(Users.user_id == user_id)
            result = 'Начало: {}'.format(row.date_registration.strftime('%d.%m.%Y %H:%M'))
        return result
