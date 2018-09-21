#!/user/bin/env python3.6

from feedgen.feed import FeedGenerator 
from flask import Flask, Response, request, jsonify

from unwetter import db, generate, wina as wina_gen
from unwetter.config import SEVERITY_FILTER, STATES_FILTER


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
    for event in db.query(SEVERITY_FILTER, STATES_FILTER):
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


@app.route('/slack/event')
def slack_event():
    if request.args.get('challenge'):
        return request.args.get('challenge')
    else:
        return ''


@app.route('/test')
def test():
    return 'OK'


if __name__ == '__main__':
    db.update()
