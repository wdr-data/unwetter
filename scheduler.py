#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""

from time import sleep

from apscheduler.schedulers.blocking import BlockingScheduler

from unwetter import db, slack, generate, wina

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def update_db():
    """
    You should not do actual work in the scheduler.
    For now, we do it anyways.
    """
    print('Running update job')
    new_events = db.update()

    if not new_events:
        return

    wina.upload([event['id'] for event in new_events])

    for event in new_events:
        print(f'Sending event {event["id"]} to Slack')
        slack.send_to_slack(generate.description(event))
        sleep(1)


sched.start()
