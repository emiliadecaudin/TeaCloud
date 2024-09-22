# --- Imports ------------------------------------------------------------------------ #

import re
from datetime import datetime, timedelta
from logging import getLogger
from os import getenv
from pathlib import Path
from typing import Final

import numpy
from discord.channel import TextChannel
from discord.client import Client
from discord.ext.commands import Bot
from discord.file import File
from discord.flags import Intents
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
URL_PATTERN: Final = re.compile(r"https?://\S+|www\.\S+")
SERVER_WIDE_CHANNEL: Final = getenv("SERVER_WIDE_CHANNEL", "general")

# Directories
CUSTOM_MASKS_DIR: Final = Path(getenv("CUSTOM_MASKS_DIR", "./custom_masks")).resolve()
OUTPUT_DIR: Final = Path(getenv("OUTPUT_DIR", "./output")).resolve()

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
CUSTOM_EXCLUSIONS: Final = {
    "Tea Cloud",
    "TeaCloud",
    "wordcloud",
    "word cloud",
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


def get_all_text_channels(client: Client) -> set[TextChannel]:
    channels = set[TextChannel]()
    for channel in client.get_all_channels():
        if isinstance(channel, TextChannel):
            channels.add(channel)
    return channels


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
    name="teacloud",
    description=(
        "Generates a word cloud of the last day of messages in this channel, or "
        f"the server if in #{SERVER_WIDE_CHANNEL}."
    ),
)
async def teacloud(interaction: Interaction) -> None:
    channel = interaction.channel
    server = interaction.guild
    if not isinstance(channel, TextChannel) or server is None:
        return

    server_wide = channel.name == SERVER_WIDE_CHANNEL
    log_prefix = f"[{server.name}.{"*" if server_wide else channel.name}]"

    LOGGER.info(f"{log_prefix} Collecting messages...")
    twenty_four_hours_ago: Final = datetime.today() - timedelta(days=1)
    text = URL_PATTERN.sub(
        "",
        " ".join(
            [
                message.content
                for channel in (
                    get_all_text_channels(bot) if server_wide else [channel]
                )
                async for message in channel.history(after=twenty_four_hours_ago)
            ]
        ),
    )

    message_description = f"word cloud for {"the whole server" if server_wide else "this channel"} since {twenty_four_hours_ago}"

    LOGGER.info(f"{log_prefix} Generating word cloud...")
    await interaction.response.send_message(
        f"Generating {message_description}.",
        ephemeral=True,
    )
    mask_file = (CUSTOM_MASKS_DIR / f"{server.id}.png").resolve()
    mask = numpy.array(Image.open(mask_file.as_posix())) if mask_file.exists() else None
    output_file = (OUTPUT_DIR / f"{server.id}_{twenty_four_hours_ago}.png").resolve()
    WordCloud(
        background_color="white",
        mask=mask,
        color_func=ImageColorGenerator(mask) if mask_file.exists() else None,
        stopwords=ALL_STOPWORDS,
    ).generate(text).to_file(output_file.as_posix())

    LOGGER.info(f"{log_prefix} Word cloud generated...")
    await interaction.response.send_message(
        f"Here's the {server.name} {message_description}.",
        file=File(output_file),
    )


# --- Main --------------------------------------------------------------------------- #


def start() -> None:
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    start()
