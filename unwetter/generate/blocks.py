#!/user/bin/env python3.6

from datetime import datetime, timedelta

from ..regions import REGIONS
from .grammar import *
from .helpers import upper_first

severities = {
    'Minor': 'Wetterwarnung',
    'Moderate': 'Markante Wetterwarnung',
    'Severe': '🔴 Amtliche Unwetterwarnung',
    'Extreme': '🔴 Amtliche Extreme Unwetterwarnung',
}


def qualify_region(region_tuple):
    name, relevance = region_tuple[:2]

    if relevance < 0.2:
        prefix = 'einzelne Teile'
    elif relevance < 0.6:
        prefix = 'Teile'
    elif relevance < 0.8:
        prefix = 'weite Teile'
    elif relevance < 1.0:
        prefix = 'der Großteil'
    else:
        return definite_article(REGIONS[name], 'gesamte', 'ganz')

    return f'{prefix} {genitive(REGIONS[name])}'


def region_list(event):
    return ', '.join(qualify_region(region) for region in event['regions'])


def area_list(event):
    return ', '.join(area['name'] for area in event['areas'])


def keywords(event):
    return f'{severities[event["severity"]]}, {region_list(event) or "Nicht NRW"}, ' \
           f'Technische Erprobung'


def title(event):
    """
    Return first sentence of main body text
    """
    if event['msg_type'] == 'Alert':
        prefix = '🚨 Neue Meldung'
    elif event['msg_type'] == 'Update':
        prefix = '🔁 Meldung aktualisiert'
    elif event['msg_type'] == 'Cancel':
        prefix = '🚫 Meldung aufgehoben'
    else:
        prefix = '⁉️ Unbekannter Meldungstyp'

    return f'{prefix}: {event["headline"]}'


def dates(event):
    onset = event['onset']
    expires = event['expires']
    today = datetime.utcnow().date()

    if onset.date() == today:
        onset_date = 'Heute'
    elif onset.date() == today + timedelta(days=1):
        onset_date = 'Morgen'
    else:
        onset_date = onset.strftime("%d.%m.%Y")

    if expires.date() == today:
        expires_date = 'Heute'
    elif expires.date() == today + timedelta(days=1):
        expires_date = 'Morgen'
    else:
        expires_date = expires.strftime("%d.%m.%Y")

    if not expires: 
        return f'ab {onset_date}, {onset.strftime("%H:%M")} Uhr (kein Ende der Gültigkeit angegeben)'
    elif onset.date() == expires.date():
        return f'{onset_date}, von {onset.strftime("%H:%M")} Uhr ' \
               f'bis {expires.strftime("%H:%M")} Uhr'
    else:
        return f'von {onset_date}, {onset.strftime("%H:%M")} Uhr ' \
               f'bis {expires_date}, {expires.strftime("%H:%M")} Uhr'


def parameters(event):
    return ', '.join(
        f'{param} ({value.replace("[", "").replace("]", "")})'
        for param, value in event['parameters'].items()
    )


def changes(event, old_event):
    """
    Generate a list of changes between two events
    :param event:
    :param old_event:
    :return: str
    """
    text = ''

    if dates(old_event) != dates(event):
        text += f'Gültigkeit: {dates(event)} (zuvor "{dates(old_event)}")\n\n'

    if area_list(old_event) != area_list(event):
        areas_now = set(area['name'] for area in event['areas'])
        areas_before = set(area['name'] for area in old_event['areas'])

        added = areas_now - areas_before
        removed = areas_before - areas_now

        if added:
            text += f'Neue Kreise/Städte: {", ".join(added)}\n'

        if removed:
            text += f'Neue Kreise/Städte: {", ".join(removed)}\n'

        text += f'Regionale Zuordnung: {upper_first(region_list(event))} ' \
                f'(zuvor: "{upper_first(region_list(old_event))}")\n\n'

    simple_fields = {
        'event': 'Wetterphänomen',
        'severity': 'Warnstufe',
        'certainty': 'Wahrscheinlichkeit',
    }

    for field in simple_fields:
        if old_event.get(field) != event.get(field):
            if field == 'severity':
                text += f'{simple_fields[field]}: {severities[event[field]]} ' \
                        f'(zuvor "{severities[old_event[field]]}")\n'
            else:
                text += f'{simple_fields[field]}: {event[field]} ' \
                        f'(zuvor "{old_event.get(field, "Nicht angegeben")}")\n'

    return text
