#!/user/bin/env python3.6

from feedgen.feed import FeedGenerator 
from flask import Flask, Response

from unwetter import db, generate


# Configuration
SEVERITY_FILTER = ['Minor', 'Moderate', 'Severe', 'Extreme']  # Which degrees of severity to track
STATES_FILTER = ['NW', 'BY', 'BW', 'SH']  # Which states to track


with open('assets/wina_template.xml', 'r') as fp:
    WINA_TEMPLATE = fp.read()

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
        fe = fg.add_entry()
        fe.id(event['id'])
        fe.title(generate.title(event))
        fe.link(href=f'{URL_BASE}wina/{event["id"]}')
        fe.description(generate.description(event).replace('\n', '<br>'))

    r = Response(fg.rss_str(pretty=True), mimetype='application/rss+xml')
    r.headers['Content-Type'] = "text/xml; charset=utf-8"
    return r


@app.route('/wina/<id>')
def wina(id):
    event = db.collection.find_one({'id': id})
    sent = event['sent'].strftime('%Y%m%dT%H%M%S,000')  # 20180827T130547,000

    wina_xml = WINA_TEMPLATE.format(
        sent=sent,
        title=generate.title(event),
        text=f'{generate.description(event)} \n {generate.more_info_text()}'
    )

    r = Response(
        wina_xml.encode('iso-8859-1', errors='xmlcharrefreplace'), mimetype='application/xml')
    r.headers['Content-Type'] = "text/xml; charset=iso-8859-1"

    return r


@app.route('/test')
def test():
    return 'OK'


if __name__ == '__main__':
    db.update()
