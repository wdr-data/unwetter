#!/user/bin/env python3.6

import os
from time import time

from slackclient import SlackClient

from unwetter import generate
from .map import COLORS
from unwetter.generate import helpers

# Set up Slack client
# Based on https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

SLACK_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
CHANNEL = os.environ.get('SLACK_CHANNEL')
CLIENT = SlackClient(SLACK_TOKEN)


def post_event(event):
    response = post_message(
        '', attachments=[
            {
                'fallback': generate.title(event),
                'color': COLORS['SEVERITIES'][event['severity']],
                'title': generate.title(event),
                'text': generate.dates(event),
                'fields': [
                    {
                        'title': generate.severities[event['severity']],
                        'value': generate.parameters(event),
                        'short': False,
                    },
                ],
                'image_url': generate.urls.map(event),
                'callback_id': event['id'],
                'footer': 'Details zur Meldung im Thread',
                'ts': int(time())
            }
        ]
    )

    thread_ts = response['ts']

    instruction = helpers.pad('Verhaltenshinweise: {event["instruction"]}') if event['instruction'] else ''
    post_message(
        f'''
Regionale Zuordnung: {generate.region_list(event)}
{instruction}
{event['description']}
        '''.strip(),
        thread_ts=thread_ts,
        attachments=[
            {
                "fallback": "Textvorschläge",
                "title": "Textvorschläge",
                "text": "Von der UWA-Redaktion automatisch generierte Textvorschläge",
                "callback_id": event['id'],
                "color": "#000000",
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
                        "name": "info",
                        "text": ":question: Infos zum Projekt",
                        "type": "button",
                        "value": "info",
                    },
                ],
            },
        ]
    )




def post_event_old(event):
    post_message(generate.description(event, short=True), attachments=[
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
                {
                    "name": "info",
                    "text": ":question: Infos zum Projekt",
                    "type": "button",
                    "value": "info",
                },
            ],
        },
    ])


def post_message(message, *, private=False, channel=CHANNEL, **kwargs):
    """
    Send message with attachments to Slack on channel. Set 'private' to a user ID to send a message
    that only that user can see. Set 'channel' to a specific ID to send in a channel different from
    the default channel.
    """
    if not private:
        return CLIENT.api_call(
            'chat.postMessage',
            channel=channel,
            text=message,
            **kwargs,
        )
    else:
        return CLIENT.api_call(
            'chat.postEphemeral',
            channel=channel,
            user=private,
            text=message,
            **kwargs,
        )
