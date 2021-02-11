import re

import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_role
from tortoise.query_utils import Q

from cogs.base_cog import BaseCog
from config import MSG_MAX_LENGTH, TASK_SLEEP_TIME, DEBUG
from database import User, Message, Event
from database.util import atomic
from util.datetime_util import render_time, render_time_diff, parse_time, utc_now, timestamp_from_datetime, datetime_from_timestamp
from util.logging_util import logger


class EventCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.event_reminder_timeout = 600

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
    @atomic
    async def new_event(self, ctx, *event_details):
        """ Format : !!NewEvent <event_name>, <event_datetime>. <event_info>"""
        event_details = ' '.join(event_details).strip()

        if (match := self.event_format.match(event_details)) is not None:
            event_name = match.group('event_name').strip()
            try:
                at_datetime = match.group('event_time').strip()
                event_info = match.group('event_info').strip()

                now = utc_now()
                user, _ = await User.get_or_create(id=ctx.author.id)
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

                author_message = await Message.create(id=ctx.message.id, channel_id=ctx.channel.id, user=user)
                bot_message = await Message.create(id=message.id, channel_id=message.channel.id, user_id=self.bot.user.id)
                new_event = await Event.create(author_message=author_message, bot_message=bot_message, event_name=event_name, scheduled_dt=event_datetime)

                await message.add_reaction(event_emoji)
                await ctx.reply(
                    f'New event :"{new_event.name}" successfully scheduled!.\nUse command `!!clear_event {new_event.id}`'
                    f'to delete the event.')

            except ValueError:
                await ctx.reply('Invalid datetime format specified')
        else:
            await ctx.reply('Invalid format.')

    @commands.command(name='MyEvents')
    @atomic
    async def get_events(self, ctx, from_timestamp: int = None):
        """Format : !!MyEvents <from_timestamp?>"""
        reply_msg = ''
        user, _ = await User.get_or_create(id=ctx.author.id)
        if from_timestamp is not None:
            from_dt = datetime_from_timestamp(from_timestamp)
            events = await Event.filter(Q(author_message__user=user) & Q(scheduled_dt__gte=from_dt)).order_by('scheduled_dt')
        else:
            events = await Event.filter(author_message__user=user).order_by('scheduled_dt')

        if events is not None and len(events) > 0:
            reply_msg += 'Your current events:\n'

            for event in events:
                if len(reply_msg) > MSG_MAX_LENGTH:
                    reply_msg += 'More events left that could not be displayed here.\n'
                    reply_msg += f'Reply with `!!MyEvents {timestamp_from_datetime(event.scheduled_dt)} to show remaining events'
                    break

                reply_msg += f'|{event.id}|{render_time(event.scheduled_dt, user)}|' \
                             f'{render_time_diff(utc_now(), event.scheduled_dt)}|{event.name}|\n'

            reply_msg += 'Reply with `!!CancelEvent id` or `!!CancelEvent all` to delete events'
        else:
            reply_msg += 'You don\'t have any events.'

        await ctx.reply(reply_msg)

    @commands.command(name='CancelEvent')
    @has_role('Sensei')
    @atomic
    async def cancel_event(self, ctx, event_id: str):
        """Format : !!CancelEvent <id>/all"""
        user, _ = await User.get_or_create(id=ctx.author.id)
        if event_id.lower() == 'all':
            events = await Event.filter(author_message__user=user).prefetch_related('bot_message')

            if len(events) > 0:
                await Event.filter(author_message__user=user).delete()
                for event in events:
                    event_channel = await self.get_or_fetch_channel(event.bot_message.channel_id)
                    event_message = event_channel.fetch_message(event.bot_message.id)
                    await event_message.delete()
                await ctx.reply('All events deleted successfully.')
            else:
                await ctx.reply('You don\'t have any events.')
        elif event_id.isdecimal():
            event_id = int(event_id)
            event = await Event.get_or_none(id=event_id).prefetch_related('bot_message', 'bot_message__user')
            if event is not None:
                if event.bot_message.user.id == user.id:
                    await event.delete()
                    event_channel = await self.get_or_fetch_channel(event.bot_message.channel_id)
                    event_message = await event_channel.fetch_message(event.bot_message.id)
                    await event_message.delete()
                    await ctx.reply(f'Event {event.name}  successfully deleted!')
                else:
                    await ctx.reply(f'Event with ID: {event_id} was not created by you.')
            else:
                await ctx.reply(f'Event with ID: {event_id} not found.')
        else:
            await ctx.reply(f'Invalid event id')

    @tasks.loop(seconds=TASK_SLEEP_TIME)
    @atomic
    async def check_events(self):
        now = utc_now()
        events = await Event.filter(scheduled_dt__lte=now).prefetch_related('bot_message')

        if events is not None and len(events) > 0:
            for event in events:
                msg = f'Reminder: Event {event.name} starts now!'
                event_channel = await self.get_or_fetch_channel(event.bot_message.channel_id)
                event_emoji = await self.get_or_fetch_emoji(event_channel.guild.id, self.event_emoji_id)
                message = await event_channel.fetch_message(event.bot_message.id)
                for reaction in message.reactions:
                    if reaction.emoji == event_emoji:
                        members = await reaction.users().flatten()
                        for member in members:
                            if member != self.bot.user and not member.bot:
                                try:
                                    await member.send(content=msg, delete_after=self.event_reminder_timeout)
                                except discord.errors.Forbidden as e:
                                    logger.critical(f'Could not remind user of event {member}, error: {e.code}')
                await event_channel.send(content=msg, delete_after=self.event_reminder_timeout)
            await Event.filter(scheduled_dt__lte=now).delete()

    @check_events.before_loop
    async def before_tasks(self):
        await self.wait_until_ready()

    def cog_unload(self):
        self.check_events.cancel()
