#!/user/bin/env python3.6

from io import BytesIO
from datetime import datetime, timedelta
from os.path import splitext
import re
from zipfile import ZipFile

import iso8601
import requests
import xmltodict
import pytz

from . import regions, db, config
from .data.districts import DISTRICTS


API_URL = 'https://opendata.dwd.de/weather/alerts/cap/' \
          'COMMUNEUNION_EVENT_STAT/Z_CAP_C_EDZW_LATEST_PVW_STATUS_PREMIUMEVENT_COMMUNEUNION_DE.zip'

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


def last_modified():
    """
    Checks when the last update was released
    :return: A datetime object
    """
    return datetime.strptime(
        requests.head(API_URL).headers['Last-Modified'],
        '%a, %d %b %Y %H:%M:%S %Z',
    )


def load_dwd_xml_events():
    """
    Load ZIP-file from DWD OpenData-API, unzip it, return list of events in XML
    """
    data_zip = BytesIO()
    data_zip.write(requests.get(API_URL).content)
    data_zip.seek(0)
    data_zip = ZipFile(data_zip)
    return {
        splitext(name)[0]: data_zip.read(name).decode('utf-8')
        for name in data_zip.namelist()
    }


def parse_polygon(polygon):
    return [[float(x) for x in pair.split(',')] for pair in polygon.split(' ')]


def district_from_commune(commune):
    common_id = commune['warn_cell_id'][-8:-3]
    warn_cell_id = f'1{common_id}000'
    name = DISTRICTS[warn_cell_id]
    return name, warn_cell_id


def is_changed(event, old_event):
    """
    Compares two events and discerns if it has changes that should trigger a push
    :param event:
    :param old_event:
    :return: bool
    """

    # Simple changes
    if any(event.get(field) != old_event.get(field) for field in ['severity', 'certainty']):
        return True

    # Notify about big hail sizes
    if 'Hagel' not in event['parameters']:
        if event['event'].replace(' und HAGEL', '') != old_event['event'].replace(' und HAGEL', ''):
            return True
    else:
        hail_re = r'^.*?(\d+).*?cm'
        hail_size_now = int(re.match(hail_re, event['parameters']['Hagel']).group(1))
        hail_size_before = int(re.match(hail_re, old_event['parameters'].get('Hagel', '0 cm')).group(1))

        if hail_size_now >= 3 > hail_size_before:
            return True
        elif event['event'].replace(' und HAGEL', '') != old_event['event'].replace(' und HAGEL', ''):
            return True

    # Changes in time
    if (abs(event['onset'] - event['sent']) > timedelta(minutes=2)
            and event['sent'] - event['onset'] < timedelta(minutes=2)
            and old_event['onset'] != event['onset']):
        return True

    elif old_event['expires'] != event['expires']:
        return True

    # New regions
    if len(set(r[0] for r in event['regions']) - set(r[0] for r in old_event['regions'])) > 0:
        return True

    # New districts
    districts_now = {
        district['name'] for district in event['districts']
        if state_for_cell_id(district['warn_cell_id']) in config.STATES_FILTER
    }
    districts_before = {
        district['name'] for district in old_event['districts']
        if state_for_cell_id(district['warn_cell_id']) in config.STATES_FILTER
    }
    added = districts_now - districts_before

    if len(districts_before) <= 3 and added:
        return True

    return False


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
        'msgType': 'msg_type',
    }
    datetime_fields = ['sent']
    for field_xml, field_json in fields.items():
        event[field_json] = xml_dict.get(field_xml)
        if field_json in datetime_fields and event[field_json]:
            event[field_json] = iso8601.parse_date(event[field_json]).astimezone(pytz.utc).replace(tzinfo=None)

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
            event[field_json] = iso8601.parse_date(event[field_json]).astimezone(pytz.utc).replace(tzinfo=None)

    for tag in ('area', 'parameter'):
        try:
            if isinstance(xml_dict['info'][tag], dict):
                xml_dict['info'][tag] = [xml_dict['info'][tag]]
        except KeyError:
            xml_dict['info'][tag] = []

    event['parameters'] = {
        param['valueName']: param['value']
        for param in xml_dict['info']['parameter']
    }

    states = set()

    poly_areas = []
    commune_areas = []

    for area in xml_dict['info']['area']:
        area['geocode'] = area.get('geocode', [])

        if isinstance(area['geocode'], dict):
            area['geocode'] = [area['geocode']]

        area['_polygons'] = area.get('polygon', [])
        if isinstance(area['_polygons'], str):
            area['_polygons'] = [area['_polygons']]

        area['_exclude_polygons'] = []
        for geocode in area['geocode']:
            if geocode['valueName'] == 'WARNCELLID':
                area['_warn_cell_id'] = geocode['value']
                states.add(state_for_cell_id(geocode['value']))

            if geocode['valueName'] == 'EXCLUDE_POLYGON':
                area['_exclude_polygons'].append(geocode['value'])

        area['_polygons'] = [parse_polygon(poly) for poly in area['_polygons']]
        area['_exclude_polygons'] = [parse_polygon(poly) for poly in area['_exclude_polygons']]

        if area['areaDesc'] == 'polygonal event area':
            poly_areas.append(area)
        else:
            commune_areas.append(area)

    event['areas'] = [
        {
            'name': area['areaDesc'],
            'warn_cell_id': area['_warn_cell_id'],
        }
        for area in commune_areas
    ]

    event['geometry'] = [
        {
            'polygons': area['_polygons'],
            'exclude_polygons': area['_exclude_polygons'],
        }
        for area in poly_areas
    ]

    event['districts'] = []
    found_districts = set()
    for area in event['areas']:
        try:
            name, warn_cell_id = district_from_commune(area)
        except KeyError:
            # Some areas don't have a related district
            continue

        if warn_cell_id in found_districts:
            continue

        found_districts.add(warn_cell_id)

        event['districts'].append({
            'name': name,
            'warn_cell_id': warn_cell_id,
        })

    event['districts'] = sorted(event['districts'], key=lambda elem: elem['name'])

    event['states'] = sorted(states)

    event['regions'] = regions.best_match([area['name'] for area in event['districts']])

    if 'references' in xml_dict:
        event['references'] = [ref.split(',')[1] for ref in xml_dict['references'].split(' ')]

    if event['msg_type'] == 'Update':
        old_events = list(db.by_ids(event.get('extended_references', event['references'])))

        if not any(e['published'] for e in old_events):
            extended_references = set()
            extended_references.update(event.get('extended_references', event['references']))

            for old_event in old_events:
                if 'extended_references' in old_event:
                    extended_references.update(old_event['extended_references'])
                elif 'references' in old_event:
                    extended_references.update(old_event['references'])

            event['extended_references'] = sorted(extended_references, reverse=True)

            old_events = list(db.by_ids(event['extended_references']))

        event['has_changes'] = [
            {
                'id': old_event['id'],
                'changed': is_changed(event, old_event),
                'published': old_event['published'],
            }
            for old_event in old_events
        ]

        event['special_type'] = special_type(event, old_events)

    event['published'] = False

    return event


def state_for_cell_id(warn_cell_id):
    return STATE_IDS[int(str(warn_cell_id)[-8:-6])]


def special_type(event, references):
    if event['msg_type'] != 'Update':
        return

    if not config.filter_event(event):
        if any(ref.get('published') for ref in references):
            return 'Irrelevant'
        return

    if all(not ref.get('published') for ref in references):
        return 'UpdateAlert'
