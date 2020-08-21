from datetime import datetime

import psycopg2

from config import DATABASE_URL


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
                   'VALUES (%s, %s, %s) RETURNING event_id;'
    cur.execute(insert_query, (message_id, event_name, event_datetime,))

    new_event_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return new_event_id


def get_event(event_id):
    conn = get_connection()
    cur = conn.cursor()

    select_query = 'SELECT event_id, message_id, event_name, event_datetime FROM events ' \
                   'WHERE event_id = (%s);'
    cur.execute(select_query, (event_id,))
    event = None if (row := cur.fetchone()) is None else {'event_id': row[0], 'message_id': row[1],
                                                          'event_name': row[2], 'event_datetime': row[3]}

    conn.commit()
    cur.close()
    conn.close()

    return event


def get_current_events():
    conn = get_connection()
    cur = conn.cursor()

    select_query = 'SELECT event_id, message_id, event_name, event_datetime FROM events ' \
                   'WHERE event_datetime < (%s);'
    cur.execute(select_query, (datetime.utcnow(),))
    events = [{'event_id': row[0], 'message_id': row[1], 'event_name': row[2], 'event_datetime': row[3]} for row in
              cur.fetchall()]

    conn.commit()
    cur.close()
    conn.close()

    return events


def delete_event(event):
    conn = get_connection()
    cur = conn.cursor()

    delete_query = 'DELETE FROM events ' \
                   'WHERE event_id = (%s);'
    cur.execute(delete_query, (event['event_id'],))

    conn.commit()
    cur.close()
    conn.close()


def delete_events(events):
    conn = get_connection()
    cur = conn.cursor()

    event_ids = [event['event_id'] for event in events]
    delete_query = 'DELETE FROM events ' \
                   'WHERE event_id = ANY (%s);'
    cur.execute(delete_query, (event_ids,))

    conn.commit()
    cur.close()
    conn.close()


def delete_all_events():
    conn = get_connection()
    cur = conn.cursor()

    delete_query = 'TRUNCATE events'
    cur.execute(delete_query)
    deleted_event_count = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()

    return deleted_event_count
