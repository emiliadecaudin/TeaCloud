from collections import Counter
from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from typing import Final

import discord.client
import discord.flags
from dotenv import load_dotenv
from wordcloud import STOPWORDS, WordCloud

logger = getLogger("discord")
load_dotenv()
BOT_TOKEN: Final = getenv("BOT_TOKEN", "")
TWENTY_FOUR_HOURS_AGO: Final = datetime.today() - timedelta(days=1)


def get_words(text: str) -> list[str]:
    return list(filter(lambda x: len(x) > 0, text.replace("\n", " ").split(" ")))


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
    logger.info("Collecting words...")
    words = Counter(
        [
            word
            for channel in get_text_channels(client)
            async for message in channel.history(after=TWENTY_FOUR_HOURS_AGO)
            for word in get_words(message.content)
        ]
    )
    for stopword in STOPWORDS:
        del words[stopword]

    logger.info("Generating word cloud...")
    WordCloud().generate_from_frequencies(words).to_file("./output.png")
    logger.info("Word cloud generated...")


client.run(BOT_TOKEN)
