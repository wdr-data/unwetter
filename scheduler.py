#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""

from time import sleep

from apscheduler.schedulers.blocking import BlockingScheduler

from unwetter import db, slack, wina
from unwetter.config import SEVERITY_FILTER, STATES_FILTER, URGENCY_FILTER


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
    new_events = [
        e for e in new_events
        if e['severity'] in SEVERITY_FILTER 
        and e['urgency'] in URGENCY_FILTER 
        and len(set(e['states']) - set(STATES_FILTER)) < len(e['states'])
    ]

    if not new_events:
        return

    wina.upload([event['id'] for event in new_events])

    for event in new_events:
        print(f'Sending event {event["id"]} to Slack')
        slack.post_event(event)
        sleep(1)


sched.start()
