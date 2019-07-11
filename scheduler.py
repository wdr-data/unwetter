#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""
from time import sleep

from apscheduler.schedulers.blocking import BlockingScheduler

from unwetter import db, slack, wina, sentry
from unwetter.config import filter_event


sentry.init()
sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def update_db():
    """
    You should not do actual work in the scheduler.
    For now, we do it anyways.
    """
    print('Running update job')
    new_events = db.update()

    if new_events is None:
        return

    # Filter new_events by SEVERITY_FILTER, URGENCY_FILTER and STATES_FILTER
    filtered = []
    for event in new_events:
        if event['msg_type'] == 'Cancel' and any(item['published'] for item in event['has_changes']):
            filtered.append(event)

        elif not filter_event(event):
            continue

        elif event['msg_type'] == 'Alert':
            filtered.append(event)

        elif any(item['changed'] and item['published'] for item in event['has_changes']):
            filtered.append(event)

        elif event['special_type'] == 'UpdateAlert':
            filtered.append(event)

        elif not any(item['changed'] and item['published'] for item in event['has_changes']):
            continue

        else:
            sentry.sentry_sdk.capture_message(f'Event was not filtered: {event["id"]}')

    if filtered:
        db.publish([event['id'] for event in filtered])

        wina.upload([event['id'] for event in filtered])

        for event in filtered:
            print(f'Sending event {event["id"]} to Slack')
            slack.post_event(event)
            sleep(1)


@sched.scheduled_job('interval', minutes=5)
def post_clear_warning():

    currently_events = db.current_events(all_severities=False)
    if currently_events:
        db.set_warn_events_memo(True)
        print('Active events: warn events memo ON')
    elif db.warn_events_memo() and not currently_events:
        db.set_warn_events_memo(False)

        title = 'Warnfplicht für NRW aufgehoben'
        text = '''
AKTUALISIERUNG:
Der Deutsche Wetterdienst gibt für NRW zurzeit keine Warnungen der Kategorie 3 (rot) und 4 (violett) mehr aus -
also vor Unwetter oder extremem Unwetter. Damit besteht keine Warnpflicht mehr. Es kann allerdings nach wie vor
markante Wetterlagen geben - alle Informationen dazu auf einen Blick hier:

UWA-Kartentool: www.wdr.de/k/unwetterkarte

https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html
(Vgl. NRW auf Website des Deutschen Wetterdienstes)
'''.strip()

        keywords = 'Unwetter, UWA, Keine Warnpflicht'

        wina.upload_text(title, text, keywords)

        slack.post_text(title, text)

        print('No active events: warn_events_memo OFF')


sched.start()
