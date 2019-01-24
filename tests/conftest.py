from mongomock import MongoClient

from unwetter import db


def pytest_sessionstart(session):
    db.mongo_client = MongoClient()
    db.mongo_db = db.mongo_client.unwetter
    db.collection = db.mongo_db.events
    db.collection_meta = db.mongo_db.events_meta
