from abc import ABC, abstractmethod
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


class Button(ABC):
    def __init__(self, *args, **kwargs):
        self._buttons = args
        self._two_line = kwargs

    @abstractmethod
    def keyboard(self):
        pass


class ButtonOneLine(Button):
    def keyboard(self):
        buttons = [InlineKeyboardButton(button, callback_data=button) for button in self._buttons]
        markup = InlineKeyboardMarkup([buttons])
        return markup


class ButtonTwoLines(Button):
    def keyboard(self):
        buttons_line_1 = [InlineKeyboardButton(button, callback_data=button) for button in self._buttons]
        buttons_line_2 = [InlineKeyboardButton(name, callback_data=data) for name, data in self._two_line.items()]
        markup = InlineKeyboardMarkup([buttons_line_1, buttons_line_2])
        return markup
