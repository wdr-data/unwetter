#!/user/bin/env python3.6

import os
from functools import lru_cache
from datetime import datetime

import pymongo

from . import sentry, config, map


try:
    MONGODB_URI = os.environ["ORMONGO_RS_URL"]
    MONGODB_DATABASE = "uwa"
    MONGODB_USER = "uwa"
    MONGODB_PASSWORD = os.environ["ORMONGO_PASSWORD"]
    mongo_client = pymongo.MongoClient(
        MONGODB_URI,
        username=MONGODB_USER,
        password=MONGODB_PASSWORD,
        authSource=MONGODB_DATABASE,
        authMechanism="SCRAM-SHA-256",
        ssl=True,
    )
    mongo_db = mongo_client.get_database(MONGODB_DATABASE)
except KeyError:
    mongo_db = pymongo.MongoClient().unwetter

collection = mongo_db.events
collection_meta = mongo_db.events_meta


@lru_cache(maxsize=32)
def by_id(id):
    event = collection.find_one({"id": id})

    if event and "special_type" not in event:
        from . import dwd

        event["special_type"] = dwd.special_type(
            event, by_ids(event.get("references", []))
        )

    return event


def by_ids(ids):
    return collection.find({"id": {"$in": ids}})


def last_updated():
    """
    :return: The datetime when the event database was last updated with new data from the API
    """
    try:
        return collection_meta.find_one({"id": "last_updated"})["at"]
    except TypeError:
        return None


def warn_events_memo():
    try:
        return collection_meta.find_one({"id": "warn_events_memo"})["active"]
    except TypeError:
        return None


def set_warn_events_memo(active):
    collection_meta.replace_one(
        {"id": "warn_events_memo"},
        {"id": "warn_events_memo", "active": active},
        upsert=True,
    )


def breaking_memo():
    try:
        return collection_meta.find_one({"id": "breaking_memo"})["active"]
    except TypeError:
        return None


def set_breaking_memo(active):
    collection_meta.replace_one(
        {"id": "breaking_memo"}, {"id": "breaking_memo", "active": active}, upsert=True
    )


def update():
    """
    Download the latest events from the API and update the database, if necessary
    """
    # Local import to prevent circular dependency
    from . import dwd

    last_modified_dwd = dwd.last_modified()
    last_updated_db = last_updated()

    print("Last modified:", last_modified_dwd)
    print("Last updated:", last_updated_db)

    if not last_updated_db:
        print('No "last_updated" timestamp found in DB, creating one now')
        collection_meta.insert_one({"id": "last_updated", "at": last_modified_dwd})
    elif last_updated_db == last_modified_dwd:
        print("API has not been updated")
        return
    else:
        print("API has been updated, updating DB...")
        collection_meta.replace_one(
            {"id": "last_updated"}, {"id": "last_updated", "at": last_modified_dwd}
        )

    xmls = dwd.load_dwd_xml_events()

    new_events = []

    for id, xml in xmls.items():
        if collection.count_documents({"id": id}):
            print("Ignoring existing event with id", id)
            continue

        try:
            event = dwd.parse_xml(xml)
        except Exception as e:
            print("Failed to parse event with ID", id)
            sentry.sentry_sdk.capture_exception(e)
            continue

        if event["status"] == "Test":
            continue

        new_events.append(event)

    if new_events:
        collection.insert_many(new_events)

    return new_events


def query(severities, states, urgencies, filter=None):
    """

    :param severities: List of severities allowed (eg. ['Severe', 'Extreme'])
    :param states: List of states (eg. ['NW'])
    :param urgencies: List of urgencies (eg. ['Immediate'])
    :param limit: Number of results
    :return: DB Cursor with the results
    """

    if not filter:
        filter = {}

    filter.update(
        {
            "severity": {"$in": severities},
            "urgency": {"$in": urgencies},
        }
    )

    if len(states) == 1:
        filter["states"] = states[0]
    elif len(states) > 1:
        filter["$or"] = [{"states": state} for state in states]

    events = collection.find(filter).sort([("sent", pymongo.DESCENDING)])

    for event in events:
        if "special_type" not in event:
            from . import dwd

            event["special_type"] = dwd.special_type(
                event, by_ids(event.get("references", []))
            )
        yield event


def load_published(limit=50):
    """
    Get `limit` events marked published

    :param limit: Number of results
    :return: DB curser with results
    """

    filter = {
        "published": True,
    }

    return collection.find(filter).sort([("sent", pymongo.DESCENDING)]).limit(limit)


def publish(ids):
    """
    Create and Set Key `published` = True
    :param ids: List of ids
    """

    collection.update_many({"id": {"$in": ids}}, {"$set": {"published": True}})


def current_events(at=None, all_severities=True):
    if not at:
        at = datetime.utcnow()

    filter = {
        "expires": {"$gte": at},
        "effective": {"$lte": at},
    }

    results = query(
        ["Minor", "Moderate", "Severe", "Extreme"],
        [],
        ["Immediate"],
        filter=filter,
    )

    results = list(results)

    if not results:
        return []

    filteredResults = []
    all_refs = set()

    for result in results:
        all_refs.update(set(result.get("references", [])))

    for result in results:
        if len(set(result["states"]) - set(config.STATES_FILTER)) == len(
            result["states"]
        ):
            continue

        if not all_severities and result["severity"] not in config.SEVERITY_FILTER:
            continue

        if result["id"] in all_refs:
            continue

        filter = {
            "references": result["id"],
            "$or": [
                {"expires": {"$lte": at}},
                {"msg_type": "Cancel"},
            ],
        }

        double_check = collection.find(filter).limit(1)
        if double_check.count():
            continue

        filteredResults.append(result)

    return sorted(filteredResults, key=map.severity_key, reverse=True)


def clear():
    """
    Reset database
    """
    collection.drop()
    collection_meta.drop()
