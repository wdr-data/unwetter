#!/user/bin/env python3.6

from zipfile import ZipFile
from io import BytesIO

import requests

DWD_URL = 'https://opendata.dwd.de/weather/alerts/cap/DISTRICT_EVENT_STAT/Z_CAP_C_EDZW_LATEST_PVW_STATUS_PREMIUMEVENT_DISTRICT_DE.zip'

def load_dwd_xml_events():
    """
    Load ZIP-file from DWD OpenData-API, unzip it, return list of events in XML
    """
    data_zip = BytesIO()
    data_zip.write(requests.get(DWD_URL).content)
    data_zip.seek(0)
    data_zip=ZipFile(data_zip)
    return [
        data_zip.read(name).decode('utf-8') 
        for name in data_zip.namelist()
    ]

def main():
    pass

if __name__ == '__main__':
    main()
