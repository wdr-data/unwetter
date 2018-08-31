#!/user/bin/env python3.6

from io import BytesIO
from zipfile import ZipFile

import iso8601
from pymongo import MongoClient
import requests
import xmltodict


DWD_URL = 'https://opendata.dwd.de/weather/alerts/cap/DISTRICT_EVENT_STAT/Z_CAP_C_EDZW_LATEST_PVW_STATUS_PREMIUMEVENT_DISTRICT_DE.zip'
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

mongo_client = MongoClient()
mongo_db = mongo_client.unwetter
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

def main():

    events = [parse_xml(event) for event in load_dwd_xml_events()]

    from pprint import pprint
    
    for event in events:
        if collection.count_documents({'id': event['id']}):
            continue
        collection.insert_one(event)
        pprint(event)

if __name__ == '__main__':
    main()
