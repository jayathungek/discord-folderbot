import dill
from typing import Optional, List, Union

from discord.ext.commands.context import Context

import util
import error
import cloudpickle
from store import db
import constansts as cst


class Node:
    name: str
    link: str
    parent: "Node"
    children: List["Node"]

    def __init__(self, name: str, link: Optional[str], parent: Union["Node", None]):
        self.name = name
        self.link = link
        self.parent = parent
        self.children = []
        self.is_last_child = False

    def is_dir(self) -> bool:
        return self.link is None

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def get_full_path(self) -> str:
        path = [self.name]
        p = self.parent
        while p is not None:
            path.insert(0, p.name)
            p = p.parent

        path = "/".join(path)
        path = util.clean_path(path)
        return path

    def get_depth(self) -> int:
        depth = 0
        p = self.parent
        while p is not None:
            depth += 1
            p = p.parent
        return depth


class Tree:
    root: Node
    pwd: Node

    def __init__(self):
        self.root = Node("/", link=None, parent=None)
        self.root.is_last_child = True
        self.pwd = self.root

    def get_node_from_path(self, path: str) -> Node:
        path = util.clean_path(path)
        pathlist = [x for x in path.split("/") if x != ""]
        cur_node = self.root
        for item in pathlist:
            found_child = False
            for child in cur_node.children:
                if item == child.name:
                    cur_node = child
                    found_child = True

            if not found_child:
                raise error.NodeDoesNotExistError(path)

        return cur_node

    def get_abs_path(self, path):
        if not path:
            path = self.get_pwd_path()
        path = util.clean_path(path)
        cur_node = self.pwd
        if path[0] == "/":
            cur_node = self.root
        path_list = path.split("/")
        non_existent_path_list = []
        for name in path_list:
            if name == "..":
                if cur_node.parent is not None:
                    cur_node = cur_node.parent
                else:
                    raise error.CdPreviousFromRootError()
            else:
                next_path = util.clean_path(f"{cur_node.get_full_path()}/{name}")
                try:
                    cur_node = self.get_node_from_path(next_path)
                except error.NodeDoesNotExistError:
                    non_existent_path_list.append(name)

        return f"{cur_node.get_full_path()}/{'/'.join(non_existent_path_list)}"

    def _create_node(self, path: str, name: str, is_file: bool, link: str):
        path = self.get_abs_path(path)
        assert not (is_file ^ (link is not None))
        assert "/" not in name
        assert name != "(empty)"

        link = str(link) if link else None

        node = self.get_node_from_path(path)
        if node.is_dir():
            for child in node.children:
                if name == child.name and is_file ^ child.is_dir():
                    raise error.NodeExistsError(f"{path}/{name}")

            new_node = Node(name, link, parent=node)
            node.children.append(new_node)
            util.ensure_last_child_correct(node.children)
        else:
            raise error.CreateNodeUnderFileError(name, path)

    def create_node(self, path, is_file: bool = False, link: str = None):
        path = util.clean_path(path)
        existing_path = "/".join(path.split("/")[:-1])
        new_dir_name = path.split("/")[-1]
        self._create_node(existing_path, new_dir_name, is_file, link)

    def destroy_node(self, path):
        path = self.get_abs_path(path)
        path = util.clean_path(path)
        node = self.get_node_from_path(path)
        if node is self.root:
            raise error.CannotRmRootError()
        node.parent.children.remove(node)
        util.ensure_last_child_correct(node.parent.children)

    def _traverse(self, node: Node, depth: int, lines: [str]):
        node_details = {
            "node": node,
            "depth": depth,
            "is_empty_dir": node.is_dir() and node.is_leaf(),
            "is_pwd": self.pwd is node,
            "drawing_items": [],  # mandatory pipe, mandatory [extra pipe positions], optional empty suffix
            "children": node.children
        }
        if node.parent is None:  # root node
            lines.append(node_details)
        else:
            if node.is_last_child:
                node_details["drawing_items"].append(cst.PIPE_END)
            else:
                node_details["drawing_items"].append(cst.PIPE_SIDE)

            pipe_positions = util.calculate_prefix(node)
            node_details["drawing_items"].append(pipe_positions)

            if node.is_dir() and node.is_leaf():
                node_details["drawing_items"].append(" *(empty)*")

            lines.append(node_details)

        for i, child in enumerate(node.children):
            self._traverse(child, depth + 1, lines)

        return lines

    def traverse(self) -> [str]:
        lines = self._traverse(self.root, 0, [])
        return lines

    def get_pwd_path(self):
        return self.pwd.get_full_path()

    def change_dir(self, path):
        abs_path = self.get_abs_path(path)
        cur_node = self.get_node_from_path(abs_path)
        if not cur_node.is_dir():
            raise error.CannotCdError(path)

        self.pwd = cur_node


def save_filetree_state(context: Context, ftree: Tree):
    server_id = context.message.guild.id
    try:
        serialized_ftree = dill.dumps(ftree)
        t = dill.loads(serialized_ftree)
        db.set(server_id, serialized_ftree)
    except Exception as err:
        # print(traceback.format_exc())
        pass


def retrieve_filetree_state(context: Context) -> Tree:
    server_id = context.message.guild.id
    serialized_ftree = db.get(server_id)
    if serialized_ftree:
        return dill.loads(serialized_ftree)
    else:
        return Tree()


if __name__ == "__main__":
    t = Tree()
    t.create_node("/test", is_file=False, link=None)
    t.create_node("/test/d1", is_file=False, link=None)
    t.create_node("/test/d1/d2", is_file=False, link=None)
    t.create_node("/test/d1/d2/file.txt", is_file=True, link="abc.com/file.txt")
    t.change_dir("test/d1/d2")
    print(t.root.children[0].children[0].children[0].children[0].name)
    p = cloudpickle.dumps(t)
    t_s = cloudpickle.loads(p)
    print(t_s.root.children[0].children[0].children[0].children[0].name)
