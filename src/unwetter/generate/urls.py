import os


URL_BASE = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com/"


def map(event):
    return f'{URL_BASE}map/{event["id"]}.png'


def wina(event):
    return f'{URL_BASE}wina/{event["id"]}'
