#!/user/bin/env python3.6

import os

from slackclient import SlackClient

from unwetter import generate

# Set up Slack client
# Based on https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

SLACK_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
CHANNEL = os.environ.get('SLACK_CHANNEL')
CLIENT = SlackClient(SLACK_TOKEN)


def post_event(event):
    post_message(generate.description(event, short=True), [
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


def post_message(message, attachments=None, private=None, channel=CHANNEL):
    """
    Send message with attachments to Slack on channel. Set 'private' to a user ID to send a message
    that only that user can see. Set 'channel' to a specific ID to send in a channel different from
    the default channel.
    """
    if not private:
        CLIENT.api_call(
            'chat.postMessage',
            channel=channel,
            text=message,
            attachments=attachments,
        )
    else:
        CLIENT.api_call(
            'chat.postEphemeral',
            channel=channel,
            user=private,
            text=message,
            attachments=attachments,
        )
