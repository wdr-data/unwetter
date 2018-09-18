#!/user/bin/env python3.6

import os

import pymongo
from pymongo import MongoClient

from . import dwd

try:
    MONGODB_URI = os.environ['MONGODB_URI']
    mongo_client = MongoClient(MONGODB_URI)
    mongo_db = mongo_client.get_database()
except KeyError:
    mongo_db = MongoClient().unwetter

collection = mongo_db.events
collection_meta = mongo_db.events_meta


def last_updated():
    try:
        return collection_meta.find_one({'id': 'last_updated'})['at']
    except TypeError:
        return None


def update():

    last_modified_dwd = dwd.last_modified()
    last_updated_db = last_updated()

    if not last_updated_db:
        print('No "last_updated" timestamp found in DB, creating one now')
        collection_meta.insert_one({'id': 'last_updated', 'at': last_modified_dwd})
    elif last_updated_db == last_modified_dwd:
        print('API has not been updated')
        return
    else:
        print('API has been updated, updating DB...')
        collection_meta.replace_one(
            {'id': 'last_updated'}, {'id': 'last_updated', 'at': last_modified_dwd})

    events = [dwd.parse_xml(event) for event in dwd.load_dwd_xml_events()]

    from pprint import pprint

    for event in events:
        if collection.count_documents({'id': event['id']}):
            continue
        collection.insert_one(event)
        pprint(event)


def query(severities, states, limit=50):
    filter = {
        'severity': {'$in': severities},
    }

    if len(states) == 1:
        filter['states'] = states[0]
    else:
        filter['$or'] = [{'states': state} for state in states]

    return collection.find(filter).sort([('sent', pymongo.DESCENDING)]).limit(limit)


def clear():
    """
    Reset database
    """
    collection.drop()
