from bot.hadleres_message import HandlerFactory, Cancel
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from abc import ABC, abstractmethod

filter_text = (Filters.text & ~Filters.regex('cancel'))
handler = HandlerFactory()


class CommandConversationHandler(ABC):
    """ Базовый класс для создания обработчика диалога с пользователем """
    keys = [
        'city',
        'check_in',
        'check_out',
        'people',
        'hotel',
        'photo'
    ]

    def __init__(self, command, commands_cls):
        self._command = command
        self._commands_cls = commands_cls(0)

        self._states = {}
        for idx, command in enumerate(self.keys, 1):
            self.__setattr__(f'_{command}', handler.create_handler(command, idx))

            if command in ['city', 'prices', 'distance']:
                self._states.update({
                    idx - 1: [MessageHandler(filter_text, getattr(self, f'_{command}'))]
                })
            elif command in ['check_in', 'check_out']:
                self._states.update({
                    idx - 1: [CallbackQueryHandler(getattr(self, f'_{command}'))]
                })
            else:
                self._states.update({
                    idx - 1: [
                            MessageHandler(filter_text, getattr(self, f'_{command}')),
                            CallbackQueryHandler(getattr(self, f'_{command}'))
                        ]
                })

        self._states.update({
            self.__getattribute__('_search').successor: [CommandHandler(self._command, self._commands_cls)]
        })

    @abstractmethod
    def __call__(self):
        pass


class SortPriceConversationHandler(CommandConversationHandler):
    """ Базовый класс для создания обработчика диалога с пользователем по командам lowprice, highprice"""
    def __init__(self, command, commands_cls):
        self.keys.append('search')
        self._cancel = Cancel()
        super().__init__(command, commands_cls)

        self.keys.remove('search')

    def __call__(self):
        conversation_handler = ConversationHandler(
                    entry_points=[CommandHandler(self._command, self._commands_cls)],
                    states=self._states,
                    fallbacks=[MessageHandler(Filters.regex('cancel'), self._cancel)]
                )
        return conversation_handler


class BestdealConversationHandler(CommandConversationHandler):
    """ Базовый класс для создания обработчика диалога с пользователем по командам bestdeal"""
    def __init__(self, command, commands_cls):
        self.keys.extend(['prices', 'distance', 'search'])
        self._cancel = Cancel()
        super().__init__(command, commands_cls)

        self.keys.remove('prices'), self.keys.remove('distance'), self.keys.remove('search')

    def __call__(self):
        conversation_handler = ConversationHandler(
                    entry_points=[CommandHandler(self._command, self._commands_cls)],
                    states=self._states,
                    fallbacks=[MessageHandler(Filters.regex('cancel'), self._cancel)]
                )
        return conversation_handler
