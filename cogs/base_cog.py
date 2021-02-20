from discord import utils
from discord.ext import commands
from discord.ext.commands import MissingRole, CommandInvokeError, CommandNotFound

from util.logging_util import logger


class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def wait_until_ready(self):
        await self.bot.wait_until_ready()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, MissingRole):
            await ctx.reply('You are lacking a required role')
        elif isinstance(error, CommandNotFound):
            await ctx.reply(str(error))
        elif isinstance(error, CommandInvokeError):
            logger.critical('CommandInvokeError : ' + str(error))
        else:
            logger.critical('Misc Error : ' + str(error))

    async def cog_check(self, ctx):
        return not ctx.author.bot

    async def get_or_fetch_guild(self, guild_id):
        return guild if (guild := self.bot.get_guild(guild_id)) else await self.bot.fetch_guild(guild_id)

    async def get_or_fetch_channel(self, channel_id):
        return channel if (channel := self.bot.get_channel(channel_id)) else await self.bot.fetch_channel(channel_id)

    async def get_or_fetch_emoji(self, guild_id, emoji_id):
        if emoji := self.bot.get_emoji(emoji_id):
            return emoji
        else:
            guild = await self.get_or_fetch_guild(guild_id)
            return utils.get(guild.emojis, id=emoji_id)
