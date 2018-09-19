#!/user/bin/env python3.6

from ftplib import FTP_TLS
from io import BytesIO
import os
import ssl
from html import escape

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
        sent=escape(sent),
        title=escape(generate.headline(event)),
        keywords=escape(generate.keywords(event)),
        text=escape(generate.description(event)).replace('\n', '&#xD;&#xA;'),
    )

    return wina_xml.encode('iso-8859-1', errors='ignore')


def upload(ids):
    """
    Uploads a WINA-XML file to a provided server via explicit FTP with TLS Protocol.
    :param: ids: List of DWD IDs
    :return: Status code
    """

    files = [BytesIO(from_id(id)) for id in ids]

    ftps = FTP_TLS(
        host=os.environ['NVS_FTP_URL'],
        user=os.environ['NVS_FTP_USER'],
        passwd=os.environ['NVS_FTP_PASS'],
        context=ssl.create_default_context(),
    )
    ftps.prot_p()

    for id, file in zip(ids, files):
        print(ftps.storbinary(f'STOR {id}.xml', file))

    print(ftps.quit())
