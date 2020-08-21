import email
import imaplib
import json
import logging
import sys
from collections import Counter

import pytz
from dateutil.relativedelta import relativedelta

from config import SMTP_SERVER, BOT_EMAIL, BOT_PWD, SMTP_PORT, RESP_OK, MAIL_LABEL, EVENTS_CHANNEL_ID, \
    EVENT_EMOJI


# noinspection PyUnresolvedReferences
def read_email():
    try:
        mail = imaplib.IMAP4_SSL(SMTP_SERVER, SMTP_PORT)
        mail.login(BOT_EMAIL, BOT_PWD)
        mail.select(MAIL_LABEL)

        resp, mails = mail.search(None, '(UNSEEN)')
        if resp == RESP_OK:
            mail_id_list = list(mails[0].split())
            new_submissions = []
            for mail_id in mail_id_list:
                # Fetch marks the email as seen
                resp, data = mail.fetch(mail_id, '(RFC822)')
                if resp == RESP_OK:
                    try:
                        raw_email = data[0][1].decode('utf8')
                        msg = email.message_from_string(raw_email)
                        email_body = msg.get_payload(decode=True)
                        email_data = json.loads(email_body)
                        new_submissions.append(email_data['form_name'])
                    except IndexError as e:
                        log(f'Mail parse error. data format has changed. data {data}, e: {e}')
                else:
                    log(f'Mail fetch failed. mail_id: {mail_id}, resp_code: {resp}')

            return dict(Counter(new_submissions))
        else:
            log(f'Mail search failed. resp_code: {resp}')

    except Exception as e:
        log(str(e))


def get_event_emoji(bot):
    channel = bot.get_channel(EVENTS_CHANNEL_ID)
    for emoji in channel.guild.emojis:
        if emoji.name == EVENT_EMOJI:
            return emoji


def log(msg):
    print(msg)


def setup_logging():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)


# Code taken and adjusted from https://github.com/Watchful1/RemindMeBot/blob/master/src/utils.py
def render_time(date_time, add_link=False):
    return f'{date_time.astimezone(pytz.UTC).strftime("%Y-%m-%d %I:%M:%S %p %Z")}' + \
           (f'(http://www.wolframalpha.com/input/?i={date_time.strftime("%Y-%m-%d %H:%M:%S %Z")} To Local Time)'.replace(
               ' ', '%20') if add_link else ' ')


def render_time_diff(start_date, end_date):
    seconds = int((end_date - start_date).total_seconds())
    if seconds > 59:
        try:
            adjusted_end_date = start_date + relativedelta(seconds=int(min(seconds * 1.02, seconds + 60 * 60 * 24)))
        except OverflowError:
            log('Overflow occurred for end_time :' + end_date)
            return ''
        delta = relativedelta(adjusted_end_date, start_date)
    else:
        delta = relativedelta(end_date, start_date)
    if delta.years > 0:
        return f"{delta.years} year{('s' if delta.years > 1 else '')}"
    elif delta.months > 0:
        return f"{delta.months} month{('s' if delta.months > 1 else '')}"
    elif delta.days > 0:
        return f"{delta.days} day{('s' if delta.days > 1 else '')}"
    elif delta.hours > 0:
        return f"{delta.hours} hour{('s' if delta.hours > 1 else '')}"
    elif delta.minutes > 0:
        return f"{delta.minutes} minute{('s' if delta.minutes > 1 else '')}"
    else:
        return ''
