#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""

from apscheduler.schedulers.blocking import BlockingScheduler

from unwetter import db

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def update_db():
    """
    You should not do actual work in the scheduler.
    For now, we do it anyways.
    """
    print('Running update job')
    db.update()


sched.start()
