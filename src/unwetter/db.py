#!/user/bin/env python3.6

import os
from functools import lru_cache

import pymongo

from . import sentry


try:
    MONGODB_URI = os.environ['MONGODB_URI']
    mongo_client = pymongo.MongoClient(MONGODB_URI)
    mongo_db = mongo_client.get_database()
except KeyError:
    mongo_db = pymongo.MongoClient().unwetter

collection = mongo_db.events
collection_meta = mongo_db.events_meta


@lru_cache(maxsize=32)
def by_id(id):
    event = collection.find_one({'id': id})

    if event and 'special_type' not in event:
        from . import dwd
        event['special_type'] = dwd.special_type(event, by_ids(event.get('references', [])))

    return event


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

        try:
            event = dwd.parse_xml(xml)
        except Exception as e:
            print('Failed to parse event with ID', id)
            sentry.sentry_sdk.capture_exception(e)
            continue

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

    events = collection.find(filter).sort([('sent', pymongo.DESCENDING)]).limit(limit)

    for event in events:
        if 'special_type' not in event:
            from . import dwd
            event['special_type'] = dwd.special_type(event, by_ids(event.get('references', [])))
        yield event


def load_published(limit=50):
    """
    Get `limit` events marked published

    :param limit: Number of results
    :return: DB curser with results
    """

    filter = {
        'published': True,
    }

    return collection.find(filter).sort([('sent', pymongo.DESCENDING)]).limit(limit)


def publish(ids):
    '''
    Create and Set Key `published` = True
    :param ids: List of ids
    '''

    collection.update_many({"id": {"$in": ids}}, {"$set": {"published": True}})



def clear():
    """
    Reset database
    """
    collection.drop()
    collection_meta.drop()
