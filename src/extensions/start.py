import dbm

import arc
import hikari
import miru

from src.func.files import *
from src.func.gitauth import *

# For more info on plugins & extensions, see: https://arc.hypergonial.com/guides/plugins_extensions/

plugin = arc.GatewayPlugin("start")


class AuthMenu(miru.View):
    # Define a new Button with the Style of success (Green)
    @miru.button(label="Confirm", style=hikari.ButtonStyle.SUCCESS)
    async def confirm_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        print("button pressed")
        uid = str(ctx.user.id)
        db = dbm.open("device_code", "c")
        device_code = db.get(uid).decode()  # type: ignore
        print(f"device code 2 {device_code}")
        r = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"accept": "application/json"},
        )
        json = r.json()
        print(json)
        access_token = json["access_token"]
        refresh_token = json["refresh_token"]
        print("tokens acquired")
        save_auth(refresh_token, access_token, uid)
        await ctx.respond(
            "Your Github account has been connected to this Discord account!", flags=hikari.MessageFlag.EPHEMERAL
        )


@plugin.include
@arc.slash_command("start", "Initiate Github authorization.")
async def start(ctx: arc.GatewayContext, client: miru.Client = arc.inject()) -> None:
    # Create a new instance of our view
    view = AuthMenu()
    uid = str(ctx.user.id)
    device_code, user_code = code_auth()
    # storing the device code so the button can use it
    print(f"device code {device_code}")
    with dbm.open("device_code", "c") as db:
        db[uid] = device_code
    db.close()
    await ctx.respond(
        f"""Enter the code `{user_code}` at <https://github.com/login/device> to allow this bot to upload files on your behalf.
                      No uploads or changes will be made that are not explicitly called by you. Click the button when you've entered the code!""",
        flags=hikari.MessageFlag.EPHEMERAL,
        components=view,
    )
    # Assign the view to the client and start it
    client.start_view(view)


@arc.loader
def load(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)


@arc.unloader
def unload(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
