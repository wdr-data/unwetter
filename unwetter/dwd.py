#!/user/bin/env python3.6

from io import BytesIO
from datetime import datetime
from zipfile import ZipFile

import iso8601
import requests
import xmltodict
import pytz

from . import regions
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
    ).replace(tzinfo=pytz.UTC)


def load_dwd_xml_events():
    """
    Load ZIP-file from DWD OpenData-API, unzip it, return list of events in XML
    """
    data_zip = BytesIO()
    data_zip.write(requests.get(API_URL).content)
    data_zip.seek(0)
    data_zip = ZipFile(data_zip)
    return [
        data_zip.read(name).decode('utf-8')
        for name in data_zip.namelist()
    ]


def parse_polygon(polygon):
    return [[float(x) for x in pair.split(',')] for pair in polygon.split(' ')]


def district_from_commune(commune):
    common_id = commune['warn_cell_id'][-8:-3]
    warn_cell_id = f'1{common_id}000'
    name = DISTRICTS[warn_cell_id]
    return name, warn_cell_id


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

    event['states'] = list(states)

    event['regions'] = regions.best_match([area['name'] for area in event['districts']])

    if 'references' in xml_dict:
        event['references'] = [ref.split(',')[1] for ref in xml_dict['references'].split(' ')]

    return event


def state_for_cell_id(warn_cell_id):
    return STATE_IDS[int(str(warn_cell_id)[1:3])]
