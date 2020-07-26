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

    async def check_submissions(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        while not self.is_closed():
            new_submissions = read_email()
            if new_submissions and len(new_submissions) != 0:
                msg = 'New form submission(s) found. '
                forms = sorted(new_submissions.items())
                if len(forms) == 1:
                    only_form = forms[0]
                    msg += f'{only_form[1]} new submission{"s" if only_form[1] > 1 else ""} in {only_form[0]}.'
                elif len(forms) > 1:
                    for form in forms[:-1]:
                        msg += f'{form[1]} new submission{"s" if form[1] > 1 else ""} in {form[0]}, '
                    last_form = forms[-1]
                    msg = msg[:-2] + f' and {last_form[1]} new submission{"s" if last_form[1] > 1 else ""} in {last_form[0]}.'
                log(msg)
                await channel.send(msg)
            await asyncio.sleep(SLEEP_TIME)


client = MyClient()
client.run(TOKEN)
