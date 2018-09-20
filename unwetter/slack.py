#!/user/bin/env python3.6

import os

from slackclient import SlackClient


# Set up Slack client (based on https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)
slack_token = os.environ.get('SLACK_BOT_TOKEN')
channel = os.environ.get('SLACK_CHANNEL')
slack_client = SlackClient(slack_token)


def send_to_slack(message):
    """
    Send message to Slack on channel
    """
    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text=message,
    )
