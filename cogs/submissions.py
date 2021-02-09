from discord.ext import tasks

from cogs.base_cog import BaseCog
from config import TASK_SLEEP_TIME
from util.email_util import read_email
from util.logging_util import logger


class SubmissionCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.check_submissions.start()

    @tasks.loop(seconds=TASK_SLEEP_TIME)
    async def check_submissions(self):
        new_submissions = read_email()
        if new_submissions and len(new_submissions) != 0:

            msg = 'New form submission(s) found.\n'
            msg += '\n'.join([f'- '
                              f'{form.split(" ")[-2]}'  # Just a hack, needs to be revisited when new forms are added.
                              f': {submission_count}' for form, submission_count in
                              sorted(new_submissions.items())])
            logger.info(msg)

            captains_channel = await self.get_or_fetch_channel(708609781610315807)
            await captains_channel.send(msg)

    @check_submissions.before_loop
    async def before_tasks(self):
        await self.wait_until_ready()

    def cog_unload(self):
        self.check_submissions.cancel()
