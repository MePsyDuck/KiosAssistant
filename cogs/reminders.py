from discord.ext import commands, tasks
from tortoise.query_utils import Q

from cogs.base_cog import BaseCog
from config import MSG_MAX_LENGTH, TASK_SLEEP_TIME
from database import User, Message, Reminder
from database.util import atomic
from util.datetime_util import parse_time, render_time_diff, utc_now, render_time, datetime_from_timestamp, timestamp_from_datetime


class ReminderCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.check_reminders.start()

    @commands.command(name='RemindMe')
    @atomic
    async def create_reminder(self, ctx, *at_datetime):
        """ Format : !!RemindMe <at_datetime>, <info> """

        if ctx.author != self.bot.user and not ctx.author.bot:
            split = ' '.join(at_datetime).strip().split(',', 1)
            at_datetime = split[0]
            info = split[1].strip() if len(split) > 1 else None

            if at_datetime:
                try:
                    now = utc_now()
                    user, _ = await User.get_or_create(id=ctx.author.id)
                    reminder_datetime = parse_time(at_datetime, now, user)

                    if reminder_datetime is None:
                        raise ValueError

                    if reminder_datetime < now:
                        await ctx.reply('Provided time has already passed, can\'t schedule reminder')
                        return

                    for_message = await Message.create(id=ctx.message.id, channel_id=ctx.channel.id, user=user)
                    reminder = await Reminder.create(info=info, added_dt=utc_now(), expire_dt=reminder_datetime, for_message=for_message)
                    await ctx.reply(
                        f'You\'ll be reminded of {info if info else "this"} in {render_time_diff(start_date=now, end_date=reminder_datetime)}.\n'
                        f'Use command `!!ClearReminder {reminder.id}` to delete this reminder.`')
                except ValueError:
                    await ctx.reply('Invalid datetime format specified')
            else:
                await ctx.reply('Invalid command format.')
        else:
            await ctx.reply('Bots cannot use this command')

    @commands.command(name='MyReminders')
    @atomic
    async def get_reminders(self, ctx, from_timestamp: int = None):
        """Format : !!MyReminders <from_timestamp?>"""
        reply_msg = ''
        user, _ = await User.get_or_create(id=ctx.author.id)
        if from_timestamp is not None:
            from_dt = datetime_from_timestamp(from_timestamp)
            reminders = await Reminder.filter(Q(for_message__user=user) & Q(expire_dt__gte=from_dt)).order_by('expire_dt')
        else:
            reminders = await Reminder.filter(for_message__user=user).order_by('expire_dt')

        if reminders is not None and len(reminders) > 0:
            reply_msg += 'Your current reminders:\n'

            for reminder in reminders:
                if len(reply_msg) > MSG_MAX_LENGTH:
                    reply_msg += 'More reminders left that could not be displayed here.\n'
                    reply_msg += f'Reply with `!!MyReminders {timestamp_from_datetime(reminder.id)} to show remaining reminders'
                    break

                reply_msg += f'|{reminder.id}|{render_time(reminder.expire_dt, user)}|' \
                             f'{render_time_diff(utc_now(), reminder.expire_dt)}|{reminder.info}|\n'

            reply_msg += 'Reply with `!!ClearReminder id` or `!!ClearReminder all` to delete reminders'
        else:
            reply_msg += 'You don\'t have any reminders.'

        await ctx.reply(reply_msg)

    @commands.command(name='ClearReminder')
    @atomic
    async def delete_reminder(self, ctx, reminder_id: str):
        """Format : !!ClearReminder <id>/all"""
        user, _ = await User.get_or_create(id=ctx.author.id)
        if reminder_id.lower() == 'all':
            reminders_count = await Reminder.filter(for_message__user=user).count()

            if reminders_count > 0:
                await Reminder.filter(for_message__user=user).delete()
                await ctx.reply('All reminders deleted successfully.')
            else:
                await ctx.reply('You don\'t have any reminders.')
        elif reminder_id.isdecimal():
            reminder_id = int(reminder_id)
            reminder = await Reminder.get_or_none(id=reminder_id).prefetch_related('for_message__user')
            if reminder is not None:
                if reminder.for_message.user.id == user.id:
                    await reminder.delete()
                    await ctx.reply(f'Reminder {reminder_id} deleted successfully')
                else:
                    await ctx.reply(f'Reminder with ID: {reminder.id} was not created by you.')
            else:
                await ctx.reply(f'Reminder with ID: {reminder_id} not found.')
        else:
            await ctx.reply('Invalid reminder id')

    @tasks.loop(seconds=TASK_SLEEP_TIME)
    @atomic
    async def check_reminders(self):
        now = utc_now()
        reminders = await Reminder.filter(expire_dt__lte=now).prefetch_related('for_message')

        if reminders is not None and len(reminders) > 0:
            for reminder in reminders:
                channel = await self.get_or_fetch_channel(reminder.for_message.channel_id)
                message = await channel.fetch_message(reminder.for_message.id)

                await message.author.send(f'Hey, here\'s your reminder as you requested : {message.jump_url}')

            await Reminder.filter(expire_dt__lte=now).delete()

    @check_reminders.before_loop
    async def before_tasks(self):
        await self.wait_until_ready()

    def cog_unload(self):
        self.check_reminders.cancel()
