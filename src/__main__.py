import arc
import boto3
import hikari
import miru

# Welcome to arc!

# Useful links:
# - Documentation: https://arc.hypergonial.com
# - GitHub repository: https://github.com/hypergonial/hikari-arc
# - Discord server to get help: https://discord.gg/hikari

ssm = boto3.client("ssm", region_name="us-east-2")
token = ssm.get_parameter(Name="/hologarden/token", WithDecryption=True)
BOT_TOKEN = token["Parameter"]["Value"]

bot = hikari.GatewayBot(BOT_TOKEN)


# Initialize arc with the bot:
arc_client = arc.GatewayClient(bot)
client = miru.Client.from_arc(arc_client)


# Load the extension from 'src/extensions/example.py'
arc_client.load_extensions_from("src/extensions")


# This must be on the last line, no code will run after this:
bot.run()
