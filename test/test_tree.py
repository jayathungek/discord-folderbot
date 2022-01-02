import os
import sys
import unittest
from types import SimpleNamespace
sys.path.append(os.path.abspath('../folderbot'))

from fakeredis import FakeServer, FakeStrictRedis

# noinspection PyUnresolvedReferences
from tree import Tree, save_filetree_state, retrieve_filetree_state
# noinspection PyUnresolvedReferences
import error
# noinspection PyUnresolvedReferences
from pathing import Filepaths, get_required_parent_dirs_for_mk


class TestCreateNode(unittest.TestCase):
    filetree: Tree

    node_name = "node"

    def setUp(self) -> None:
        self.filetree = Tree()

    def test_create_node(self):
        self.filetree.create_node(f"/{self.node_name}", is_file=False, link=None)
        child_names = [child.name for child in self.filetree.pwd.children]
        self.assertIn(self.node_name, child_names)

    def test_create_node_existent(self):
        self.filetree.create_node(f"/{self.node_name}", is_file=False, link=None)
        with self.assertRaises(error.NodeExistsError):
            self.filetree.create_node(f"/{self.node_name}", is_file=False, link=None)

    def test_create_node_under_file(self):
        self.filetree.create_node(f"/{self.node_name}", is_file=False, link=None)
        self.filetree.create_node(f"/{self.node_name}/{self.node_name}.ext", is_file=True, link="some/link")
        with self.assertRaises(error.CreateNodeUnderFileError):
            self.filetree.create_node(f"/{self.node_name}/{self.node_name}.ext/new_node", is_file=False, link=None)


class TestDestroyNode(unittest.TestCase):
    filetree: Tree

    node_name = "node"

    def setUp(self) -> None:
        self.filetree = Tree()

    def test_destroy_node(self):
        self.filetree.create_node(f"/{self.node_name}")
        self.filetree.destroy_node(f"/{self.node_name}")
        child_names = [child.name for child in self.filetree.pwd.children]
        self.assertNotIn(self.node_name, child_names)

    def test_destroy_node_nonexistent(self):
        with self.assertRaises(error.NodeDoesNotExistError):
            self.filetree.destroy_node(f"/{self.node_name}")

    def test_destroy_node_root(self):
        with self.assertRaises(error.CannotRmRootError):
            self.filetree.destroy_node(f"/")


class TestTreeFunctionality(unittest.TestCase):
    filetree: Tree

    node_name = "node"

    def setUp(self) -> None:
        self.filetree = Tree()
        self.filetree.create_node("/test1", is_file=False, link=None)
        self.filetree.create_node("/test1/d1", is_file=False, link=None)
        self.filetree.create_node("/test1/d1/d2", is_file=False, link=None)
        self.filetree.create_node("/test1/file.txt", is_file=True, link="abc.com/file.txt")
        self.filetree.create_node("/test1/d1/file.txt", is_file=True, link="abc.com/file.txt")
        self.filetree.create_node("/test1/d1/d2/file.txt", is_file=True, link="abc.com/file.txt")
        self.filetree.create_node("/test2", is_file=False, link=None)

    def test_get_node_from_path(self):
        node = self.filetree.get_node_from_path("/test1/file.txt")
        self.assertEqual("file.txt", node.name)

    def test_get_node_from_path_nonexistent(self):
        with self.assertRaises(error.NodeDoesNotExistError):
            self.filetree.get_node_from_path("/test1/d1/non_existent")

    def test_traverse(self):
        traversed_lines = self.filetree.traverse()
        self.assertEqual(8, len(traversed_lines))


class TestFiletreeCd(unittest.TestCase):
    filetree: Tree

    def setUp(self) -> None:
        self.filetree = Tree()
        self.filetree.create_node("/node1", is_file=False, link=None)
        self.filetree.create_node("/node1/node2", is_file=False, link=None)
        self.filetree.create_node("/node1/node2/node3", is_file=False, link=None)
        self.filetree.create_node("/node1/node2/file.ext", is_file=True, link="fake_link")

    def test_cd_absolute(self):
        cd_dir = "/node1/node2/node3"
        self.filetree.change_dir(cd_dir)
        self.assertEqual(cd_dir, self.filetree.get_pwd_path())

    def test_cd_relative(self):
        cd_dir = "node1/node2/../../node1"
        self.filetree.change_dir(cd_dir)
        self.assertEqual("/node1", self.filetree.get_pwd_path())

    def test_cd_relative_trailing(self):
        cd_dir = "node1/node2/../.."
        self.filetree.change_dir(cd_dir)
        self.assertEqual("/", self.filetree.get_pwd_path())

    def test_cd_previous_from_root(self):
        cd_dir = ".."
        with self.assertRaises(error.CdPreviousFromRootError):
            self.filetree.change_dir(cd_dir)

    def test_cd_to_file(self):
        cd_dir = "/node1/node2/file.ext"
        with self.assertRaises(error.CannotCdError):
            self.filetree.change_dir(cd_dir)

    def test_cd_to_nonexistent_node(self):
        cd_dir = "/node1/node2/does_not_exist"
        with self.assertRaises(error.NodeDoesNotExistError):
            self.filetree.change_dir(cd_dir)


class TestFiletreeState(unittest.TestCase):
    filetree: Tree
    redis: FakeStrictRedis
    context: SimpleNamespace

    def setUp(self):
        self.filetree = Tree()
        self.filetree.create_node("/node1", is_file=False, link=None)
        self.filetree.create_node("/node1/node2", is_file=False, link=None)
        self.filetree.create_node("/node1/node2/node3", is_file=False, link=None)
        self.filetree.create_node("/node1/node2/file.ext", is_file=True, link="fake_link")

        self.redis = FakeStrictRedis(server=FakeServer())

        guild = SimpleNamespace(**{"id": "test_id"})
        message = SimpleNamespace(**{"guild": guild})
        self.context = SimpleNamespace(**{
            "message": message
        })

    def test_retrieve_filetree_state_existing(self):
        save_filetree_state(database=self.redis, context=self.context, ftree=self.filetree)
        ret_filetree = retrieve_filetree_state(database=self.redis, context=self.context)
        traversed_nodes = ret_filetree.traverse()
        self.assertEqual(5, len(traversed_nodes))

    def test_retreive_filetree_state_new(self):
        ret_filetree = retrieve_filetree_state(database=self.redis, context=self.context)
        traversed_nodes = ret_filetree.traverse()
        self.assertEqual(1, len(traversed_nodes))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
