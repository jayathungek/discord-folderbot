import re

import constants as cst


def clean_path(path: str) -> str:
    newpath = re.sub(r"/{2,}", "/", path)
    if len(newpath) > 1:
        newpath = newpath[:-1] if newpath[-1] == "/" else newpath
    return newpath


def ensure_last_child_correct(nodes):
    for i, node in enumerate(nodes):
        node.is_last_child = True if i + 1 == len(nodes) else False


def calculate_prefix(node) -> [int]:
    p = node.parent
    postions = []
    while p is not None:
        if not p.is_last_child:
            postions.append(p.get_depth())
        p = p.parent

    return map(lambda x: len(cst.SPACE) * x, postions)


def replace_substring(substring: str, pos: int, main_string: str) -> str:
    return main_string[:pos] + substring + main_string[pos + len(substring):]
