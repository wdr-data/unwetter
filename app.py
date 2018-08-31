#!/user/bin/env python3.6

from io import BytesIO
import os
from zipfile import ZipFile

from feedgen.feed import FeedGenerator 
from flask import Flask, Response
import iso8601
import pymongo
from pymongo import MongoClient
import requests
import xmltodict

from wina_template import WINA_TEMPLATE


DWD_URL = 'https://opendata.dwd.de/weather/alerts/cap/DISTRICT_EVENT_STAT/Z_CAP_C_EDZW_LATEST_PVW_STATUS_PREMIUMEVENT_DISTRICT_DE.zip'
SEVERITY_FILTER = ['Moderate', 'Severe', 'Extreme']  # Which degrees of severity to track
STATES_FILTER = ['NW', 'BY', 'BW']  # Which states to track
STATE_IDS = {
    1: 'SH',
    2: 'HH',
    3: 'NI',
    4: 'HB',
    5: 'NW',
    6: 'HE',
    7: 'RP',
    8: 'BW',
    9: 'BY',
    10: 'SL',
    11: 'BE',
    12: 'BB',
    13: 'MV',
    14: 'SN',
    15: 'ST',
    16: 'TH',
}
URL_BASE = 'https://unwetter-bot.herokuapp.com/'

app = Flask(__name__)

try:
    MONGODB_URI = os.environ['MONGODB_URI']
    mongo_client = MongoClient(MONGODB_URI)
    mongo_db = mongo_client.get_database()
except KeyError:
    mongo_db = MongoClient().unwetter

collection = mongo_db.events


def load_dwd_xml_events():
    """
    Load ZIP-file from DWD OpenData-API, unzip it, return list of events in XML
    """
    data_zip = BytesIO()
    data_zip.write(requests.get(DWD_URL).content)
    data_zip.seek(0)
    data_zip=ZipFile(data_zip)
    return [
        data_zip.read(name).decode('utf-8') 
        for name in data_zip.namelist()
    ]


def parse_xml(xml):
    """
    Parse event from XML to dictionary
    """
    xml_dict = xmltodict.parse(xml)['alert']
    event = {}
    fields = {
        'identifier': 'id',
        'sender': 'sender',
        'sent': 'sent',
        'status': 'status',
        'msgType' : 'msg_type',
    }
    datetime_fields = ['sent']
    for field_xml, field_json in fields.items():
        event[field_json] = xml_dict.get(field_xml)
        if field_json in datetime_fields and event[field_json]:
            event[field_json] = iso8601.parse_date(event[field_json])

    info_fields = {
        'event': 'event',
        'responseType': 'response_type',
        'urgency': 'urgency',
        'severity': 'severity',
        'certainty': 'certainty',
        'effective': 'effective',
        'onset': 'onset',
        'expires': 'expires',
        'headline': 'headline',
        'description': 'description',
        'instruction': 'instruction',       
    }

    datetime_fields = ['effective', 'onset', 'expires']

    for field_xml, field_json in info_fields.items():
        event[field_json] = xml_dict['info'].get(field_xml)
        if field_json in datetime_fields and event[field_json]:
            event[field_json] = iso8601.parse_date(event[field_json])

    if isinstance(xml_dict['info']['area'], dict):
        xml_dict['info']['area'] = [xml_dict['info']['area']]

    states = set()
    
    for area in xml_dict['info']['area']:
        if isinstance(area['geocode'], dict):
            area['geocode'] = [area['geocode']]
        for geocode in area['geocode']:
            if geocode['valueName'] == 'WARNCELLID':
                area['_warn_cell_id'] = geocode['value']
                state_id = int(geocode['value'][1:3])
                states.add(state_id)

    event['areas'] = [
        {
            'name': area['areaDesc'],
            'warn_cell_id': area['_warn_cell_id'],
        } 
        for area in xml_dict['info']['area']
    ]

    event['states'] = [STATE_IDS[state_id] for state_id in states]

    return event


def clear_db():
    """
    Reset database
    """
    collection.drop()


def make_title(event):
    if event['msg_type'] == 'Alert':
        prefix = '🚨 Neue Meldung'
    elif event['msg_type'] == 'Update':
        prefix = '🔁 Meldung aktualisiert'
    elif event['msg_type'] == 'Cancel':
        prefix = '🚫 Meldung aufgehoben'
    else:
        prefix = '⁉️ Unbekannter Meldungstyp'
    
    return f'{prefix}: {event["headline"]}'


def make_description(event):
    severities = {
        'Minor': 'Wetterwarnung',
        'Moderate': 'Markante Wetterwarnung',
        'Severe': '🔴 Amtliche Unwetterwarnung',
        'Extreme': '🔴 Amtliche Extreme Unwetterwarnung',
    }
    return f'''
Warnstufe: {severities[event['severity']]} 
Orte: {', '.join(area['name'] for area in event['areas'])}
Gültig von {event['onset'].strftime('%d.%m.%Y %H:%M:%S')} bis {event['expires'].strftime('%d.%m.%Y %H:%M:%S') if event['expires'] else 'Nicht angegeben'}
Warnmeldung: {event['description']}
    '''.strip()


@app.route('/feed.rss')
def feed():
    update_db()
    fg = FeedGenerator()
    fg.id('https://unwetter-bot.herokuapp.com/')
    fg.title('Unwetter Testfeed')
    fg.link(href='https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html', rel='alternate')
    fg.subtitle('This is a test feed!')
    fg.link(href='https://unwetter-bot.herokuapp.com/feed.rss', rel='self')
    fg.language('de')
    filter = { 
        'severity': {'$in': SEVERITY_FILTER}, 
    }
    if len(STATES_FILTER) == 1: 
        filter['states'] = STATES_FILTER[0]
    else:
        filter['$or'] = [{'states': state} for state in STATES_FILTER]
    
    # Iterate over the most recent 50 events matching filter
    for event in collection.find(filter).sort([('sent', pymongo.DESCENDING)]).limit(50):
        fe = fg.add_entry()
        fe.id(event['id'])
        fe.title(make_title(event))
        fe.link(href=f'{URL_BASE}wina/{event["id"]}')
        fe.description(make_description(event).replace('\n', '<br>'))
    
    return Response(fg.rss_str(pretty=True), mimetype='application/rss+xml')


@app.route('/wina/<id>')
def wina(id):
    event = collection.find_one({'id': id})
    sent = event['sent'].strftime('%Y%m%dT%H%M%S,000')  # 20180827T130547,000
    wina = WINA_TEMPLATE.format(sent=sent, title=make_title(event), text=make_description(event))
    r = Response(wina.encode('iso-8859-1', errors='xmlcharrefreplace'), mimetype='application/xml')
    r.headers['Content-Type'] = "text/xml; charset=iso-8859-1"
    return r


@app.route('/test')
def test():
    return 'OK'

def update_db():
    
    events = [parse_xml(event) for event in load_dwd_xml_events()]

    from pprint import pprint
    
    for event in events:
        event['id'] += 'foo'
        if collection.count_documents({'id': event['id']}):
            continue
        collection.insert_one(event)
        pprint(event)

if __name__ == '__main__':
    update_db()
