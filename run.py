from discord.ext import commands

from bot import AssistantBot
from config import TOKEN
from util.logging_util import setup_logging

if __name__ == "__main__":
    setup_logging()
    AssistantBot(command_prefix=commands.when_mentioned_or('!!'), help_command=None).run(TOKEN)
