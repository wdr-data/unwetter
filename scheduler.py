#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""

from apscheduler.schedulers.blocking import BlockingScheduler

from unwetter import db, slack, generate

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def update_db():
    """
    You should not do actual work in the scheduler.
    For now, we do it anyways.
    """
    print('Running update job')
    new_events = db.update()
    for event in new_events:
        slack.send_to_slack(generate.description(event))


sched.start()
