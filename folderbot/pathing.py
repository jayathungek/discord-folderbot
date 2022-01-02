from dataclasses import dataclass

import util
import error
import constants as cst


def get_required_parent_dirs_for_mk(filetree, abs_path: str) -> [str]:
    cur_filepath = ""
    required_dirs = []
    for i, name in enumerate(abs_path.split("/")):
        cur_filepath += f"/{name}"
        try:
            filetree.get_node_from_path(cur_filepath)
        except error.NodeDoesNotExistError:
            required_dirs.append(util.clean_path(cur_filepath))

    return required_dirs


@dataclass
class Filepaths:
    _paths: [str]
    _target_nodes: []
    _is_mk_cmd: bool

    def __iter__(self):
        to_iterate = self._paths if self._is_mk_cmd else self._target_nodes
        for item in to_iterate:
            yield item

    def __repr__(self) -> str:
        return self._paths[-1]

    def __init__(self, filetree, rel_path: str, is_mk_cmd: bool = False):
        self._target_nodes = []
        self._is_mk_cmd = is_mk_cmd
        self._paths = list(map(util.clean_path, self._build_paths(filetree, util.clean_path(rel_path))))

    def get_target_nodes(self) -> []:
        return self._paths if self._is_mk_cmd else self._target_nodes

    @staticmethod
    def _split_path_list_on_cd_symb(path_list: [str]) -> [[str]]:
        endpoints = []
        cd_count = 0
        in_cd_run = False
        cur_path_segment = []
        path_list = [p for p in path_list if p != ""]
        for name in path_list:
            if in_cd_run:
                cd_count += 1
                if name != cst.PREV_DIR_SYM:
                    cd_count -= 1
                    in_cd_run = False
                    endpoints.append((cur_path_segment, cd_count))
                    cur_path_segment = [name]
                    cd_count = 0
            else:
                if name == cst.PREV_DIR_SYM:
                    cd_count += 1
                    in_cd_run = True
                else:
                    cur_path_segment.append(name)

        endpoints.append((cur_path_segment, cd_count))

        return endpoints

    def _build_paths(self, filetree, path: str) -> [str]:
        path = util.clean_path(path)
        is_relative = False if path[0] == "/" else True
        if is_relative:
            pwd = filetree.get_pwd_path()
            path = util.clean_path(f"{pwd}/{path}")

        path_list = path.split("/")
        endpoints = []
        cur_working_plist = []
        split_path_list = Filepaths._split_path_list_on_cd_symb(path_list)
        final_cd_count = 0
        for plist, cd_count in split_path_list:
            if len(endpoints) == 0:
                endpoints.append(plist)
                cur_working_plist += plist
                if cd_count > len(cur_working_plist):
                    raise error.CdPreviousFromRootError()
                # print(f"plist: {plist}, cwp: {cur_working_plist}, chopping off the last {cd_count} items")
                cur_working_plist = plist[: -cd_count]
            else:
                cur_working_plist += plist
                if cd_count > len(cur_working_plist):
                    raise error.CdPreviousFromRootError()
                # print(f"plist: {plist}, cwp: {cur_working_plist}, chopping off the last {cd_count} items")
                endpoints.append(cur_working_plist)
                cur_working_plist = cur_working_plist[:-cd_count]

            final_cd_count = cd_count

        if final_cd_count > 0:
            endpoints.append(cur_working_plist)

        endpoints_str = []
        endpoints = list(dict.fromkeys([util.clean_path(f"/{'/'.join(plist)}") for plist in endpoints]))
        for full_path in endpoints:
            if not self._is_mk_cmd:
                if cst.ALL_ITEMS_SYM in full_path and full_path[-1] != cst.ALL_ITEMS_SYM:
                    raise error.InvalidFilepathError(path, f"Cannot use {cst.ALL_ITEMS_SYM} "
                                                           f"as a directory name")
                if full_path[-1] == cst.ALL_ITEMS_SYM:
                    node = filetree.get_node_from_path(full_path[:-2])
                    for child in node.children:
                        self._target_nodes.append(child)
                else:
                    node = filetree.get_node_from_path(full_path)
                    self._target_nodes.append(node)
            else:
                if cst.ALL_ITEMS_SYM in full_path:
                    raise error.InvalidFilepathError(path, f"Cannot use {cst.ALL_ITEMS_SYM} "
                                                           f"as a directory name")
            endpoints_str.append(full_path)

        if is_relative and len(self._target_nodes) > 1:
            self._target_nodes = self._target_nodes[1:]
        return endpoints_str


if __name__ == '__main__':  # pragma: no cover
    from tree import Tree

    t = Tree()
    t.create_node("a", is_file=False, link=None)
    t.create_node("a/a1", is_file=False, link=None)
    t.create_node("a/a1/a2", is_file=False, link=None)
    t.create_node("b", is_file=False, link=None)
    # t.change_dir("a/a1/a2")
    # ps = Filepaths(t, "../../../b", is_mk_cmd=False)
    ps = Filepaths(t, "a/a1/a2/../..", is_mk_cmd=False)
    mk = Filepaths._split_path_list_on_cd_symb(["a", "a1", "a2", "..", "a1", "..", ".."])
    print(mk)
    # print(get_required_parent_dirs_for_mk(t, '/a/b/c'))
    # # for p in ps:
    # #     t.create_node(p, is_file=False, link=None)
    # print([n.name for n in ps.get_target_nodes()])
