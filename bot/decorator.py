class CollectionCommand:
    """ Класс-декоратор для сбора команд в словарь: команда-класс команды"""
    def __init__(self, action: str, actions: dict):
        self.action = action
        self.actions = actions

    def __call__(self, obj):
        self.actions.update({self.action: obj})
        return obj
