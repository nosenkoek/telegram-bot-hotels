import logging
from functools import wraps
from os import path

# TODO настроить логгер, ошибки должны быть в том числе в терминале
my_path = path.dirname(path.abspath(__file__))
path_log = path.join(my_path, '../logger/logging.log')

logging.basicConfig(filename=path_log,
                    filemode='w',
                    encoding='utf-8',
                    level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S'
                    )

my_logger = logging.getLogger('logger')


terminal_logger = logging.StreamHandler()
terminal_logger.setLevel(logging.WARNING)


file_logger = logging.FileHandler(path_log)

my_logger.addHandler(terminal_logger)
my_logger.addHandler(file_logger)

def logger(func, name):
    @wraps(func)
    def wrapper(*args, **kwargs):
        my_logger.info('{} | {} run'.format(name, func.__qualname__))
        try:
            result = func(*args, **kwargs)
        except TypeError:
            """ для работы со staticmethod """
            args = args[1:]
            result = func(*args, **kwargs)
        except Exception as err:
            my_logger.exception('{} | {} ERROR {}'.format(name, func.__qualname__, err))
        return result
    return wrapper


def logger_all():
    @wraps(logger)
    def decorate(cls):
        for method_name in dir(cls):
            if method_name.startswith('__') is False or method_name == '__call__':
                current_method = getattr(cls, method_name)
                decorate_method = logger(current_method, cls.__name__)
                setattr(cls, method_name, decorate_method)
        return cls
    return decorate

