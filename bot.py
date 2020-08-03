import re
from datetime import datetime

import dateparser
import discord
from discord.ext import tasks
from discord.ext.commands import has_role, Bot, MissingRole

from config import TOKEN, SLEEP_TIME, EVENTS_CHANNEL_ID, EVENT_EMOJI, CAPTAINS_CHANNEL_ID
from util import log, schedule_event, get_current_events, delete_events, read_email

bot = Bot(command_prefix='!')


@bot.event
async def on_ready():
    log('Logged in as')
    log(bot.user.name)
    log(bot.user.id)
    log('------')
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
            msg = f'Reminder! {event["event_name"]} starts now!'
            channel = bot.get_channel(EVENTS_CHANNEL_ID)
            message = await channel.fetch_message(event['message_id'])
            for reaction in message.reactions:
                if reaction.emoji == EVENT_EMOJI:
                    members = await reaction.users().flatten()
                    for member in members:
                        if member != bot.user and not member.bot:
                            await member.send(content=msg, delete_after=60)
            log(msg)
            await channel.send(msg)
        delete_events(events)


@check_events.before_loop
async def before_check_events():
    await bot.wait_until_ready()


@bot.command(name='event')
@has_role('Sensei')
async def new_event(ctx, *event_info):
    """ Format : #event "<event_name>" <datetime> """
    event_format = re.compile(r'(?P<event_name>.*) :: (?P<time>.*)')

    event_info = ' '.join(event_info).strip()

    if (match := event_format.match(event_info)) is not None:
        event_name = match.group('event_name')
        try:
            event_time = match.group('time')
            event_datetime = dateparser.parse(event_time, settings={'TIMEZONE': 'UTC'})
            now = datetime.utcnow()
            if event_datetime < now:
                await ctx.send('Time has already passed, can\'t schedule the event')
                return
            channel = bot.get_channel(EVENTS_CHANNEL_ID)
            message = await channel.send(
                f'New Event: {event_name} {event_time}. Get a reminder by reacting with {EVENT_EMOJI}')
            schedule_event(message.id, event_name, event_datetime)
            await message.add_reaction(EVENT_EMOJI)
            await ctx.author.send('New event successfully scheduled!')
        except ValueError:
            await ctx.send('Invalid datetime format specified')
    else:
        await ctx.send('Invalid format.')


@new_event.error
async def new_event_error(ctx, error):
    if isinstance(error, MissingRole):
        await ctx.send('You are lacking a required role')
    else:
        log(str(error))
        raise error


# setup_logging()
check_events.start()
bot.run(TOKEN)
