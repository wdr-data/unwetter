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

    if db.warn_events_memo() and not db.current_events(all_severities=False):
        # Send notification
        db.set_warn_events_memo(False)


sched.start()
