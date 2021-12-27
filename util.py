import re

import constansts as cst


def clean_path(path: str) -> str:
    return re.sub(r"/{2,}", "/", path)


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


def insert(substring: str, pos: int, main_string: str) -> str:
    return main_string[:pos] + substring + main_string[pos + len(substring):]
