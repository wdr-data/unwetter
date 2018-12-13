
URL_BASE = 'https://unwetter-bot.herokuapp.com/'


def map(event):
    return f'{URL_BASE}map/{event["id"]}.png'


def wina(event):
    return f'{URL_BASE}wina/{event["id"]}'
