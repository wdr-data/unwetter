from glob import glob
from os.path import dirname, basename, splitext

from unwetter import db, dwd

from .helpers import load_asset
from . import alert_1


events = {}
xmls = {}

for filename in glob(f"{dirname(__file__)}/*.xml"):
    filename = basename(filename)
    name = splitext(filename)[0]

    xml = load_asset(filename)
    event = dwd.parse_xml(xml)

    events[name] = event
    xmls[name] = xml

    db.collection.insert_one(event)
