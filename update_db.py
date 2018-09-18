#!/user/bin/env python3.6

"""
This file should be scheduled in Heroku using the Scheduler Add-On
https://devcenter.heroku.com/articles/scheduler

The schedule should be set to one every 60 seconds
"""

from unwetter import db

if __name__ == '__main__':
    db.update()
