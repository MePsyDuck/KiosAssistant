import discord
from discord.ext import commands

from cogs.events import EventCog
from cogs.reminders import ReminderCog
from cogs.submissions import SubmissionCog
from cogs.users import UserCog
from config import DEBUG
from database import init_orm
from util.logging_util import logger


class AssistantBot(commands.Bot):
    __version__ = "2.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_cog(EventCog(self))
        self.add_cog(ReminderCog(self))
        if not DEBUG:
            self.add_cog(SubmissionCog(self))
        self.add_cog(UserCog(self))

        self.loop.create_task(init_orm())

    async def on_ready(self):
        logger.info('Logged in as')
        logger.info(self.user.name)
        logger.info(self.user.id)
        logger.info('------------')
        await self.change_presence(activity=discord.Activity(name='Kio\'s commands',
                                                             type=discord.ActivityType.listening))
