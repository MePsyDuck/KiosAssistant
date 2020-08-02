import email
import imaplib
import json
from collections import Counter
from datetime import datetime

import psycopg2

from config import SMTP_SERVER, BOT_EMAIL, BOT_PWD, SMTP_PORT, RESP_OK, MAIL_LABEL, DATABASE_URL


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


def log(msg):
    print(msg)


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def schedule_event(message_id, event_name, event_datetime):
    """
    CREATE TABLE events (
    event_id SERIAL,
    message_id BIGINT,
    event_name VARCHAR(255),
    event_datetime TIMESTAMP
    );
    """
    conn = get_connection()
    cur = conn.cursor()

    insert_query = 'INSERT INTO events (message_id, event_name, event_datetime) ' \
                   'VALUES (%s, %s)'
    cur.execute(insert_query, (message_id, event_name, event_datetime,))

    cur.commit()
    cur.close()
    conn.close()


def get_current_events():
    conn = get_connection()
    cur = conn.cursor()

    select_query = 'SELECT message_id, event_id, event_name, event_datetime FROM events ' \
                   'WHERE event_datetime < (%s)'
    cur.execute(select_query, (datetime.utcnow(),))
    events = [{'message_id': row[0], 'event_id': row[1], 'event_name': row[2], 'event_datetime': row[3]} for row in
              cur.fetchall()]

    cur.commit()
    cur.close()
    conn.close()
    return events


def delete_events(events):
    conn = get_connection()
    cur = conn.cursor()

    event_ids = [event['event_id'] for event in events]
    delete_query = 'DELETE FROM events ' \
                   'WHERE event_id = ANY (%s)'
    cur.execute(delete_query, (event_ids,))

    cur.commit()
    cur.close()
    conn.close()
