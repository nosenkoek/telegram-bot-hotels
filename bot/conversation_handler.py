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
        self._cancel = Cancel()

        self._states = {}
        for idx, name_handler in enumerate(self.keys, 1):
            self.__setattr__(f'_{name_handler}', handler.create_handler(name_handler, idx))

            if name_handler == 'city':
                self._states.update({
                    self._commands_cls.successor:
                        [MessageHandler(filter_text, getattr(self, f'_{name_handler}'))]
                })
            elif name_handler in ['prices', 'distance']:
                self._states.update({
                    getattr(self, f'_{self.keys[idx - 2]}').successor:
                        [MessageHandler(filter_text, getattr(self, f'_{name_handler}'))]
                })
            elif name_handler in ['check_in', 'check_out', 'search']:
                self._states.update({
                    getattr(self, f'_{self.keys[idx - 2]}').successor:
                        [CallbackQueryHandler(getattr(self, f'_{name_handler}'))]
                })
            else:
                self._states.update({
                    getattr(self, f'_{self.keys[idx - 2]}').successor: [
                        MessageHandler(filter_text, getattr(self, f'_{name_handler}').message),
                        CallbackQueryHandler(getattr(self, f'_{name_handler}'))
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
        super().__init__(command, commands_cls)
        self.keys.remove('prices'), self.keys.remove('distance'), self.keys.remove('search')

    def __call__(self):
        conversation_handler = ConversationHandler(
            entry_points=[CommandHandler(self._command, self._commands_cls)],
            states=self._states,
            fallbacks=[MessageHandler(Filters.regex('cancel'), self._cancel)]
        )
        return conversation_handler
