# Message types
MSG_OK = 0x00
MSG_ERR = 0x01
MSG_INFO = 0x10
MSG_LS = 0x11

# Emojis
FOLDER_CLOSED = ":file_folder:"
FOLDER_OPEN = ":open_file_folder:"
PIPE = "┃"
PIPE_SIDE = "┣"
PIPE_END = "┗"
PIP_HORIZ = "━"
SPACE = "⠀⠀"

# Message attributes
DEBUG_STR = "[DEBUG] "
MSG_COLORS = {MSG_OK: 0x55ACEE, MSG_ERR: 0x8F0009, MSG_INFO: 0xC1B927, MSG_LS: 0x55ACEE}
MSG_TITLES = {MSG_OK: "", MSG_ERR: "error", MSG_INFO: "info", MSG_LS: "ls: "}
HELP_STRINGS = {
    "folderbot": "**folderbot** is a pseudo-filesystem for Discord servers that keeps track of attachments in "
                 "directories. It maintains a separate file tree for each server and supports the unix-style commands "
                 "shown below. Relative filepaths are also supported.",
    "tree": "**>>tree**\n"
            "prints the full file tree",
    "pwd": "**>>pwd**\n"
           "shows the __**p**__resent __**w**__orking __**d**__irectory",
    "ls": "**>>ls** [*path*]\n"
          "__**l**__i__**s**__ts the contents of the directory located at *path*. If *path* is not specified, lists "
          "contents of current directory",
    "cd": "**>>cd** [*path*]\n"
          "__**c**__hanges __**d**__irectory to the one specified by *path*. If *path* is not specified, "
          "changes to root directory",
    "mk": "**>>mk** path1 [*path2* *path3* ...]\n"
          "__**m**__a__**k**__es the directories specified by the (space separated) *path*s",
    "rm": "**>>rm** path1 [*path2* *path3* ...]\n"
          "__**r**__e__**m**__oves all the files/directories located at the (space separated) *path*s",
    "up": "**>>up** *path*\n"
          "__**up**__loads the attachments in the message to the directory pointed to by *path*. If *path* is not "
          "specified, attachments are uploaded to the current directory"
}

# Logic
COMMANDS = ["up", "tree", "mk", "rm", "ls", "lsa"]
NEWLINE = "\n"
PREV_DIR_SYM = ".."
CUR_DIR_SYM = "."
ALL_ITEMS_SYM = "*"
LS_GRID_COLS = 4
