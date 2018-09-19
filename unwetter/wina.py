#!/user/bin/env python3.6

from unwetter import db, generate


with open('assets/wina_template.xml', 'r') as fp:
    WINA_TEMPLATE = fp.read()


def from_id(id):
    """
    Generates an iso-8859-1 encoded byte string that contains an XML file for OpenMedia/WINA
    :param id: The DWD ID for the event to be processed
    :return: A byte string XML for use with OpenMedia
    """
    event = db.collection.find_one({'id': id})
    sent = event['sent'].strftime('%Y%m%dT%H%M%S,000')

    wina_xml = WINA_TEMPLATE.format(
        sent=sent,
        title=generate.headline(event),
        keywords=generate.keywords(event),
        text=generate.description(event).replace('\n', '&#xD;&#xA;'),
    )

    return wina_xml.encode('iso-8859-1', errors='xmlcharrefreplace')
