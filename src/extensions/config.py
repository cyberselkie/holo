import arc
import hikari
import miru

import boto3
from botocore.exceptions import ClientError


from src.func.files import *
from src.func.gitauth import *

# For more info on plugins & extensions, see: https://arc.hypergonial.com/guides/plugins_extensions/

plugin = arc.GatewayPlugin("config")


@plugin.include
@arc.slash_command("config", "Set up a repository to pre-fill for the /post and save message commands.")
async def config(ctx: arc.GatewayContext, client: miru.Client = arc.inject()) -> None:
    uid = str(ctx.user.id)
    if auth_check(uid):
        code_refresh(uid)
        modal = Config()

        gh_username = miru.TextInput(
            label="Username", custom_id="gh_username", placeholder="cyberselkie", required=True
        )
        repository = miru.TextInput(
            label="Repository", custom_id="repository", placeholder="holo", required=False
        )
        gh_branch = miru.TextInput(label="Branch", custom_id="gh_branch", placeholder="main", required=False)
        filepath = miru.TextInput(label="Filepath", custom_id="filepath", placeholder="file/path/here", required=False)
        post_title = miru.TextInput(label="Title", custom_id="post_title", placeholder="MyNote", required=False)

        modal.add_item(gh_username)
        modal.add_item(repository)
        modal.add_item(gh_branch)
        modal.add_item(filepath)
        modal.add_item(post_title)

        builder = modal.build_response(client)
        await ctx.respond_with_builder(builder)
        client.start_modal(modal)
    else:
        await ctx.respond("Use the /start command!", flags=hikari.MessageFlag.EPHEMERAL)


class Config(miru.Modal, title="Configure default values."):
    # The callback function is called after the user hits 'Submit'
    async def callback(self, ctx: miru.ModalContext) -> None:
        # You can also access the values using ctx.values,
        # Modal.values, or use ctx.get_value_by_id()
        uid = str(ctx.author.id)

        branch = str(ctx.get_value_by_id("gh_branch"))
        fp = str(ctx.get_value_by_id("filepath"))
        gh_user = str(ctx.get_value_by_id("gh_username"))
        repo = str(ctx.get_value_by_id("repository"))
        title =  str(ctx.get_value_by_id("post_title"))

        dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
        table = dynamodb.Table("hologarden-config")  # type: ignore
        if config_check(uid):
            try:
                table.update_item(
                    Key={"userID": str(uid)},
                    UpdateExpression="set branch=:branch",
                    ExpressionAttributeValues={":branch": branch},
                    ReturnValues="UPDATED_NEW",
                )
                table.update_item(
                    Key={"userID": str(uid)},
                    UpdateExpression="set filepath=:filepath",
                    ExpressionAttributeValues={":filepath": fp},
                    ReturnValues="UPDATED_NEW",
                )
                table.update_item(
                    Key={"userID": str(uid)},
                    UpdateExpression="set gh_username=:gh_username",
                    ExpressionAttributeValues={":gh_username": gh_user},
                    ReturnValues="UPDATED_NEW",
                )
                table.update_item(
                    Key={"userID": str(uid)},
                    UpdateExpression="set repository=:repository",
                    ExpressionAttributeValues={":repository": repo},
                    ReturnValues="UPDATED_NEW",
                )
                table.update_item(
                    Key={"userID": str(uid)},
                    UpdateExpression="set title=:title",
                    ExpressionAttributeValues={":title": title},
                    ReturnValues="UPDATED_NEW",
                )
            except ClientError as e:
                print(e)
        else:
            response = table.put_item(
                Item={"userID": str(uid),
                    "branch": branch,
                    "filepath": fp,
                    "gh_username": gh_user,
                    "repository": repo,
                    "title": title}
            )
            print(response)
        print("Successfully saved config.")
        await ctx.respond(
                    f"Config saved.\nRepository:{repo}/{gh_user}\nBranch:{branch}\nFilepath:{fp}/{title}\nRun this command again to change your config.",
                    flags=hikari.MessageFlag.EPHEMERAL,
                )


@arc.loader
def load(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)


@arc.unloader
def unload(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
