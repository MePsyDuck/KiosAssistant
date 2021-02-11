from discord.ext import commands

from cogs.base_cog import BaseCog
from database import User
from util.datetime_util import valid_timezone, valid_time_format


class UserCog(BaseCog):
    @commands.command(name='ViewProfile')
    async def view_profile(self, ctx):
        """Format : !!ViewProfile"""
        user, _ = await User.get_or_create(id=ctx.author.id)

        reply_msg = f'{ctx.author.name}:\n'
        reply_msg += f'Time zone: {user.time_zone or "Not set yet"}\n'
        reply_msg += f'Time format: {user.time_format or "Not set yet"}'

        await ctx.reply(reply_msg)

    @commands.command(name='SetTimeZone')
    async def set_timezone(self, ctx, *timezone):
        """Format : !!SetTimeZone <timezone>"""
        timezone = ' '.join(timezone).strip()
        if valid_timezone(timezone):
            await User.update_or_create(id=ctx.author.id, time_zone=timezone)
        else:
            await ctx.reply(f'`{timezone}` is not a valid timezone.')

    @commands.command(name='SetTimeFormat')
    async def set_clock(self, ctx, time_format: str):
        """Format : !!SetTimeFormat 12/24"""
        time_format = time_format.strip()
        if valid_time_format(time_format):
            await User.update_or_create(id=ctx.author.id, time_format=time_format)
        else:
            await ctx.reply(f'`{time_format}` is not a valid time format. Use `12`/`24`')
