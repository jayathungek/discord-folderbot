from discord import Embed
from discord.ext import commands

import util
import error
from secret import get_discord_token
from tree import Tree, save_filetree_state, retrieve_filetree_state
import constansts as cst


bot = commands.Bot(command_prefix=">>", help_command=None)


async def send_message(context, message: str, msg_type: int, msg_title_override: str = None):
    msg_title = cst.MSG_TITLES[msg_type]
    if msg_title_override:
        msg_title = msg_title_override
    embed = Embed(title=msg_title, description=message, colour=cst.MSG_COLORS[msg_type])
    await context.send(embed=embed)


async def send_help_msg(context, command: str = "folderbot"):
    if command == "folderbot":
        message = "\n\n".join(cst.HELP_STRINGS.values())
    else:
        try:
            message = cst.HELP_STRINGS[command]
        except KeyError:
            err = error.CommandNotFoundError(command)
            await send_message(context, str(err), cst.MSG_ERR, msg_title_override=f"error: help")
            return

    await send_message(context, message, cst.MSG_INFO, msg_title_override=f"help: {command}")


@bot.event
async def on_command_error(ctx, err):
    if isinstance(err, commands.errors.CommandNotFound):
        await send_help_msg(ctx)


@bot.command(name="help")
async def folderbot_help(ctx, command="folderbot"):
    await send_help_msg(ctx, command)


@bot.command(name="rm")
async def remove(ctx, *paths):
    filetree = retrieve_filetree_state(ctx)
    if len(paths) == 0:
        err = error.NoPathsProvidedError("rm")
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: rm")
        return

    fail = []
    dirs_to_rm = []
    for path in paths:
        path = util.clean_path(path)
        full_path = ""
        cd_from_root = False
        path_list = path.split("/")
        for i, _ in enumerate(path_list):
            full_path = f"{filetree.get_pwd_path()}/{'/'.join(path_list[: i + 1])}"
            try:
                full_path = filetree.get_abs_path(full_path)
            except error.CdPreviousFromRootError as err:
                fail.append((err, path))
                cd_from_root = True
                break

            try:
                filetree.get_node_from_path(full_path)
            except error.NodeDoesNotExistError as err:
                fail.append((err, path))
                break

        if cd_from_root:
            err = error.CdPreviousFromRootError()
            fail.append((err, path))
            continue

        dirs_to_rm.append(full_path)

    success, fail = await _rmdirs(filetree, *dirs_to_rm)

    if len(success) > 0:
        message = f"**Removed these items successfully:**\n{cst.NEWLINE.join('* ' + i for i in success)}"
        await send_message(ctx, message, cst.MSG_INFO, msg_title_override="rm")

    if len(fail) > 0:
        message = f"**Failed to remove these items:**" \
                  f"\n{cst.NEWLINE.join('* ' + name + ' -> ' + str(msg) for msg, name in fail)}"
        await send_message(ctx, message, cst.MSG_ERR, msg_title_override="error: rm")

    save_filetree_state(ctx, filetree)


@bot.command(name="mk")
async def mkdirs(ctx, *paths):
    filetree = retrieve_filetree_state(ctx)
    if len(paths) == 0:
        err = error.NoPathsProvidedError("mk")
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: mk")
        return

    success = []
    fail = []
    for path in paths:
        path = util.clean_path(path)
        dirs_to_mk = []
        full_path = ""
        cd_from_root = False
        path_list = path.split("/")
        for i, _ in enumerate(path_list):
            full_path = f"{filetree.get_pwd_path()}/{'/'.join(path_list[: i + 1])}"
            # full_path = util.clean_path(full_path)
            try:
                full_path = filetree.get_abs_path(full_path)
            except error.CdPreviousFromRootError as err:
                fail.append((err, path))
                cd_from_root = True
                break

            try:
                filetree.get_node_from_path(full_path)
            except error.NodeDoesNotExistError:
                dirs_to_mk.append(full_path)
                continue

        if len(dirs_to_mk) == 0 and not cd_from_root:
            err = error.NodeExistsError(full_path)
            fail.append((err, path))
            continue

        s, f = await _mkdirs(filetree, *dirs_to_mk)
        if len(s) > 0:
            success.append(s[-1])

        if len(f) > 0:
            fail.append(f[-1])

    if len(success) > 0:
        message = f"**Created these folders successfully:**\n{cst.NEWLINE.join('* ' + i for i in success)}"
        await send_message(ctx, message, cst.MSG_INFO, msg_title_override="mk")

    if len(fail) > 0:
        message = f"**Failed to create these folders:**" \
                  f"\n{cst.NEWLINE.join('* ' + name + ' -> ' + str(msg) for msg, name in fail)}"
        await send_message(ctx, message, cst.MSG_ERR, msg_title_override="error: mk")

    save_filetree_state(ctx, filetree)


async def _mkdirs(filetree: Tree, *paths):
    success = []
    fail = []
    for path in paths:
        path = util.clean_path(path)
        if path[0] != "/":
            path = util.clean_path(f"{filetree.get_pwd_path()}/{path}")
        try:
            filetree.create_node(path, is_file=False)
            success.append(path)
        except (
            error.NodeDoesNotExistError,
            error.NodeExistsError,
            error.CreateNodeUnderFileError,
        ) as err:
            fail.append((err, path.split("/")[-1]))

    return success, fail


async def _rmdirs(filetree: Tree, *paths):
    success = []
    fail = []
    for path in paths:
        path = util.clean_path(path)
        if path[0] != "/":
            path = util.clean_path(f"{filetree.get_pwd_path()}/{path}")
        try:
            filetree.destroy_node(path)
            success.append(path)
        except (
            error.NodeDoesNotExistError, error.CannotRmRootError
        ) as err:
            if path == "/":
                fail.append((err, path))
            else:
                fail.append((err, path.split("/")[-1]))

    return success, fail


@bot.command(name="tree")
async def tree(ctx):
    filetree = retrieve_filetree_state(ctx)
    traversed_nodes = filetree.traverse()
    message = ""
    for node_details in traversed_nodes:
        node_filename = f"{node_details['node'].name}"
        if node_details["is_pwd"]:
            node_filename = f"__**{node_filename}**__"

        node_str_rep = (
            f"{cst.FOLDER_OPEN} {node_filename}"
            if node_details["node"].is_dir()
            else f"[{node_details['node'].name}]({node_details['node'].link})"
        )

        if node_details["is_empty_dir"]:
            node_str_rep = f"{node_str_rep} *(empty)*"

        if len(node_details["drawing_items"]) > 0:
            mandatory_pipe = node_details["drawing_items"][0]
            pipe_positions = node_details["drawing_items"][1]
            node_str_rep = (
                f"{cst.SPACE * node_details['depth']}{mandatory_pipe} {node_str_rep}"
            )

            for pos in pipe_positions:
                node_str_rep = util.insert(cst.PIPE, pos, node_str_rep)

        message = f"{message}\n{node_str_rep}"

    await send_message(ctx, message, cst.MSG_OK, msg_title_override=f"Current directory: {filetree.get_pwd_path()}")


@bot.command(name="pwd")
async def pwd(ctx):
    filetree = retrieve_filetree_state(ctx)
    message = f"Current directory: {filetree.get_pwd_path()}"
    await send_message(ctx, message, cst.MSG_INFO, msg_title_override="pwd")


@bot.command(name="cd")
async def cd(ctx, directory="/"):
    filetree = retrieve_filetree_state(ctx)
    try:
        filetree.change_dir(directory)
        message = f"Current directory: {filetree.get_pwd_path()}"
        await send_message(ctx, message, cst.MSG_INFO)
    except (
        error.CannotCdError,
        error.CdPreviousFromRootError,
        error.NodeDoesNotExistError,
    ) as err:
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: cd")

    save_filetree_state(ctx, filetree)


@bot.command(name="ls")
async def ls(ctx, directory: str = None, cols=cst.LS_GRID_COLS):
    filetree = retrieve_filetree_state(ctx)
    if directory is None:
        directory = filetree.get_pwd_path()
    try:
        node = filetree.get_node_from_path(directory)
        if not node.is_dir():
            raise error.CannotLsError(directory)

        ls_items = []
        for child in node.children:
            ls_items.append((child.name, child.link, child.is_dir()))
        lines = []
        if len(ls_items) == 0:
            lines.append("*(empty)*")
        for x in range(0, len(ls_items), cols):
            line = ""
            cur_batch = ls_items[x: x + cols]
            for name, link, is_dir in cur_batch:
                if is_dir:
                    line += f"{cst.FOLDER_OPEN}{name}{cst.SPACE}"
                else:
                    line += f"[{name}]({link}){cst.SPACE}"
            lines.append(line)
        ls_str = "\n".join(lines)
        await send_message(ctx, ls_str, cst.MSG_LS, msg_title_override=f"ls: {directory}")
    except (error.NodeDoesNotExistError, error.CannotLsError) as err:
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: ls")


@bot.command(name="up")
async def upload(ctx, directory=None):
    filetree = retrieve_filetree_state(ctx)
    message = ctx.message
    if directory is None:
        directory = filetree.get_pwd_path()
    elif directory[0] != "/":
        directory = filetree.get_abs_path(directory)
        directory = util.clean_path(directory)
    try:
        filetree.get_node_from_path(directory)
    except error.NodeDoesNotExistError as err:
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: up")
        return

    files = message.attachments
    if len(files) == 0 or files is None:
        err = error.NoAttachmentsInMessageError()
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: up")
        return

    success = []
    fail = []
    for file in files:
        filename = str(file).split("/")[-1]
        try:
            filetree.create_node(f"{directory}/{filename}", is_file=True, link=file)
            success.append(f"[{filename}]({file})")
        except (error.NodeExistsError, error.CreateNodeUnderFileError) as err:
            fail.append((err, filename))

    if len(success) > 0:
        message = f"**Uploaded these files successfully to {directory}:**" \
                  f"\n{cst.NEWLINE.join('* ' + i for i in success)}"
        await send_message(ctx, message, cst.MSG_INFO, msg_title_override="up")

    if len(fail) > 0:
        message = f"**Failed to upload these files to {directory}:**" \
                  f"\n{cst.NEWLINE.join('* ' + name + ' -> ' + str(msg) for msg, name in fail)}"
        await send_message(ctx, message, cst.MSG_ERR, msg_title_override="error: up")

    save_filetree_state(ctx, filetree)


bot.run(get_discord_token())
