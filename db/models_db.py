from peewee import SqliteDatabase, Model, PrimaryKeyField, UUIDField, CharField, DateTimeField, SQL
from datetime import datetime
from os import path

""" Модели для работы с Базой Данных. Построена на базе ORM peewee"""

my_path = path.dirname(path.abspath(__file__))
path_db = path.join(my_path, 'telebot_db.sgl')

conn_db = SqliteDatabase(path_db)


class BaseModel(Model):
    """ Базовая модель для создания БД """
    class Meta:
        database = conn_db
        id = PrimaryKeyField()


class Users(BaseModel):
    """
    Модель таблицы users
    Args:
        user_id - id пользователя в телеграмме
        user_name - Имя пользователя в телеграмме
        date_registration - дата начала общения с ботом
    """
    user_id = CharField(unique=True)
    user_name = CharField(max_length=50)
    date_request = DateTimeField(null=False, default=datetime.now())

    class Meta:
        table_name = 'users'


class UserRequests(BaseModel):
    """
    Модель таблицы user_requests
    Args:
        user_id - id пользователя в телеграмме (внешний ключ к табл. users)
        date_request - дата запроса
        command_request - команда запроса
        city_request - выбранный город
        hotels - список, полученных отелей (словарь name: url)

    """
    user_id = CharField()
    date_request = DateTimeField(null=False, default=datetime.now())
    command_request = CharField(max_length=20)
    city_request = CharField(max_length=50)
    hotels = CharField(max_length=255)

    class Meta:
        table_name = 'user_requests'
        constraints = [SQL('FOREIGN KEY(user_id) REFERENCES users (user_id)')]



