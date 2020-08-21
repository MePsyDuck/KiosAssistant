import re
from datetime import datetime

import dateparser
import discord
import psycopg2
from discord.ext import tasks
from discord.ext.commands import has_role, Bot, MissingRole, CommandInvokeError

from config import TOKEN, SLEEP_TIME, EVENTS_CHANNEL_ID, CAPTAINS_CHANNEL_ID, EVENT_REMINDER_TIMEOUT, DEBUG
from db_util import schedule_event, get_current_events, delete_events, delete_event, get_event
from util import log, read_email, get_event_emoji, render_time_diff, render_time, setup_logging

bot = Bot(command_prefix='!!')
bot.event_emoji = None


@bot.event
async def on_ready():
    log('Logged in as')
    log(bot.user.name)
    log(bot.user.id)
    log('------')
    bot.event_emoji = get_event_emoji(bot)
    await bot.change_presence(activity=discord.Activity(name='Kio\'s commands',
                                                        type=discord.ActivityType.listening))


@tasks.loop(seconds=SLEEP_TIME)
async def check_submissions():
    channel = bot.get_channel(CAPTAINS_CHANNEL_ID)
    new_submissions = read_email()
    if new_submissions and len(new_submissions) != 0:
        msg = 'New form submission(s) found.\n'
        msg += '\n'.join([f'- '
                          f'{form.split(" ")[-2]}'  # Just a hack, needs to be revisited when new forms are added.
                          f': {submission_count}' for form, submission_count in
                          sorted(new_submissions.items())])
        log(msg)
        await channel.send(msg)


@check_submissions.before_loop
async def before_check_submissions():
    await bot.wait_until_ready()


@tasks.loop(seconds=SLEEP_TIME)
async def check_events():
    events = get_current_events()
    if events and len(events) != 0:
        for event in events:
            msg = f'Reminder: Event {event["event_name"]} starts now!'
            channel = bot.get_channel(EVENTS_CHANNEL_ID)
            message = await channel.fetch_message(event['message_id'])
            for reaction in message.reactions:
                if reaction.emoji == bot.event_emoji:
                    members = await reaction.users().flatten()
                    for member in members:
                        if member != bot.user and not member.bot:
                            try:
                                await member.send(content=msg, delete_after=EVENT_REMINDER_TIMEOUT)
                            except discord.errors.Forbidden as e:
                                log(f'Could not remind user {member}, error: {e.code}')
            await channel.send(msg)
            # await message.delete()
        delete_events(events)


@check_events.before_loop
async def before_check_events():
    await bot.wait_until_ready()


@bot.command(name='new_event')
@has_role('Sensei')
async def new_event(ctx, *event_details):
    """ Format : !!event <event_name>, <event_datetime>. <event_info>"""
    name_date_sep = ','
    date_info_sep = '.'
    event_format = re.compile(
        rf'(?P<event_name>.+?){name_date_sep}(?P<event_time>.+?(?=\.)){date_info_sep}(?P<event_info>.*)')

    event_details = ' '.join(event_details).strip()

    if (match := event_format.match(event_details)) is not None:
        event_name = match.group('event_name').strip()
        try:
            event_time = match.group('event_time').strip()
            event_datetime = dateparser.parse(event_time, settings={'TIMEZONE': 'UTC'})
            if event_datetime is None:
                raise ValueError
            now = datetime.utcnow()
            if event_datetime < now:
                await ctx.send('Time has already passed, can\'t schedule the event')
                return

            event_info = match.group('event_info').strip()
            channel = bot.get_channel(EVENTS_CHANNEL_ID)
            message = await channel.send(
                f"New Event: {event_name}, starting {f'in {time}, ' if (time := render_time_diff(now, event_datetime)) is not None else ''}"
                f"on {render_time(event_datetime)}. Get a reminder by reacting with {bot.event_emoji}"
                f"\n{event_info}")
            new_event_id = schedule_event(message.id, event_name, event_datetime)
            await message.add_reaction(bot.event_emoji)
            await ctx.author.send(
                f'New event successfully scheduled! Event : {event_name}, ID : {new_event_id}.\nUse command `!!clear_event {new_event_id}` in any channel to unschedule the event.')
        except ValueError:
            await ctx.send('Invalid datetime format specified')
    else:
        await ctx.send('Invalid format.')


@bot.command(name='clear_event')
@has_role('Sensei')
async def clear_event(ctx, event_id: int):
    event = get_event(event_id)
    if event is not None:
        delete_event(event)
        channel = bot.get_channel(EVENTS_CHANNEL_ID)
        message = await channel.fetch_message(event['message_id'])
        await message.delete()
        await ctx.author.send(f'Event {event["event_name"]}, ID {event_id}  successfully cleared!')
    else:
        await ctx.author.send(f'Event with ID {event_id} not found.')


@bot.command(name='clear_events')
@has_role('Sensei')
async def clear_events(ctx):
    # deleted_event_count = delete_all_events()
    # if deleted_event_count == 0:
    #     await ctx.author.send(f'No events were scheduled.')
    # if deleted_event_count == 1:
    #     await ctx.author.send(f'{deleted_event_count} event successfully cleared!')
    # else:
    #     await ctx.author.send(f'All of {deleted_event_count} events successfully cleared!')

    # Commented as this doesn't seem like a good idea
    await ctx.author.send('This command does not work as of now. Please contact Kio or MePsyDuck')


@new_event.error
@clear_event.error
@clear_events.error
async def handle_error(ctx, error):
    if isinstance(error, MissingRole):
        await ctx.send('You are lacking a required role')
    elif isinstance(error, CommandInvokeError):
        if isinstance(error.original, psycopg2.Error):
            log('Postgres Error : ' + str(error.original))
            await ctx.author.send('Error clearing events, contact Kio or MePsyDuck')
        else:
            log('Misc CommandInvokeError : ' + str(error))
    else:
        log('Misc Error : ' + str(error))


if DEBUG == '1':
    setup_logging()
check_submissions.start()
check_events.start()
bot.run(TOKEN)
