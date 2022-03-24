import logging
from functools import wraps
from os import path

my_path = path.dirname(path.abspath(__file__))
path_log = path.join(my_path, '../logger/logging.log')

logging.basicConfig(filename=path_log,
                    filemode='w',
                    encoding='utf-8',
                    level=logging.INFO,
                    format='%(asctime)s | %(name)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S'
                    )

# terminal_logger = logging.StreamHandler()
# file_logger = logging.FileHandler(path_log)


# def logger(cls):
#     @wraps(cls)
#     def wrapper(*args, **kwargs):
#         instance = cls(*args, **kwargs)
#         logging.info('{}'.format(cls.__name__))
#         return instance
#     return wrapper

class LoggerMixin():
    def logger(self):
        logger = logging.getLogger(f'{self.__class__.__name__}')
        return logger
