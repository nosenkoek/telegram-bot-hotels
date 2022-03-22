from abc import ABC, abstractmethod
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from bot.bot import TelebotHandler
from db.db_handler import DatabaseFactory

""" Бот: @guinea_pig_2022_bot """


TOKEN = '5113338503:AAFtsZUu5UYQGTFl2PC6SfpoTbrsrGNa6EY'



class AbstractFactory(ABC):
    """ Абстрактная фабрика для сбора слоев приложения"""
    @abstractmethod
    def create_telebot(self):
        pass

    # @abstractmethod
    # def create_database(self):
    #     pass


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

        for commands, commands_obj in self.handler.COMMANDS.items():
            if commands in ['lowprice', 'highprice']:
                dispatcher.add_handler(ConversationHandler(
                    entry_points=[CommandHandler(commands, commands_obj())],
                    states={
                        commands_obj.CITY: [MessageHandler(Filters.text, commands_obj.city)],
                        commands_obj.CHECKIN: [MessageHandler(Filters.text, commands_obj.check_in)]
                    },
                    fallbacks=[CommandHandler(commands, commands_obj.cancel)]
                ))
            else:
                dispatcher.add_handler(CommandHandler(commands, commands_obj()))


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
