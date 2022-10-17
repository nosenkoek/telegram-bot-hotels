from settings import KEYS_BESTDEAL, KEYS_SORTPRICE, KEYS_FOR_BUTTON, \
    KEYS_FOR_TEXT_MSG, KEYS_FOR_BUTTON_TEXT_MSG

from bot.hadleres_message import HandlerFactory, Cancel

from telegram.ext import CommandHandler, MessageHandler, Filters, \
    ConversationHandler, CallbackQueryHandler
from abc import ABC

pattern_regex = r'[cC]ancel'
filter_text = (Filters.text & ~Filters.regex(pattern_regex))
handler = HandlerFactory()


class StateBuilder(ABC):
    """ Базовый класс-строитель
    для динамического создания словаря состояния для обработчиков"""
    def __init__(self, command, commands_cls, *args):
        self.keys = args
        self.state = {}
        self.command = command
        self.commands_cls = commands_cls(0)
        self.cancel = Cancel()

    def create_attr(self):
        """
        Добавление всех обработчиков в класс строителя в качестве атрибутов
        """
        for idx_step in range(1, len(self.keys)):
            self.__setattr__(f'_{self.keys[idx_step]}',
                             handler.create_handler(self.keys[idx_step],
                                                    idx_step))

    def command_handler(self):
        """
        Добавление в словарь первого и последнего обработчиков
        """
        self.state.update({
            self.commands_cls.successor:
                [MessageHandler(filter_text,
                                getattr(self, f'_{self.keys[1]}'))],
            getattr(self, '_search').successor:
                [CommandHandler(self.command, self.commands_cls)]
        })

    def msg_handler(self, *args):
        """
        Добавление обработчиков только для текстовых сообщений
        """
        for step in args:
            if step in self.keys:
                idx_step = self.keys.index(step)

                self.state.update({
                    getattr(self, f'_{self.keys[idx_step - 1]}').successor:
                        [MessageHandler(filter_text,
                                        getattr(self, f'_{step}'))]
                })

    def query_handler(self, *args):
        """
        Добавление обработчиков только для кнопок
        """
        for step in args:
            if step in self.keys:
                idx_step = self.keys.index(step)

                self.state.update({
                    getattr(self, f'_{self.keys[idx_step - 1]}').successor: [
                        CallbackQueryHandler(getattr(self, f'_{step}')),
                        MessageHandler(Filters.regex(pattern_regex),
                                       self.cancel)
                    ]
                })

    def msg_query_handler(self, *args):
        """
        Добавление обработчиков для текстовых сообщений и кнопок
        """
        for step in args:
            if step in self.keys:
                idx_step = self.keys.index(step)

                self.state.update({
                    getattr(self, f'_{self.keys[idx_step - 1]}').successor: [
                        MessageHandler(filter_text,
                                       getattr(self, f'_{step}').message),
                        CallbackQueryHandler(getattr(self, f'_{step}'))
                    ]
                })


class ConversationDirector():
    """ Класс-директор для создания обработчика диалога"""
    def __init__(self, builder: StateBuilder):
        self._builder = builder

    def create_conversation_handler(self) -> ConversationHandler:
        """
        Создание обработчика диалога
        :return: ConversationHandler
        """
        self._builder.create_attr()
        self._builder.command_handler()
        self._builder.msg_handler(*KEYS_FOR_TEXT_MSG)
        self._builder.query_handler(*KEYS_FOR_BUTTON)
        self._builder.msg_query_handler(*KEYS_FOR_BUTTON_TEXT_MSG)

        conversation_handler = ConversationHandler(
            entry_points=[CommandHandler(self._builder.command,
                                         self._builder.commands_cls)],
            states=self._builder.state,
            fallbacks=[MessageHandler(Filters.regex(pattern_regex),
                                      self._builder.cancel)]
        )
        return conversation_handler


class SortPriceConversationHandler():
    """ Создание обработчика диалога для lowprice и highprice.
    Внешний интерфейс"""
    def __init__(self, command, commands_cls):
        builder = StateBuilder(command, commands_cls, *KEYS_SORTPRICE)
        self.director = ConversationDirector(builder)

    def __call__(self) -> ConversationHandler:
        conversation_handler = self.director.create_conversation_handler()
        return conversation_handler


class BestdealConversationHandler():
    """ Создание обработчика диалога для bestdeal. Внешний интерфейс"""
    def __init__(self, command, commands_cls):
        builder = StateBuilder(command, commands_cls, *KEYS_BESTDEAL)
        self.director = ConversationDirector(builder)

    def __call__(self) -> ConversationHandler:
        conversation_handler = self.director.create_conversation_handler()
        return conversation_handler
