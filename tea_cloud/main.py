# --- Imports ------------------------------------------------------------------------ #

import re
from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from typing import Final, TypeGuard

import numpy
from discord import TextChannel
from discord.abc import GuildChannel
from discord.client import Client
from discord.ext.commands import Bot, Context
from discord.file import File
from discord.flags import Intents
from dotenv import load_dotenv
from PIL import Image
from wordcloud import STOPWORDS, ImageColorGenerator, WordCloud

# --- Constants ---------------------------------------------------------------------- #

# Load environment variables.
load_dotenv()

# Main flow.
LOGGER: Final = getLogger("discord")
BOT_TOKEN: Final = getenv("BOT_TOKEN", "")
URL_PATTERN: Final = re.compile(r"https?://\S+|www\.\S+")


# Stopwords.
ALPHABET_STOPWORDS: Final = {chr(i) for i in range(ord("a"), ord("z") + 1)}
TOP_100_COMMON_WORDS: Final = {
    "the",
    "be",
    "to",
    "of",
    "and",
    "a",
    "in",
    "that",
    "have",
    "I",
    "it",
    "for",
    "not",
    "on",
    "with",
    "he",
    "as",
    "you",
    "do",
    "at",
    "this",
    "but",
    "his",
    "by",
    "from",
    "they",
    "we",
    "say",
    "her",
    "she",
    "or",
    "an",
    "will",
    "my",
    "one",
    "all",
    "would",
    "there",
    "their",
    "what",
    "so",
    "up",
    "out",
    "if",
    "about",
    "who",
    "get",
    "which",
    "go",
    "me",
    "when",
    "make",
    "can",
    "like",
    "time",
    "no",
    "just",
    "him",
    "know",
    "take",
    "people",
    "into",
    "year",
    "your",
    "good",
    "some",
    "could",
    "them",
    "see",
    "other",
    "than",
    "then",
    "now",
    "look",
    "only",
    "come",
    "its",
    "over",
    "think",
    "also",
    "back",
    "after",
    "use",
    "two",
    "how",
    "our",
    "work",
    "first",
    "well",
    "way",
    "even",
    "new",
    "want",
    "because",
    "any",
    "these",
    "give",
    "day",
    "most",
    "us",
}
CUSTOM_DOUGCORD_COMMON_WORDS: Final = {
    "one",
    "people",
    "think",
    "lol",
    "thing",
    "will",
    "actually",
    "https",
    "oh",
    "much",
    "going",
    "yeah",
    "ok",
    "wait",
    "really",
}
ALL_STOPWORDS: Final = (
    STOPWORDS | ALPHABET_STOPWORDS | TOP_100_COMMON_WORDS | CUSTOM_DOUGCORD_COMMON_WORDS
)

# --- Helpers ------------------------------------------------------------------------ #


def is_text_channel(channel: GuildChannel) -> TypeGuard[TextChannel]:
    return isinstance(channel, TextChannel)


def get_text_channels(client: Client) -> set[TextChannel]:
    channels = set[TextChannel]()
    for channel in client.get_all_channels():
        if is_text_channel(channel):
            channels.add(channel)
    return channels


# --- Set-up Client ------------------------------------------------------------------ #

intents = Intents.default()
intents.message_content = True

bot = Bot("/", intents=intents)

# --- Handlers ----------------------------------------------------------------------- #


@bot.command()
async def wordcloud(ctx: Context) -> None:
    LOGGER.info("Collecting messages...")

    twenty_four_hours_ago: Final = datetime.today() - timedelta(days=1)
    output_file = f"{twenty_four_hours_ago}.png"

    channels = get_text_channels(bot)

    text = " ".join(
        [
            message.content
            for channel in channels
            async for message in channel.history(after=twenty_four_hours_ago)
        ]
    )
    text = URL_PATTERN.sub("", text)

    LOGGER.info("Generating word cloud...")
    doug_mask = numpy.array(Image.open("doug_mask.png"))
    WordCloud(
        background_color="white",
        mask=doug_mask,
        color_func=ImageColorGenerator(doug_mask),
        stopwords=ALL_STOPWORDS,
    ).generate(text).to_file(output_file)
    LOGGER.info("Word cloud generated...")

    for channel in channels:
        if channel.name == "tech":
            await channel.send(
                f"Here's the Dougcord Tea Cloud since {twenty_four_hours_ago}.",
                file=File(output_file),
            )


# --- Main --------------------------------------------------------------------------- #

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
