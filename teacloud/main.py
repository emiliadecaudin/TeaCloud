# --- Imports ------------------------------------------------------------------------ #

import re
from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from pathlib import Path
from typing import Final, LiteralString

import numpy
from discord.channel import TextChannel
from discord.ext.commands import Bot
from discord.file import File
from discord.flags import Intents
from discord.guild import Guild
from discord.interactions import Interaction
from dotenv import load_dotenv
from PIL import Image
from wordcloud import STOPWORDS, ImageColorGenerator, WordCloud

# --- Constants ---------------------------------------------------------------------- #

# Load environment variables.
load_dotenv()

# Main flow.
LOGGER: Final = getLogger("discord")
BOT_TOKEN: Final = getenv("BOT_TOKEN", "")
BOT_USER_ID: Final = int(getenv("BOT_USER_ID", 0))
URL_PATTERN: Final = re.compile(r"https?://\S+|www\.\S+")
SPOILER_PATTERN: Final = re.compile(r"\|\|(.*?)\|\|", flags=re.S)
SERVER_WIDE_CHANNEL: Final = getenv("SERVER_WIDE_CHANNEL", "general")

# Directories
CUSTOM_MASKS_DIR: Final = Path(getenv("CUSTOM_MASKS_DIR", "./custom_masks")).resolve()
OUTPUT_DIR: Final = Path(getenv("OUTPUT_DIR", "./output")).resolve()

# Stopwords.
ALPHABET_STOPWORDS: Final = {chr(i) for i in range(ord("a"), ord("z") + 1)}
TOP_100_COMMON_WORDS: Final[set[LiteralString]] = {
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
CUSTOM_EXCLUSIONS: Final[set[LiteralString]] = {
    "TeaCloud",
    "wordcloud",
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
    STOPWORDS | ALPHABET_STOPWORDS | TOP_100_COMMON_WORDS | CUSTOM_EXCLUSIONS
)

# --- Helpers ------------------------------------------------------------------------ #


def get_all_text_channels(server: Guild) -> set[TextChannel]:
    return {channel for channel in server.channels if isinstance(channel, TextChannel)}


async def collect_messages(
    server_wide: bool, channel: TextChannel, server: Guild, after: datetime
) -> str:
    all_messages = " ".join(
        [
            message.content
            for channel in (get_all_text_channels(server) if server_wide else [channel])
            async for message in channel.history(after=after)
            if message.author.id != BOT_USER_ID
        ]
    )
    no_urls = URL_PATTERN.sub("", all_messages)
    no_spoilers = SPOILER_PATTERN.sub("", no_urls)
    return no_spoilers


def generate_word_cloud(text: str, server_id: int) -> File:
    mask_file = (CUSTOM_MASKS_DIR / f"{server_id}.png").resolve()
    mask = numpy.array(Image.open(mask_file.as_posix())) if mask_file.exists() else None
    output_file = (
        OUTPUT_DIR / f"{server_id}_{datetime.timestamp(datetime.today())}.png"
    ).resolve()
    WordCloud(
        background_color="white",
        mask=mask,
        color_func=ImageColorGenerator(mask) if mask_file.exists() else None,
        stopwords=ALL_STOPWORDS,
    ).generate(text).to_file(output_file.as_posix())

    return File(output_file.as_posix())


# --- Initialize Bot ----------------------------------------------------------------- #

intents = Intents.default()
intents.message_content = True

bot = Bot("/", intents=intents)

# --- Handlers ----------------------------------------------------------------------- #


@bot.event
async def on_ready() -> None:
    LOGGER.info("Syncing commands...")
    await bot.tree.sync()
    LOGGER.info("Commands synced succesfully!")


@bot.tree.command(
    description=(
        "Generates a word cloud of the last day of messages in this channel, or "
        f"the server if in #{SERVER_WIDE_CHANNEL}."
    ),
)
async def teacloud(interaction: Interaction) -> None:
    channel = interaction.channel
    server = interaction.guild
    if not isinstance(channel, TextChannel) or server is None:
        LOGGER.warning("Ran in improper context; aborting...")
        return

    server_wide = channel.name == SERVER_WIDE_CHANNEL
    log_prefix = f"[{server.name}.{"*" if server_wide else channel.name}]"
    twenty_four_hours_ago: Final = datetime.today() - timedelta(days=1)

    LOGGER.info(f"{log_prefix} Generating word cloud...")
    await interaction.response.defer(thinking=True)
    word_cloud_file = generate_word_cloud(
        await collect_messages(
            server_wide, channel, server, after=twenty_four_hours_ago
        ),
        server.id,
    )

    LOGGER.info(f"{log_prefix} Word cloud generated...")
    await interaction.followup.send(
        (
            f"Here's the {server.name} word cloud for "
            f"{"the whole server" if server_wide else "this channel"} "
            f"since yesterday, {twenty_four_hours_ago.strftime("%-I:%S %p")}."
        ),
        file=word_cloud_file,
    )


# --- Main --------------------------------------------------------------------------- #


def start() -> None:
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    start()
