import discord
from discord.ext import commands
from discord.ext.commands import Bot

from cogs.events import EventCog
from cogs.reminders import ReminderCog
from cogs.submissions import SubmissionCog
from cogs.users import UserCog
from config import TOKEN, DEBUG
from util.logging_util import setup_logging, logger

bot = Bot(command_prefix=commands.when_mentioned_or('!!'))


@bot.event
async def on_ready():
    logger.info('Logged in as')
    logger.info(bot.user.name)
    logger.info(bot.user.id)
    logger.info('------------')
    await bot.change_presence(activity=discord.Activity(name='Kio\'s commands',
                                                        type=discord.ActivityType.listening))


if __name__ == "__main__":
    setup_logging()

    bot.add_cog(EventCog(bot))
    bot.add_cog(ReminderCog(bot))
    if not DEBUG:
        bot.add_cog(SubmissionCog(bot))
    bot.add_cog(UserCog(bot))

    bot.run(TOKEN)
