import arc
import hikari
import miru

from src.func.files import *
from src.func.gitauth import *

# For more info on plugins & extensions, see: https://arc.hypergonial.com/guides/plugins_extensions/

plugin = arc.GatewayPlugin("post")


@plugin.include
@arc.slash_command("post", "Write a Markdown File")
async def post_slash(ctx: arc.GatewayContext, client: miru.Client = arc.inject()) -> None:
    uid = str(ctx.user.id)
    if auth_check(uid):
        code_refresh(uid)
        modal = Post()

        repository = miru.TextInput(
            label="Username/Repository", custom_id="repository", placeholder="cyberselkie/holo", required=True
        )
        gh_branch = miru.TextInput(label="Branch", custom_id="gh_branch", placeholder="main", required=True)
        filepath = miru.TextInput(label="Filepath", custom_id="filepath", placeholder="file/path/here", required=False)

        post_contents = miru.TextInput(
            label="File Contents",
            custom_id="post_contents",
            placeholder="# This is my header \n\n Isn't this an awesome note?",
            style=hikari.TextInputStyle.PARAGRAPH,
            required=True,
        )
        post_title = miru.TextInput(label="Title", custom_id="post_title", placeholder="MyNote", required=True)

        modal.add_item(repository)
        modal.add_item(gh_branch)
        modal.add_item(filepath)
        modal.add_item(post_title)
        modal.add_item(post_contents)

        builder = modal.build_response(client)
        await ctx.respond_with_builder(builder)
        client.start_modal(modal)
    else:
        await ctx.respond("Use the /start command!", flags=hikari.MessageFlag.EPHEMERAL)


@plugin.include
@arc.slash_command("edit", "Edit a Markdown File")
async def edit_slash(
    ctx: arc.GatewayContext,
    gh_username: arc.Option[str, arc.StrParams(description="Github username.")],
    repo: arc.Option[str, arc.StrParams(description="Github repository.")],
    fp: arc.Option[str, arc.StrParams(description="Filepath in repository, including filename.")],
    branch: arc.Option[str, arc.StrParams(description="Repository branch.")],
    client: miru.Client = arc.inject(),
) -> None:
    uid = str(ctx.user.id)
    if auth_check(uid):
        code_refresh(uid)
        contents = retrieve_contents(uid, gh_username, repo, fp)
        file, filename = download_contents(contents)
        if len(file) > 3000:
            await ctx.respond(
                f"This file has too many characters, sorry! {len(file)} is more than 3000.",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
        else:
            modal = Post()
            repository = miru.TextInput(
                label=f"{gh_username}/{repo}", custom_id="repository", value=f"{gh_username}/{repo}", required=True
            )
            gh_branch = miru.TextInput(label="Branch", custom_id="gh_branch", value=branch, required=True)
            filepath = miru.TextInput(label=fp, custom_id="filepath", value=fp, required=False)
            post_contents = miru.TextInput(
                label="File Contents",
                custom_id="post_contents",
                value=file,
                style=hikari.TextInputStyle.PARAGRAPH,
                required=True,
            )
            post_title = miru.TextInput(label="Title", custom_id="post_title", value=filename, required=True)

            modal.add_item(repository)
            modal.add_item(gh_branch)
            modal.add_item(filepath)
            modal.add_item(post_title)
            modal.add_item(post_contents)

            builder = modal.build_response(client)
            await ctx.respond_with_builder(builder)
            client.start_modal(modal)
    else:
        await ctx.respond("Use the /start command!", flags=hikari.MessageFlag.EPHEMERAL)


@plugin.include
@arc.message_command("Save Message", is_dm_enabled=True)
async def append_msg_command(
    ctx: arc.GatewayContext, message: hikari.Message, client: miru.Client = arc.inject()
) -> None:
    uid = str(ctx.user.id)
    if auth_check(uid):
        code_refresh(uid)

        message_contents = f"{message.author}: {message.content}"
        modal = Post()

        repository = miru.TextInput(
            label="Username/Repository", custom_id="repository", placeholder="cyberselkie/holo", required=True
        )
        gh_branch = miru.TextInput(label="Branch", custom_id="gh_branch", placeholder="main", required=True)
        filepath = miru.TextInput(label="Filepath", custom_id="filepath", placeholder="file/path/here", required=False)

        post_contents = miru.TextInput(
            label="File Contents",
            custom_id="post_contents",
            value=message_contents,
            style=hikari.TextInputStyle.PARAGRAPH,
            required=True,
        )
        post_title = miru.TextInput(label="Title", custom_id="post_title", placeholder="MyNote", required=True)

        modal.add_item(repository)
        modal.add_item(gh_branch)
        modal.add_item(filepath)
        modal.add_item(post_title)
        modal.add_item(post_contents)

        builder = modal.build_response(client)
        await ctx.respond_with_builder(builder)
        client.start_modal(modal)
    else:
        await ctx.respond("Use the /start command!", flags=hikari.MessageFlag.EPHEMERAL)


class Post(miru.Modal, title="Write a Markdown File"):
    # The callback function is called after the user hits 'Submit'
    async def callback(self, ctx: miru.ModalContext) -> None:
        # You can also access the values using ctx.values,
        # Modal.values, or use ctx.get_value_by_id()
        uid = str(ctx.author.id)
        repository = ctx.get_value_by_id("repository")

        x = validate_repo(repository)
        if x is None:
            await ctx.respond("Check your repository field!")
        else:
            auth = auth_login(uid)
            g = Github(auth=auth)
            g.get_user().login

            gh_repo = x[1]
            user = x[0]

            name = remove_punctuation(ctx.get_value_by_id("post_title"))
            post_name = f"{name}.md"
            body = ctx.get_value_by_id("post_contents")

            if ctx.get_value_by_id("filepath") == "":
                fp = post_name
            else:
                fp = f"{ctx.get_value_by_id('filepath')}/{ctx.get_value_by_id('post_title'}"

            repo = g.get_repo(repository)
            contents = retrieve_contents(uid, user, gh_repo, fp)
            if contents:
                file, filename = download_contents(contents)
                body = f"{file}\n{body}"
                repo.update_file(contents.path, "Updated via Discord", body, contents.sha)  # type: ignore
                await ctx.respond(f"File located at <{contents.html_url}> updated.", flags=hikari.MessageFlag.EPHEMERAL)  # type: ignore
            else:
                repo.create_file(path=fp, message=post_name, content=body, branch=ctx.get_value_by_id("gh_branch"))
                print(repo)
                print(f"{post_name} uploaded.")
                await ctx.respond(
                    f"{post_name} uploaded to https://github.com/{user}/{gh_repo}/blob/{ctx.get_value_by_id('gh_branch')}/{fp}.",
                    flags=hikari.MessageFlag.EPHEMERAL,
                )


@arc.loader
def load(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)


@arc.unloader
def unload(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
