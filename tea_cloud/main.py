# --- Imports ------------------------------------------------------------------------ #

import re
from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from typing import Final

import discord.client
import discord.file
import discord.flags
import numpy
from discord.ext import commands
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
}
ALL_STOPWORDS: Final = (
    STOPWORDS | ALPHABET_STOPWORDS | TOP_100_COMMON_WORDS | CUSTOM_DOUGCORD_COMMON_WORDS
)

# --- Helpers ------------------------------------------------------------------------ #


def get_text_channels(client: discord.client.Client) -> set[discord.TextChannel]:
    channels = set[discord.TextChannel]()
    for channel in client.get_all_channels():
        if isinstance(channel, discord.TextChannel):
            channels.add(channel)
    return channels


# --- Set-up Client ------------------------------------------------------------------ #

intents = discord.flags.Intents.default()
intents.message_content = True

bot = commands.Bot("/", intents=intents)

# --- Handlers ----------------------------------------------------------------------- #


@bot.command()
async def wordcloud(ctx: commands.Context) -> None:
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
                file=discord.file.File(output_file),
            )


# --- Main --------------------------------------------------------------------------- #

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
