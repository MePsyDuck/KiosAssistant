import email
import imaplib
import json
from collections import Counter

from discord.ext import tasks

from cogs.base_cog import BaseCog
from config import BOT_PWD, BOT_EMAIL
from config import TASK_SLEEP_TIME
from util.logging_util import logger


class SubmissionCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

        self.check_submissions.start()

    @staticmethod
    def read_email():
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            mail.login(BOT_EMAIL, BOT_PWD)
            mail.select('"Form Submission Notifications"')

            resp, mails = mail.search(None, '(UNSEEN)')
            if resp == 'OK':
                mail_id_list = list(mails[0].split())
                new_submissions = []
                for mail_id in mail_id_list:
                    # Fetch marks the email as seen
                    resp, data = mail.fetch(mail_id, '(RFC822)')
                    if resp == 'OK':
                        try:
                            # noinspection PyUnresolvedReferences
                            raw_email = data[0][1].decode('utf8')
                            msg = email.message_from_string(raw_email)
                            email_body = msg.get_payload(decode=True)
                            email_data = json.loads(email_body)
                            new_submissions.append(email_data['form_name'])
                        except IndexError as e:
                            logger.critical(f'Mail parse error. data format has changed. data {data}, e: {e}')
                    else:
                        logger.warning(f'Mail fetch failed. mail_id: {mail_id}, resp_code: {resp}')

                return dict(Counter(new_submissions))
            else:
                logger.warning(f'Mail search failed. resp_code: {resp}')

        except Exception as e:
            logger.critical(str(e))

    @tasks.loop(seconds=TASK_SLEEP_TIME)
    async def check_submissions(self):
        new_submissions = self.read_email()
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
