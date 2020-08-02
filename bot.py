import re
from datetime import datetime

import dateparser
import discord
from discord.ext import tasks
from discord.ext.commands import has_role, CheckFailure, Bot

from config import TOKEN, CAPTAINS_CHANNEL_ID, SLEEP_TIME, EVENTS_CHANNEL_ID
from util import read_email, log, schedule_event, get_current_events, delete_events

bot = Bot(command_prefix='#')


@bot.event
async def on_ready():
    log('Logged in as')
    log(bot.user.name)
    log(bot.user.id)
    log('------')
    await bot.change_presence(
        activity=discord.Activity(name='Kio\'s commands', type=discord.ActivityType.listening))


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
    channel = bot.get_channel(EVENTS_CHANNEL_ID)
    events = get_current_events()
    if events and len(events) != 0:
        for event in events:
            msg = f'Reminder! {event["event_name"]} starts now!'
            message = await channel.fetch_message(event['message_id'])
            for reaction in message.reactions:
                if reaction.emoji.name == ':voteYes:':
                    users = await reaction.users().flatten()
                    for user in users:
                        await user.send(content=msg, delete_after=60 * 60)
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
    event_format = re.compile(r'"(?P<event_name>.*?)" (?P<time>.*?)')

    event_info = ' '.join(event_info).strip()

    if (match := event_format.match(event_info)) is not None:
        event_name = match.group('event_name')
        try:
            event_datetime = dateparser.parse(match.group('time'))
            if event_datetime > datetime.utcnow():
                await ctx.send('Time has already passed, can\'t schedule the event')
                return
            schedule_event(ctx.message.id, event_name, event_datetime)
            channel = bot.get_channel(EVENTS_CHANNEL_ID)
            await channel.send(f'New Event: {event_info}. Get a reminder by reacting with :voteYes:')
            await ctx.author.send('New event scheduled!')
        except ValueError:
            await ctx.send('Invalid datetime format specified')
    else:
        await ctx.send('Invalid format.')


@new_event.error
async def new_event_error(error, ctx):
    if isinstance(error, CheckFailure):
        await ctx.send(ctx.message.channel, 'You are lacking a required role')
    else:
        raise error


bot.run(TOKEN)
