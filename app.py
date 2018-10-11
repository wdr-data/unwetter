#!/user/bin/env python3.6
from datetime import datetime
import os

from feedgen.feed import FeedGenerator
from flask import Flask, Response, request, json

from unwetter import db, generate, wina as wina_gen, slack, twitter
from unwetter.config import SEVERITY_FILTER, STATES_FILTER, URGENCY_FILTER


URL_BASE = 'https://unwetter-bot.herokuapp.com/'
app = Flask(__name__)


@app.route('/feed.rss')
def feed():
    fg = FeedGenerator()
    fg.id('https://unwetter-bot.herokuapp.com/')
    fg.title('Unwetter Testfeed')
    fg.link(href='https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html', rel='alternate')
    fg.subtitle('This is a test feed!')
    fg.link(href='https://unwetter-bot.herokuapp.com/feed.rss', rel='self')
    fg.language('de')

    # Iterate over the most recent 50 events matching filter
    for event in db.query(SEVERITY_FILTER, STATES_FILTER, URGENCY_FILTER):
        fe = fg.add_entry(order='append')
        fe.id(event['id'])
        fe.title(generate.headline(event))
        fe.link(href=f'{URL_BASE}wina/{event["id"]}')
        fe.published(event['sent'])
        fe.description(generate.description(event).replace('\n', '<br>'))

    r = Response(fg.rss_str(pretty=True), mimetype='application/rss+xml')
    r.headers['Content-Type'] = "text/xml; charset=utf-8"
    return r


@app.route('/wina/<id>')
def wina(id):
    r = Response(wina_gen.from_id(id), mimetype='application/xml')
    r.headers['Content-Type'] = "text/xml; charset=iso-8859-1"

    return r


@app.route('/slack/event', methods=['GET', 'POST'])
def slack_event():
    data = request.json or request.form

    if not data:
        return ''

    if data.get('challenge'):
        return data.get('challenge')

    payload = data.get('payload')

    if payload:
        data = json.loads(payload)

    print(data)

    actions = data.get('actions')

    for action in actions:
        id = data['callback_id']
        channel_id = data['channel']['id']
        user_id = data['user']['id']

        response = None
        attachments = None

        if action['name'] == 'twitter':
            response = 'Vorschlag Tweet:\n' + generate.tweet(db.by_id(id))
            attachments = [
                {
                    "fallback": "Aktionen",
                    "title": "Aktionen",
                    "callback_id": id,
                    "color": "#3AA3E3",
                    "attachment_type": "default",
                    "actions": [
                        {
                            "name": "send_tweet",
                            "text": ":bird: Tweet senden",
                            "type": "button",
                            "value": data['message_ts'],
                        },
                    ],
                },
            ]
        elif action['name'] == 'send_tweet':
            message_ts = action['value']
            start = datetime.utcfromtimestamp(float(message_ts))
            end = datetime.utcnow()
            elapsed = str(end - start)
            elapsed = elapsed.split('.')[0].replace('days', 'Tage').replace('day', 'Tag')

            demo_handle = os.environ["TWITTER_DEMO_HANDLE"]

            tweet = f'In {elapsed} informiert UWA dich über das Unwetter @{demo_handle}'

            try:
                twitter.api.update_status(tweet)

                response = 'Tweet gesendet :+1:'
                user_id = None  # Send to everyone
            except:
                response = 'Tweet senden fehlgeschlagen :thinking_face:'
                slack.post_message(response, private=user_id, channel=channel_id)
                raise

        elif action['name'] == 'crawl':
            response = 'Vorschlag TV-Crawl:\n' + generate.crawl(db.by_id(id))
        elif action['name'] == 'dwd':
            response = 'Offizielle Meldung des DWD:\n' + db.by_id(id)['description']
        elif action['name'] == 'info':
            response = f'''
Diese Meldung basiert auf offiziellen Informationen des Deutschen Wetterdienstes:
https://www.dwd.de/DE/wetter/warnungen_gemeinden/warnkarten/warnWetter_nrw_node.html?bundesland=nrw

Die Bereitstellung dieser Information ist ein Projekt des Digitalen Wandels und wird aktiv weiterentwickelt.
Informationen und Kontakt: {os.environ["WDR_PROJECT_INFO_URL"]}
            '''.strip()

        if response:
            slack.post_message(
                response, private=user_id, channel=channel_id, attachments=attachments)

    return ''


@app.route('/test')
def test():
    return 'OK'


if __name__ == '__main__':
    db.update()
