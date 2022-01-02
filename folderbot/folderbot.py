from discord import Embed
from discord.ext import commands

import util
import error
import redis
import constants as cst
from pathing import Filepaths, get_required_parent_dirs_for_mk
from secret import get_discord_token, get_redis_url, is_production
from tree import Tree, save_filetree_state, retrieve_filetree_state

bot = commands.Bot(command_prefix=">>", help_command=None)


async def send_message(context, message: str, msg_type: int, msg_title_override: str = None):
    msg_title = cst.MSG_TITLES[msg_type] if is_production() else cst.DEBUG_STR + cst.MSG_TITLES[msg_type]
    if msg_title_override:
        msg_title = msg_title_override if is_production() else cst.DEBUG_STR + msg_title_override
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
    filetree = retrieve_filetree_state(database, ctx)
    if len(paths) == 0:
        err = error.NoPathsProvidedError("rm")
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: rm")
        return

    success = []
    fail = []
    for path in paths:
        try:
            abs_paths = Filepaths(filetree, path)
            target_nodes = abs_paths.get_target_nodes()
            for node in target_nodes:
                full_filepath = node.get_full_path()
                filetree.destroy_node(full_filepath)
                success.append(full_filepath)

        except (error.CdPreviousFromRootError, error.InvalidFilepathError, error.NodeDoesNotExistError) as err:
            fail.append((err, path))

    if len(success) > 0:
        message = f"**Removed these items successfully:**\n{cst.NEWLINE.join(i for i in success)}"
        await send_message(ctx, message, cst.MSG_INFO, msg_title_override="rm")

    if len(fail) > 0:
        message = f"**Failed to remove these items:**" \
                  f"\n{cst.NEWLINE.join(name + ' -> ' + str(msg) for msg, name in fail)}"
        await send_message(ctx, message, cst.MSG_ERR, msg_title_override="error: rm")

    save_filetree_state(database, ctx, filetree)


@bot.command(name="mk")
async def mkdirs(ctx, *paths):
    filetree = retrieve_filetree_state(database, ctx)
    if len(paths) == 0:
        err = error.NoPathsProvidedError("mk")
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: mk")
        return

    success = []
    fail = []
    for path in paths:
        cd_from_root = False
        dirs_to_mk = []
        final_abs_path = ""
        try:
            abs_paths = Filepaths(filetree, path, is_mk_cmd=True)
            abs_paths = abs_paths.get_target_nodes()
            for p in abs_paths:
                final_abs_path = p
                dirs_to_mk += get_required_parent_dirs_for_mk(filetree, p)

        except (error.CdPreviousFromRootError, error.InvalidFilepathError) as err:
            fail.append((err, path))
            if isinstance(err, error.CdPreviousFromRootError):
                cd_from_root = True

        dirs_to_mk = list(set(dirs_to_mk))
        dirs_to_mk = sorted(dirs_to_mk, key=lambda d: len(d.split("/")))
        if len(dirs_to_mk) == 0 and not cd_from_root:
            node_name = path.split("/")[-1]
            err = error.NodeExistsError(final_abs_path)
            fail.append((err, node_name))
            continue

        s, f = await _mkdirs(filetree, *dirs_to_mk)
        if len(s) > 0:
            success += s

        if len(f) > 0:
            fail.append(f[-1])
    if len(success) > 0:
        message = f"**Created these folders successfully:**\n{cst.NEWLINE.join(i for i in success)}"
        await send_message(ctx, message, cst.MSG_INFO, msg_title_override="mk")

    if len(fail) > 0:
        message = f"**Failed to create these folders:**" \
                  f"\n{cst.NEWLINE.join(name + ' -> ' + str(msg) for msg, name in fail)}"
        await send_message(ctx, message, cst.MSG_ERR, msg_title_override="error: mk")

    save_filetree_state(database, ctx, filetree)


async def _mkdirs(filetree: Tree, *paths):
    success = []
    fail = []
    for path in paths:
        path = util.clean_path(path)
        if path[0] != "/":
            path = util.clean_path(f"{filetree.get_pwd_path()}/{path}")
        try:
            filetree.create_node(path, is_file=False)
        except (
                error.NodeDoesNotExistError,
                error.NodeExistsError,
                error.CreateNodeUnderFileError,
        ) as err:
            fail.append((err, path.split("/")[-1]))
        success.append(path)

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
    filetree = retrieve_filetree_state(database, ctx)
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
                node_str_rep = util.replace_substring(cst.PIPE, pos, node_str_rep)

        message = f"{message}\n{node_str_rep}"
    print(len(message))
    # TODO: Discord embeds have a char limit of 6000, how to work around this?
    await send_message(ctx, message, cst.MSG_OK, msg_title_override=f"Current directory: {filetree.get_pwd_path()}")


@bot.command(name="pwd")
async def pwd(ctx):
    filetree = retrieve_filetree_state(database, ctx)
    message = f"Current directory: {filetree.get_pwd_path()}"
    await send_message(ctx, message, cst.MSG_INFO, msg_title_override="pwd")


@bot.command(name="cd")
async def cd(ctx, directory="/"):
    filetree = retrieve_filetree_state(database, ctx)
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

    save_filetree_state(database, ctx, filetree)


@bot.command(name="ls")
async def ls(ctx, directory: str = None, cols=cst.LS_GRID_COLS):
    filetree = retrieve_filetree_state(database, ctx)
    if directory is None:
        directory = filetree.get_pwd_path()
    try:
        abs_paths = Filepaths(filetree, directory)
        node = abs_paths.get_target_nodes()[-1]
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
        await send_message(ctx, ls_str, cst.MSG_LS, msg_title_override=f"ls: {node.get_full_path()}")
    except (error.NodeDoesNotExistError, error.CannotLsError) as err:
        await send_message(ctx, str(err), cst.MSG_ERR, msg_title_override="error: ls")


@bot.command(name="up")
async def upload(ctx, directory=None):
    filetree = retrieve_filetree_state(database, ctx)
    message = ctx.message
    if directory is None:
        directory = filetree.get_pwd_path()
    else:
        try:
            directory = str(Filepaths(filetree, directory))
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
                  f"\n{cst.NEWLINE.join(i for i in success)}"
        await send_message(ctx, message, cst.MSG_INFO, msg_title_override="up")

    if len(fail) > 0:
        message = f"**Failed to upload these files to {directory}:**" \
                  f"\n{cst.NEWLINE.join(name + ' -> ' + str(msg) for msg, name in fail)}"
        await send_message(ctx, message, cst.MSG_ERR, msg_title_override="error: up")

    save_filetree_state(database, ctx, filetree)


if __name__ == '__main__':
    database = redis.from_url(get_redis_url())
    bot.run(get_discord_token())
