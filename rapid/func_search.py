from typing import Dict, List, Optional, Union


# TODO что-то мне не нравится эта прогулка с учетом списка и словаря
#  Может разделить на 2 функции для списка и для словаря?

def search_substruct(struct: Union[Dict, List], key_result: str) -> Optional[List]:
    """ Функция для поиска подструктуры по ключу """
    if isinstance(struct, dict):
        if key_result in struct.keys():
            return struct[key_result]

        values = struct.values()
    else:
        values = struct

    for sub_struct in values:
        if isinstance(sub_struct, dict) or isinstance(sub_struct, list):
            result = search_substruct(sub_struct, key_result)
            if result:
                break
    else:
        result = None
    return result



# def search_substruct(struct: Dict, key_result: str) -> Optional[List]:
#     """ Функция для поиска подструктуры по ключу """
#     if key_result in struct.keys():
#         return struct[key_result]
#
#     for sub_struct in struct.values():
#         if isinstance(sub_struct, dict):
#             result = search_substruct(sub_struct, key_result)
#             if result:
#                 break
#     else:
#         result = None
#     return result
