#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""

from time import sleep

from apscheduler.schedulers.blocking import BlockingScheduler

from unwetter import db, slack, wina
from unwetter.config import filter_event


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
        if filter_event(event) and event['has_changes']:
            filtered.append(event)
        else:
            if event['msg_type'] == 'Alert':
                continue

            latest_reference = db.latest_reference(event['references'])
            if latest_reference and filter_event(latest_reference):
                filtered.append(event)

    if not filtered:
        return

    wina.upload([event['id'] for event in filtered])

    for event in filtered:
        print(f'Sending event {event["id"]} to Slack')
        slack.post_event(event)
        sleep(1)


sched.start()
