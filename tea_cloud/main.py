from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from typing import Final

import discord.client
import discord.flags
from dotenv import load_dotenv
from wordcloud import WordCloud

logger = getLogger("discord")
load_dotenv()
BOT_TOKEN: Final = getenv("BOT_TOKEN", "")
TWENTY_FOUR_HOURS_AGO: Final = datetime.today() - timedelta(days=1)


def get_text_channels(client: discord.client.Client) -> set[discord.TextChannel]:
    channels = set[discord.TextChannel]()
    for channel in client.get_all_channels():
        if isinstance(channel, discord.TextChannel):
            channels.add(channel)
    return channels


intents = discord.flags.Intents.default()
intents.message_content = True

client = discord.client.Client(intents=intents)


@client.event
async def on_ready() -> None:
    logger.info("Collecting messages...")
    text = " ".join(
        [
            message.content
            for channel in get_text_channels(client)
            async for message in channel.history(after=TWENTY_FOUR_HOURS_AGO)
        ]
    )

    logger.info("Generating word cloud...")
    WordCloud().generate(text).to_file("./output.png")
    logger.info("Word cloud generated...")


client.run(BOT_TOKEN)
