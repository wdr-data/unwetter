#!/user/bin/env python3.6

import os

from slackclient import SlackClient


# Set up Slack client
# Based on https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
SLACK_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
CHANNEL = os.environ.get('SLACK_CHANNEL')
CLIENT = SlackClient(SLACK_TOKEN)


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
