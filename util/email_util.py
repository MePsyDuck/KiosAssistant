import email
import imaplib
import json
from collections import Counter

from config import SMTP_SERVER, SMTP_PORT, BOT_PWD, BOT_EMAIL, MAIL_LABEL, RESP_OK
from util.logging_util import logger


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