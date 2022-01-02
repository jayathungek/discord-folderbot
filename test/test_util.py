import os
import sys
import unittest
sys.path.append(os.path.abspath('../folderbot'))

# noinspection PyUnresolvedReferences
import util
# noinspection PyUnresolvedReferences
from tree import Node, Tree
# noinspection PyUnresolvedReferences
import constants as cst


class TestCleanPath(unittest.TestCase):
    def test_clean_path_absolute(self):
        in_path = "////node1/node2//node3//"
        out_path = util.clean_path(in_path)
        self.assertEqual("/node1/node2/node3", out_path)

    def test_clean_path_relative(self):
        in_path = "//..//node1/node2/../node3//"
        out_path = util.clean_path(in_path)
        self.assertEqual("/../node1/node2/../node3", out_path)

    def test_clean_path_relative_leading_trailing(self):
        in_path = "..//..//node1/node2/../node3//.."
        out_path = util.clean_path(in_path)
        self.assertEqual("../../node1/node2/../node3/..", out_path)


class TestEnsureLastChildCorrect(unittest.TestCase):
    nodes: [Node]

    def setUp(self) -> None:
        self.nodes = []
        for x in range(5):
            new_node = Node(f"node_{x}", link=None, parent=self.nodes[-1] if len(self.nodes) else None)
            self.nodes.append(new_node)

    def test_ensure_last_child_correct(self):
        test_node = Node(f"test_node", link=None, parent=self.nodes[-1])
        self.nodes.append(test_node)
        util.ensure_last_child_correct(self.nodes)

        for i, node in enumerate(self.nodes):
            if i + 1 < len(self.nodes):
                self.assertEqual(False, node.is_last_child)
            else:
                self.assertEqual(True, node.is_last_child)


class TestCalculatePrefix(unittest.TestCase):
    filetree: Tree

    def setUp(self) -> None:
        self.filetree = Tree()
        self.filetree.create_node("/test1", is_file=False, link=None)
        self.filetree.create_node("/test2", is_file=False, link=None)
        self.filetree.create_node("/test1/d1", is_file=False, link=None)
        self.filetree.create_node("/test1/d1/d2", is_file=False, link=None)
        self.filetree.create_node("/test1/file.txt", is_file=True, link="abc.com/file.txt")
        self.filetree.create_node("/test1/d1/file.txt", is_file=True, link="abc.com/file.txt")
        self.filetree.create_node("/test1/d1/d2/file.txt", is_file=True, link="abc.com/file.txt")

    def test_calculate_prefix_top_level(self):
        toplevel_nodes = [
            self.filetree.get_node_from_path(p) for p in [
                f"test{i+1}" for i in range(2)
            ]
        ]

        for node in toplevel_nodes:
            prefix = list(util.calculate_prefix(node))
            self.assertListEqual([], prefix)

    def test_calculate_prefix_nested(self):
        nested_nodes = [
            self.filetree.get_node_from_path("/test1/file.txt"),
            self.filetree.get_node_from_path("/test1/d1/file.txt"),
            self.filetree.get_node_from_path("/test1/d1/d2/file.txt")
        ]

        for i, node in enumerate(nested_nodes):
            prefix = list(util.calculate_prefix(node))
            self.assertEqual(i + 1, len(prefix))


class TestReplaceSubstring(unittest.TestCase):
    test_string: str

    def setUp(self) -> None:
        self.substring = "foo"
        self.main_string = "0123456789"

    def test_replace_substring_front(self):
        new_str = util.replace_substring(self.substring, 0, self.main_string)
        self.assertEqual("foo3456789", new_str)

    def test_replace_substring_middle(self):
        new_str = util.replace_substring(self.substring, 7, self.main_string)
        self.assertEqual("0123456foo", new_str)

    # def test_replace_substring_end(self):
    #     new_str = util.replace_substring(self.substring, 20, self.main_string)
    #     self.assertEqual(self.main_string, new_str)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
