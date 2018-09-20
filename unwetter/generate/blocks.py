#!/user/bin/env python3.6

from ..regions import REGIONS


severities = {
    'Minor': 'Wetterwarnung',
    'Moderate': 'Markante Wetterwarnung',
    'Severe': '🔴 Amtliche Unwetterwarnung',
    'Extreme': '🔴 Amtliche Extreme Unwetterwarnung',
}


def qualify_region(region_tuple):
    name, relevance = region_tuple[:2]

    if relevance < 0.2:
        prefix = 'Einzelne Teile'
    elif relevance < 0.6:
        prefix = 'Teile'
    elif relevance < 0.8:
        prefix = 'Weite Teile'
    elif relevance < 1.0:
        prefix = 'Der Großteil'
    else:
        gender = REGIONS[name]['gender']
        if gender:
            return f'{gender.capitalize()} gesamte {name}'
        else:
            return f'Ganz {name}'

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
    if not expires: 
        return f'ab {onset.strftime("%d.%m.%Y, %H:%M")} Uhr (kein Ende der Gültigkeit angegeben)'
    elif onset.date() == expires.date():
        return f'am {onset.strftime("%d.%m.%Y von %H:%M")} Uhr ' \
               f'bis {expires.strftime("%H:%M")} Uhr'
    else:
        return f'von {onset.strftime("%d.%m.%Y, %H:%M")} Uhr ' \
               f'bis {expires.strftime("%d.%m.%Y, %H:%M")} Uhr'


def parameters(event):
    return ', '.join(
        f'{param} ({value.replace("[", "").replace("]", "")})'
        for param, value in event['parameters'].items()
    )
