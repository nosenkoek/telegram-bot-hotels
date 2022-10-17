from bot.command_handler import TelebotHandler
from bot.conversation_handler import SortPriceConversationHandler, \
    BestdealConversationHandler
from logger.logger import logger_all
from settings import TOKEN

from abc import ABC, abstractmethod
from telegram.ext import Updater, CommandHandler, Defaults
from warnings import filterwarnings


""" Бот: @guinea_pig_2022_bot """


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
        self.updater = Updater(token, defaults=Defaults(run_async=True))
        self.handler = TelebotHandler()

        print(self.handler.COMMANDS)

    def add_handlers_commands(self) -> None:
        """ Регистрация обработчиков команд бота """
        dispatcher = self.updater.dispatcher
        # для отключения предупреждения о per_message=False в
        # ConversationHandler
        filterwarnings(action="ignore", message=r".*CallbackQueryHandler")

        for commands, commands_cls in self.handler.COMMANDS.items():
            if commands in ['lowprice', 'highprice']:
                handler_price = SortPriceConversationHandler(commands,
                                                             commands_cls)
                dispatcher.add_handler(handler_price())
            elif commands == 'bestdeal':
                handler_price = BestdealConversationHandler(commands,
                                                            commands_cls)
                dispatcher.add_handler(handler_price())
            else:
                """ Добавление обработки остальных реализованных команд """
                dispatcher.add_handler(CommandHandler(commands,
                                                      commands_cls()))

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
        bot.start()
        return bot
