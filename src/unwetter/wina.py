#!/user/bin/env python3.6

from ftplib import FTP_TLS
from io import BytesIO
import os
import ssl
from html import escape
from datetime import datetime
from uuid import uuid4

from . import db, generate

with open("assets/wina_template.xml", "r") as fp:
    WINA_TEMPLATE = fp.read()


def from_id(id):
    """
    Generates an iso-8859-1 encoded byte string that contains an XML file for OpenMedia/WINA
    :param id: The DWD ID for the event to be processed
    :return: A byte string XML for use with OpenMedia
    """
    event = db.by_id(id)
    sent = generate.local_time(event["sent"]).strftime("%Y%m%dT%H%M%S,000")

    title = generate.title(event, variant="wina_headline")
    text = generate.description(event)
    keywords = generate.keywords(event)

    breaking = False
    if not db.breaking_memo():
        breaking = True
    elif event["severity"] == "Extreme":
        breaking = True

    # Set all to breaking if event is "Severe" or "Extreme"
    if event["severity"] == "Extreme" or event["severity"] == "Severe":
        breaking = True

    return wina_xml(sent, title, text, keywords, breaking)


def wina_xml(sent, title, text, keywords="", breaking=False):
    """
    Generate wina xml file in iso code 8859-1
    :param sent: Sent time
    :param title: headline of wina
    :param text: body text
    :param keywords:
    :param breaking
    :return:
    """

    if breaking:
        priority_number = 1
    else:
        priority_number = 3

    return WINA_TEMPLATE.format(
        sent=escape(sent),
        title=escape(title),
        keywords=escape(keywords),
        text=escape(text).replace("\n", "&#xD;&#xA;"),
        priority_number=priority_number,
    ).encode("iso-8859-1", errors="ignore")


def upload_text(title, text, keywords):

    sent = generate.local_time(datetime.utcnow()).strftime("%Y%m%dT%H%M%S,000")
    upload([BytesIO(wina_xml(sent, title, text, keywords))])


def upload_ids(ids):
    files = [BytesIO(from_id(id)) for id in ids]
    return upload(files)


def upload(files):
    """
    Uploads a WINA-XML file to a provided server via explicit FTP with TLS Protocol.
    :param: files: List of DWD BytesIO(from_id(id))
    :return: Status code
    """

    logins = [
        ("NVS_FTP_URL", "NVS_FTP_USER", "NVS_FTP_PASS"),
        ("NVS_FTP_URL_SECONDARY", "NVS_FTP_USER_SECONDARY", "NVS_FTP_PASS_SECONDARY"),
    ]

    for login_info in logins:

        if any(var not in os.environ for var in login_info):
            print("Missing environment variable for FTP login")
            continue

        # Retry 5 times
        last_exception = None
        for i in range(5):
            try:
                ftps = _ftp_connect(login_info)
                break
            except Exception as e:
                last_exception = e
                print(e)
                print(f"[{i + 1}/5] Retrying FTP connection...")
                continue
        else:
            print("Failed FTP connection")
            sentry.sentry_sdk.capture_exception(last_exception)
            continue

        ftps.prot_p()

        for file in files:
            file.seek(0)
            print(ftps.storbinary(f"STOR uwa_{uuid4()}.xml", file))

        print(ftps.quit())
