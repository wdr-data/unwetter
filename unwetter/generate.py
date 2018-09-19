#!/user/bin/env python3.6

import os

from .regions import REGIONS


severities = {
    'Minor': 'Wetterwarnung',
    'Moderate': 'Markante Wetterwarnung',
    'Severe': '🔴 Amtliche Unwetterwarnung',
    'Extreme': '🔴 Amtliche Extreme Unwetterwarnung',
}


def headline(event):
    """
    Return text for headline
    """
    if event['msg_type'] == 'Alert':
        postfix = 'Neue Meldung'
    elif event['msg_type'] == 'Update':
        postfix = 'Aktualisierung'
    elif event['msg_type'] == 'Cancel':
        postfix = 'Meldung aufgehoben'
    else:
        postfix = 'Unbekannter Meldungstyp'

    return f'DETAILS zur amtlichen UNWETTERWARNUNG für NORDRHEIN-WESTFALEN des DWD ({postfix})'


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

    genetiv = REGIONS[name]['cases']['genetiv']
    return f'{prefix} {genetiv}'


def region_list(event):
    return ', '.join(qualify_region(region) for region in event['regions'])


def keywords(event):
    return f'{severities[event["severity"]]}, {region_list(event)}, Technische Erprobung'


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
        return f'Ab {onset.strftime("%d.%m.%Y, %H:%M")} Uhr (kein Ende der Gültigkeit angegeben).' 
    elif onset.date() == expires.date():
        return f'Von {onset.strftime("%d.%m.%Y, %H:%M")} Uhr bis {expires.strftime("%H:%M")} Uhr.' 
    else:
        return f'Von {onset.strftime("%d.%m.%Y, %H:%M")} Uhr bis {expires.strftime("%d.%m.%Y, %H:%M")} Uhr.' 


def parameters(event):
    return ', '.join(
        f'{param} ({value.replace("[", "").replace("]", "")})'
        for param, value in event['parameters'].items()
    )


def description(event):
    """
    Return main body text
    """
    text = f'''
{title(event)}

Warnstufe: {severities[event['severity']]}

Regionale Zuordnung: {region_list(event)}

Gültigkeit: {dates(event)}

Warnung vor: {parameters(event)}

Betroffene Kreise und Städte: {', '.join(area['name'] for area in event['areas'])}

Warnmeldung: {event['description']}

Verhaltenshinweise: {event['instruction'] or ''}

Dieser Text basiert auf offiziellen Informationen des Deutschen Wetterdienstes:
https://www.dwd.de/DE/wetter/warnungen_gemeinden/warnkarten/warnWetter_nrw_node.html?bundesland=nrw

Die Bereitstellung dieser Information ist ein Projekt des Digitalen Wandels und wird aktiv weiterentwickelt.
Informationen und Kontakt: {os.environ["WDR_PROJECT_INFO_URL"]}
    '''.strip()

    for optional in ['Regionale Zuordnung:', 'Warnung vor:', 'Verhaltenshinweise:']:
        text = text.replace(f'{optional} \n\n', '')

    return text
