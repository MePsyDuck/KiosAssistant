import asyncio

import discord

from config import TOKEN, CHANNEL_ID, SLEEP_TIME
from util import read_email, log


# Taken from https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bg_task = self.loop.create_task(self.check_submissions())

    async def on_ready(self):
        log('Logged in as')
        log(self.user.name)
        log(self.user.id)
        log('------')
        await self.change_presence(
            activity=discord.Activity(name='Kio\'s commands', type=discord.ActivityType.listening))

    async def check_submissions(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        while not self.is_closed():
            new_submissions = read_email()
            if new_submissions and len(new_submissions) != 0:
                msg = 'New form submission(s) found.\n'
                msg += '\n'.join([f'- '
                                  f'{form.split(" ")[-2]}'  # Just a hack, needs to be revisited when new forms are added.
                                  f': {submission_count}' for form, submission_count in
                                  sorted(new_submissions.items())])
                log(msg)
                await channel.send(msg)
            await asyncio.sleep(SLEEP_TIME)


client = MyClient()
client.run(TOKEN)
