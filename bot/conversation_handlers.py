from bot.bot import CityHandle, DateHandler, PeopleHandler, HotelCountHandler, \
    PhotoCountHandler, SearchHandler, Cancel
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler, PreCheckoutQueryHandler, ChosenInlineResultHandler

# TODO подумать над базовым классом, возможно фабрика


class SortPriceConversationHandler():
    def __init__(self, command, commands_cls):

        self._command = command
        self._commands_cls = commands_cls(0)
        self._city = CityHandle(1)
        self._check_in = DateHandler(2)
        self._check_out = DateHandler(3)
        self._people = PeopleHandler(4)
        self._hotel = HotelCountHandler(5)
        self._photo = PhotoCountHandler(6)
        self._search = SearchHandler(7)
        self._cancel = Cancel(7)

    # TODO сделать возможность отмены выполнения команды - это под вопросом
    def __call__(self):
        states = {
                        self._commands_cls.successor: [MessageHandler(Filters.text, self._city)],
                        self._city.successor: [CallbackQueryHandler(self._check_in)],
                        self._check_in.successor: [CallbackQueryHandler(self._check_out)],
                        self._check_out.successor: [CallbackQueryHandler(self._people),
                                                    MessageHandler(Filters.text, self._people.message)],
                        self._people.successor: [CallbackQueryHandler(self._hotel),
                                                 MessageHandler(Filters.text, self._hotel.message)],
                        self._hotel.successor: [CallbackQueryHandler(self._photo),
                                                MessageHandler(Filters.text, self._photo.message)],
                        self._photo.successor: [CallbackQueryHandler(self._search)],
                        self._search.successor: [CommandHandler(self._command, self._commands_cls)],
                    }
        handler = ConversationHandler(
                    entry_points=[CommandHandler(self._command, self._commands_cls)],
                    states=states,
                    # todo подумать как можно использовать
                    fallbacks=[CommandHandler('cancel', self._cancel())]
                )
        return handler


class BestdealConversationHandler():
    # TODO доделать
    def __init__(self, command, commands_cls):
        self._command = command
        self._commands_cls = commands_cls(0)
        self._city = CityHandle(1)
        self._check_in = DateHandler(2)
        self._check_out = DateHandler(3)
        self._people = PeopleHandler(4)
        self._hotel = HotelCountHandler(5)
        self._photo = PhotoCountHandler(6)
        self._search = SearchHandler(7)
        self._cancel = Cancel(8)

    def __call__(self):
        handler = ConversationHandler(
                    entry_points=[CommandHandler(self._command, self._commands_cls)],
                    states={
                        self._commands_cls.successor: [MessageHandler(Filters.text, self._city)],
                        self._city.successor: [MessageHandler(Filters.text, self._check_in)],
                        self._check_in.successor: [MessageHandler(Filters.text, self._check_out)],
                        self._check_out.successor: [MessageHandler(Filters.text, self._people)],
                        self._people.successor: [MessageHandler(Filters.text, self._hotel)],
                        self._hotel.successor: [MessageHandler(Filters.text, self._photo)],
                        self._photo.successor: [MessageHandler(Filters.text, self._search)],
                        self._search.successor: [CommandHandler(self._command, self._commands_cls)],
                    },
                    # todo подумать как можно использовать
                    fallbacks=[CommandHandler('cancel', self._cancel())]
                )
        return handler

