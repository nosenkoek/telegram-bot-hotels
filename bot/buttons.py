from abc import ABC, abstractmethod
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

BUTTON_NO_PHOTO = {'Без фото': 0}


class Button(ABC):
    def __init__(self, *args):
        self._buttons = args

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
        buttons_line_2 = [InlineKeyboardButton(key, callback_data=value) for key, value in BUTTON_NO_PHOTO.items()]
        markup = InlineKeyboardMarkup([buttons_line_1, buttons_line_2])
        return markup
