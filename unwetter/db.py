#!/user/bin/env python3.6

import os
from functools import lru_cache

import pymongo
import pytz
from bson import CodecOptions
from pymongo import MongoClient


try:
    MONGODB_URI = os.environ['MONGODB_URI']
    mongo_client = MongoClient(MONGODB_URI)
    mongo_db = mongo_client.get_database()
except KeyError:
    mongo_db = MongoClient().unwetter

collection = mongo_db.events.with_options(codec_options=CodecOptions(
    tz_aware=True,
    tzinfo=pytz.timezone('Europe/Berlin'),
))

collection_meta = mongo_db.events_meta.with_options(codec_options=CodecOptions(
    tz_aware=True,
    tzinfo=pytz.timezone('Europe/Berlin'),
))


@lru_cache(maxsize=32)
def by_id(id):
    return collection.find_one({'id': id})


def by_ids(ids):
    return collection.find({'id': {'$in': ids}})


def last_updated():
    """
    :return: The datetime when the event database was last updated with new data from the API
    """
    try:
        return collection_meta.find_one({'id': 'last_updated'})['at']
    except TypeError:
        return None


def update():
    """
    Download the latest events from the API and update the database, if necessary
    """
    # Local import to prevent circular dependency
    from . import dwd

    last_modified_dwd = dwd.last_modified()
    last_updated_db = last_updated()

    print('Last modified:', last_modified_dwd)
    print('Last updated:', last_updated_db)

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

    xmls = dwd.load_dwd_xml_events()

    new_events = []

    for id, xml in xmls.items():
        if collection.count_documents({'id': id}):
            print('Ignoring existing event with id', id)
            continue

        event = dwd.parse_xml(xml)

        if event['status'] == 'Test':
            continue

        collection.insert_one(event)
        new_events.append(event)

    return new_events


def query(severities, states, urgencies, limit=50):
    """

    :param severities: List of severities allowed (eg. ['Severe', 'Extreme'])
    :param states: List of states (eg. ['NW'])
    :param urgencies: List of urgencies (eg. ['Immediate'])
    :param limit: Number of results
    :return: DB Cursor with the results
    """

    filter = {
        'severity': {'$in': severities},
        'urgency': {'$in': urgencies},
    }

    if len(states) == 1:
        filter['states'] = states[0]
    else:
        filter['$or'] = [{'states': state} for state in states]

    return collection.find(filter).sort([('sent', pymongo.DESCENDING)]).limit(limit)


@lru_cache(maxsize=32)
def latest_reference(references, ):
    """

    :param references: List of IDs
    :return: A single event
    """

    if len(references) > 1:
        filter = {
            'id': {'$in': references},
        }
    else:
        filter = {
            'id': references[0],
        }

    filter['has_changes'] = True

    try:
        return collection.find(filter).sort([('sent', pymongo.DESCENDING)])[0]
    except IndexError:
        print(f'Could not find object for references')
        return None


def clear():
    """
    Reset database
    """
    collection.drop()
    collection_meta.drop()
