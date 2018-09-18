#!/user/bin/env python3.6

import os


def title(event):
    if event['msg_type'] == 'Alert':
        prefix = '🚨 Neue Meldung'
    elif event['msg_type'] == 'Update':
        prefix = '🔁 Meldung aktualisiert'
    elif event['msg_type'] == 'Cancel':
        prefix = '🚫 Meldung aufgehoben'
    else:
        prefix = '⁉️ Unbekannter Meldungstyp'

    return f'{prefix}: {event["headline"]}'


def description(event):
    severities = {
        'Minor': 'Wetterwarnung',
        'Moderate': 'Markante Wetterwarnung',
        'Severe': '🔴 Amtliche Unwetterwarnung',
        'Extreme': '🔴 Amtliche Extreme Unwetterwarnung',
    }
    return f'''
Warnstufe: {severities[event['severity']]} 
Orte: {', '.join(area['name'] for area in event['areas'])}
Gültig von {event['onset'].strftime('%d.%m.%Y %H:%M:%S')} bis {event['expires'].strftime('%d.%m.%Y %H:%M:%S') if event['expires'] else 'Nicht angegeben'}
Warnmeldung: {event['description']}
    '''.strip()


def more_info_text():

    return f'Infos zu dieser Meldung: {os.environ["WDR_PROJECT_INFO_URL"]}'
