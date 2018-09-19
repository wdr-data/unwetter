#!/user/bin/env python3.6

import os

from .blocks import *
from .helpers import rreplace, upper_first


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


def description(event):
    """
    Return main body text
    """
    text = f'''
{title(event)}

Warnstufe: {severities[event['severity']]}

Regionale Zuordnung: {region_list(event)}

Gültigkeit: {dates(event).capitalize()}.

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


def crawl(event):
    prefix = 'aktualisierte' if event['msg_type'] == 'Update' else ''

    if len(event['areas']) < 3:
        location = area_list(event)
    else:
        location = region_list(event)

    if not location:
        location = area_list(event)

    location = rreplace(location, ', ', ' und ', 1)

    text = ' '.join(
        word.capitalize() if word.isupper() else word
        for word in event['event'].split()
    ).replace('Schwer', 'schwer')

    for lower_word in ('Heftig', 'Schwer', 'Starke'):
        text = text.replace(lower_word, lower_word.lower())

    text = upper_first(text)

    the_crawl = f'{prefix} amtliche Unwetterwarnung des Deutschen Wetterdienstes für ' \
                f'{location}. {text} möglich. Gültig {dates(event)}.'.strip()

    return upper_first(the_crawl)
