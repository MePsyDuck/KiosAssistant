import re

import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_role

from cogs.base_cog import BaseCog
from config import MSG_MAX_LENGTH, TASK_SLEEP_TIME, DEBUG
from database.api import db_api
from util.datetime_util import render_time, render_time_diff, parse_time, utc_now, timestamp_from_datetime, datetime_from_timestamp
from util.logging_util import logger


class EventCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.event_reminder_timeout = 120

        if DEBUG:
            self.event_channel_id = 739549756019179601
            self.event_emoji_id = 744635360524369982
        else:
            self.event_channel_id = 623521212676440074
            self.event_emoji_id = 766214664065384480

        name_date_sep = ','
        date_info_sep = '.'
        self.event_format = re.compile(
            rf'(?P<event_name>.+?){name_date_sep}(?P<event_time>.+?(?=\.)){date_info_sep}(?P<event_info>.*)')

        self.check_events.start()

    @commands.command(name='NewEvent')
    @has_role('Sensei')
    async def new_event(self, ctx, *event_details):
        """ Format : !!NewEvent <event_name>, <event_datetime>. <event_info>"""
        event_details = ' '.join(event_details).strip()

        if (match := self.event_format.match(event_details)) is not None:
            event_name = match.group('event_name').strip()
            try:
                at_datetime = match.group('event_time').strip()
                event_info = match.group('event_info').strip()

                now = utc_now()
                user = db_api.users.get_or_add(ctx.author.id)
                event_datetime = parse_time(at_datetime, now, user)

                if event_datetime is None:
                    raise ValueError

                if event_datetime < now:
                    await ctx.reply('Time has already passed, can\'t schedule the event')
                    return

                event_channel = await self.get_or_fetch_channel(self.event_channel_id)
                event_emoji = await self.get_or_fetch_emoji(event_channel.guild.id, self.event_emoji_id)
                message = await event_channel.send(
                    f"New Event: {event_name}, starting {f'in {time}, ' if (time := render_time_diff(now, event_datetime)) is not None else ''}"
                    f"on {render_time(event_datetime, user)}. Get a reminder by reacting with {event_emoji}"
                    f"\n{event_info}")

                author_message = db_api.messages.add(ctx.message.id, ctx.message.channel_id, user.id)
                event_message = db_api.messages.add(message.id, message.channel_id, self.bot.user.id)
                new_event = db_api.events.add(author_message.id, event_message.id, event_name, event_datetime)

                await message.add_reaction(event_emoji)
                await ctx.reply(
                    f'New event :"{new_event.name}" successfully scheduled!.\nUse command `!!clear_event {new_event.id}`'
                    f'to delete the event.')

            except ValueError:
                await ctx.reply('Invalid datetime format specified')
        else:
            await ctx.reply('Invalid format.')

    @commands.command(name='MyEvents')
    async def get_events(self, ctx, from_timestamp: int = None):
        """Format : !!MyEvents <from_timestamp?>"""
        reply_msg = ''
        user = db_api.users.get(user_id=ctx.author.id)
        from_dt = datetime_from_timestamp(from_timestamp)
        events = db_api.users.get_events(user.id, from_dt)

        if events:
            reply_msg += 'Your current events:\n'

            for event in events:
                if len(reply_msg) > MSG_MAX_LENGTH:
                    reply_msg += 'More events left that could not be displayed here.\n'
                    reply_msg += f'Reply with `!!MyEvents {timestamp_from_datetime(event.scheduled_dt)} to show remaining events'
                    break

                reply_msg += f'|{event.id}|{render_time(event.scheduled_dt, user)}|' \
                             f'{render_time_diff(utc_now(), event.scheduled_dt)}|{event.name}|\n'

            reply_msg += 'Reply with `!!ClearEvent id` or `!!ClearEvent all` to delete events'
        else:
            reply_msg += 'You don\'t have any events.'

        await ctx.reply(reply_msg)

    @commands.command(name='ClearEvent')
    @has_role('Sensei')
    async def clear_event(self, ctx, event_id: str):
        """Format : !!ClearEvent <id>/all"""
        if event_id.lower() == 'all':
            user = db_api.users.get(ctx.author.id)
            if len(user.events) > 0:
                db_api.events.delete_for_user(user.id)

                for event in user.events:
                    channel = await self.get_or_fetch_channel(event.event_message.channel_id)
                    event_message = channel.get_message(event.event_message.id)
                    await event_message.delete()
                await ctx.reply('All events deleted successfully.')
            else:
                await ctx.reply('You don\'t have any events.')
        elif event_id.isdecimal():
            event_id = int(event_id)
            event = db_api.events.get(event_id)
            if event is not None:
                channel = await self.get_or_fetch_channel(event.event_message.channel_id)
                event_message = await channel.fetch_message(event.event_message.id)
                db_api.events.delete(event.id)
                await event_message.delete()
                await ctx.reply(f'Event {event.name}  successfully deleted!')
            else:
                await ctx.reply(f'Event with ID: {event_id} not found.')
        else:
            await ctx.reply(f'Invalid event id')

    @tasks.loop(seconds=TASK_SLEEP_TIME)
    async def check_events(self):
        events = db_api.events.get_current()
        if events is not None and len(events) > 0:
            for event in events:
                msg = f'Reminder: Event {event.name} starts now!'
                channel = await self.get_or_fetch_channel(event.event_message.channel_id)
                event_emoji = await self.get_or_fetch_emoji(channel.guild.id, self.event_emoji_id)
                message = await channel.fetch_message(event.event_message.id)
                for reaction in message.reactions:
                    if reaction.emoji == event_emoji:
                        members = await reaction.users().flatten()
                        for member in members:
                            if member != self.bot.user and not member.bot:
                                try:
                                    await member.send(content=msg, delete_after=self.event_reminder_timeout)
                                except discord.errors.Forbidden as e:
                                    logger.critical(f'Could not remind user {member}, error: {e.code}')
                await channel.send(msg)
                db_api.events.delete(event.id)

    @check_events.before_loop
    async def before_tasks(self):
        await self.wait_until_ready()

    def cog_unload(self):
        self.check_events.cancel()
