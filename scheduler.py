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
@slack.report_errors
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
        if (filter_event(event)
                and (event['msg_type'] == 'Alert' or any(event['has_changes'].values()))):
            filtered.append(event)
        else:
            if event['msg_type'] == 'Alert':
                continue

            old_events = db.by_ids(event['references'])
            if any(filter_event(old_event) and
                   (old_event['msg_type'] == 'Alert' or any(old_event['has_changes'].values()))
                   for old_event in old_events):
                filtered.append(event)

    if not filtered:
        return

    wina.upload([event['id'] for event in filtered])

    for event in filtered:
        print(f'Sending event {event["id"]} to Slack')
        slack.post_event(event)
        sleep(1)


sched.start()
