import os

import arc
import hikari
import miru
from dotenv import load_dotenv

# Welcome to arc!

# Useful links:
# - Documentation: https://arc.hypergonial.com
# - GitHub repository: https://github.com/hypergonial/hikari-arc
# - Discord server to get help: https://discord.gg/hikari

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = hikari.GatewayBot(BOT_TOKEN)  # type: ignore


# Initialize arc with the bot:
arc_client = arc.GatewayClient(
    bot,
    integration_types=[hikari.ApplicationIntegrationType.GUILD_INSTALL, hikari.ApplicationIntegrationType.USER_INSTALL],
)
client = miru.Client.from_arc(arc_client)


# Load the extension from 'src/extensions/example.py'
arc_client.load_extensions_from("src/extensions")


# This must be on the last line, no code will run after this:
bot.run()
