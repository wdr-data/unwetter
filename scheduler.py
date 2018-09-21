#!/user/bin/env python3.6

"""
Contains regular jobs like updating the DB
"""

from time import sleep

from apscheduler.schedulers.blocking import BlockingScheduler

from unwetter import db, slack, generate, wina
from unwetter.config import SEVERITY_FILTER, STATES_FILTER


sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=1)
def update_db():
    """
    You should not do actual work in the scheduler.
    For now, we do it anyways.
    """
    print('Running update job')
    new_events = db.update()

    # Filter new_events by SEVERITY_FILTER and STATES_FILTER
    new_events = [
        e for e in new_events
        if e['severity'] in SEVERITY_FILTER 
        and len(set(e['states']) - set(STATES_FILTER)) < len(e['states'])
    ]

    if not new_events:
        return

    wina.upload([event['id'] for event in new_events])

    for event in new_events:
        print(f'Sending event {event["id"]} to Slack')
        slack.post_message(generate.description(event, short=True), [
            {
                "fallback": "Textvorschläge generieren",
                "title": "Textvorschläge generieren",
                "text": "Textvorschläge für Twitter und den TV-Crawl werden im WDR automatisch "
                        "generiert.",
                "callback_id": event['id'],
                "color": "#3AA3E3",
                "attachment_type": "default",
                "actions": [
                    {
                        "name": "twitter",
                        "text": ":bird: Twitter",
                        "type": "button",
                        "value": "twitter",
                    },
                    {
                        "name": "crawl",
                        "text": ":tv: TV-Crawl",
                        "type": "button",
                        "value": "crawl",
                    },
                    {
                        "name": "dwd",
                        "text": ":cloud: DWD Meldung",
                        "type": "button",
                        "value": "dwd",
                    },
                ],
            },
        ])
        sleep(1)


sched.start()
