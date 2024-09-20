from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from typing import Final

import discord.client
import discord.file
import discord.flags
import numpy
from dotenv import load_dotenv
from PIL import Image
from wordcloud import ImageColorGenerator, WordCloud, STOPWORDS

logger = getLogger("discord")
load_dotenv()
BOT_TOKEN: Final = getenv("BOT_TOKEN", "")
TWENTY_FOUR_HOURS_AGO: Final = datetime.today() - timedelta(days=1)

alphabet_stop_words = {chr(i) for i in range(ord('a'), ord('z') + 1)}
top_100_common_words = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I", "it", "for", "not", "on", "with", "he", "as", "you", 
    "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", 
    "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", 
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", 
    "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", 
    "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", "new", 
    "want", "because", "any", "these", "give", "day", "most", "us"
}
custom_dougcord_common_words = {
    "one", "people", "think", "lol", "thing", "will", "actually", "one"
}

all_stop_words = STOPWORDS.union(alphabet_stop_words).union(top_100_common_words).union(custom_dougcord_common_words)

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

    channels = get_text_channels(client)

    text = " ".join(
        [
            message.content
            for channel in channels
            async for message in channel.history(after=TWENTY_FOUR_HOURS_AGO)
        ]
    )

    logger.info("Generating word cloud...")
    doug_mask = numpy.array(Image.open("doug_mask.png"))
    WordCloud(
        background_color="white",
        mask=doug_mask,
        color_func=ImageColorGenerator(doug_mask),
        stopwords=all_stop_words,
    ).generate(text).to_file("output.png")
    logger.info("Word cloud generated...")

    for channel in channels:
        if channel.name == "tech":
            await channel.send(file=discord.file.File("./output.png"))


client.run(BOT_TOKEN)
