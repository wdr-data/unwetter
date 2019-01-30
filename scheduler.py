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
        if filter_event(event):
            if event['msg_type'] == 'Alert' or any(t['changed'] for t in event['has_changes']):
                filtered.append(event)

            elif all(not t['changed'] for t in event['has_changes']):
                continue

            elif any(t['changed'] for t in event['has_changed']):
                filtered.append(event)

            elif event['msg_type'] == 'Cancel':
                filtered.append(event)

            else:
                sentry.sentry_sdk.capture_message(f'Event was not filtered: {event["id"]}')

        else:
            if event['msg_type'] in ['Alert', 'Cancel']:
                continue

            else:
                old_events = db.by_ids(event['references'])

                if any(old_event['published'] for old_event in old_events):
                    filtered.append(event)

                elif all(not old_event['published'] for old_event in old_events):
                    continue

                else:
                    sentry.sentry_sdk.capture_message(f'Event was not filtered: {event["id"]}')

    if not filtered:
        return

    db.publish([event['id'] for event in filtered])

    wina.upload([event['id'] for event in filtered])

    for event in filtered:
        print(f'Sending event {event["id"]} to Slack')
        slack.post_event(event)
        sleep(1)


sched.start()
