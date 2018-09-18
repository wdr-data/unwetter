#!/user/bin/env python3.6

import logging
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


def last_updated():
    return collection.find_one({'id': '_last_updated'})['at']


def update():

    last_modified_dwd = dwd.last_modified()
    last_updated_db = last_updated()

    if not last_updated_db:
        logging.info('No "_last_updated" timestamp found in DB, creating one now')
        collection.insert_one({'id': '_last_updated', 'at': last_modified_dwd})
    elif last_updated_db == last_modified_dwd:
        logging.info('API has not been updated')
        return
    else:
        logging.info('Updating DB')
        collection.replace_one(
            {'id': '_last_updated'}, {'id': '_last_updated', 'at': last_modified_dwd})

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
