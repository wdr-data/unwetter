import datetime
from pathlib import Path

from unwetter import dwd

ASSETS = Path('tests') / 'assets'


def load_asset(name):
    with open(ASSETS / name, 'r') as fp:
        return fp.read()


def test_parse_xml_alert():
    xml = load_asset('alert_simple.xml')

    print(repr(dwd.parse_xml(xml)))

    expected = {'id': '2.49.0.1.276.0.DWD.PVW.1544539320000.938e4a06-3fa8-4d7d-984f-ddd1cc3cc149.DEU', 'sender': 'CAP@dwd.de', 'sent': datetime.datetime(2018, 12, 11, 15, 42, tzinfo=datetime.timezone(datetime.timedelta(0, 3600), '+01:00')), 'status': 'Actual', 'msg_type': 'Alert', 'event': 'LEICHTER SCHNEEFALL', 'response_type': 'None', 'urgency': 'Immediate', 'severity': 'Minor', 'certainty': 'Likely', 'effective': datetime.datetime(2018, 12, 11, 15, 42, tzinfo=datetime.timezone(datetime.timedelta(0, 3600), '+01:00')), 'onset': datetime.datetime(2018, 12, 11, 20, 0, tzinfo=datetime.timezone(datetime.timedelta(0, 3600), '+01:00')), 'expires': datetime.datetime(2018, 12, 12, 18, 0, tzinfo=datetime.timezone(datetime.timedelta(0, 3600), '+01:00')), 'headline': 'Amtliche WARNUNG vor LEICHTEM SCHNEEFALL', 'description': 'Es tritt im Warnzeitraum leichter Schneefall mit Mengen zwischen 2 cm und 6 cm auf. In Staulagen werden Mengen bis 12 cm erreicht. Verbreitet wird es glatt.', 'instruction': None, 'parameters': {'Schneefall': '2-6 [cm]', 'Staulagen': '<12 [cm]'}, 'areas': [{'name': 'Gemeinde Marktschellenberg', 'warn_cell_id': '809172124'}, {'name': 'Große Kreisstadt Bad Reichenhall', 'warn_cell_id': '809172114'}, {'name': 'Gemeinde Schneizlreuth', 'warn_cell_id': '809172131'}, {'name': 'Gemeinde Bayerisch Gmain', 'warn_cell_id': '809172115'}, {'name': 'Gemeinde Ramsau b. Berchtesgaden', 'warn_cell_id': '809172129'}, {'name': 'gemeindefreies Gebiet Schellenberger Forst', 'warn_cell_id': '809172454'}, {'name': 'Gemeinde Schönau a. Königssee', 'warn_cell_id': '809172132'}, {'name': 'Gemeinde Berchtesgaden', 'warn_cell_id': '809172116'}, {'name': 'gemeindefreies Gebiet Eck', 'warn_cell_id': '809172452'}, {'name': 'Gemeinde Bischofswiesen', 'warn_cell_id': '809172117'}], 'geometry': [{'polygons': [[[47.649516, 13.088408], [47.627731, 13.095559], [47.601428, 13.06272], [47.586558, 13.064585], [47.576588, 13.041576], [47.55744, 13.055659], [47.534852, 13.031254], [47.52382, 13.04593], [47.492017, 13.047249], [47.486669, 13.027228], [47.464132, 13.000845], [47.47773, 12.98889], [47.474182, 12.972272], [47.496918, 12.908707], [47.521878, 12.88036], [47.526766, 12.857831], [47.54564, 12.847679], [47.544968, 12.81831], [47.556333, 12.794917], [47.578914, 12.779591], [47.610268, 12.807405], [47.626943, 12.799841], [47.632935, 12.780846], [47.667687, 12.754759], [47.679113, 12.733432], [47.682056, 12.695715], [47.696414, 12.715687], [47.734419, 12.719312], [47.740619, 12.760821], [47.753541, 12.787022], [47.755585, 12.814265], [47.755222, 12.848779], [47.752606, 12.883121], [47.744824, 12.894049], [47.770173, 12.928074], [47.747996, 12.935507], [47.738255, 12.914208], [47.723851, 12.905658], [47.709598, 12.930025], [47.707376, 12.987051], [47.713147, 12.998341], [47.722716, 13.017576], [47.709452, 13.048304], [47.686952, 13.07996], [47.672822, 13.076683], [47.649516, 13.088408], [47.649516, 13.088408]]], 'exclude_polygons': []}], 'districts': [{'name': 'Kreis Berchtesgadener Land', 'warn_cell_id': '109172000'}], 'states': ['BY'], 'regions': [], 'has_changes': True}

    assert dwd.parse_xml(xml) == expected
