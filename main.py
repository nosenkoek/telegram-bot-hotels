from abc import ABC, abstractmethod

from telegram.ext import Updater, CommandHandler
from bot.bot import TelebotHandler
from bot.conversation_handlers import SortPriceConversationHandler, BestdealConversationHandler
from db.db_handler import DatabaseFactory
from logger.logger import logger_all

""" Бот: @guinea_pig_2022_bot """

TOKEN = '5113338503:AAFtsZUu5UYQGTFl2PC6SfpoTbrsrGNa6EY'


class AbstractFactory(ABC):
    """ Абстрактная фабрика для сбора слоев приложения"""
    @abstractmethod
    def create_telebot(self):
        pass


@logger_all()
class TeleBot():
    """ Класс для инициализации телеграмм команд и запуска бота"""
    def __init__(self, token: str) -> None:
        """ Создается обработчик команд"""
        self.updater = Updater(token)
        self.handler = TelebotHandler()

        print(self.handler.COMMANDS)

    def add_handlers_commands(self) -> None:
        """ Регистрация обработчиков команд бота """
        dispatcher = self.updater.dispatcher
        for commands, commands_cls in self.handler.COMMANDS.items():
            if commands in ['lowprice', 'highprice']:
                """ Добавление функции разговора при запросах 'lowprice', 'highprice' """
                handler_price = SortPriceConversationHandler(commands, commands_cls)
                dispatcher.add_handler(handler_price())
            elif commands == 'bestdeal':
                handler_price = BestdealConversationHandler(commands, commands_cls)
                dispatcher.add_handler(handler_price())
            else:
                """ Добавление обработки остальных реализованных команд """
                dispatcher.add_handler(CommandHandler(commands, commands_cls()))

    def start(self) -> None:
        """ Запуск бота """
        self.updater.start_polling()
        self.updater.idle()


class TeleBotFactory(AbstractFactory):
    """ Непосредственное создание приложения"""
    def create_telebot(self) -> TeleBot:
        """ Создание и запуск Телеграмм-бота"""
        bot = TeleBot(TOKEN)
        bot.add_handlers_commands()
        # bot.add_handlers_message()
        bot.start()
        return bot


if __name__ == '__main__':
    tele_bot = TeleBotFactory()
    tele_bot.create_telebot()

