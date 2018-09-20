#!/user/bin/env python3.6

import os

from slackclient import SlackClient


# Set up Slack client (based on https://www.fullstackpython.com/blog/build-first-slack-bot-python.html)
slack_token = os.environ.get('SLACK_BOT_TOKEN')
slack_client = SlackClient(slack_token)


def send_to_slack(message, channel):  # testing channel: CCKQ5BX5G
    """
    Send message to Slack on channel
    """
    if slack_client.rtm_connect(with_team_state=False):  # Read and print the bot's user ID by calling Web API method `auth.test` to check if connected to Slack
        ta_id = slack_client.api_call("auth.test")["user_id"]
        print(f'Themen-Agent connected and running as User-ID {ta_id}!')
        
        slack_client.api_call(
            'chat.postMessage',
            channel=channel,
            text=message
            )

        print(f'Message sent to Slack: {message}')
        
    else:
print('Connection to Slack failed.')