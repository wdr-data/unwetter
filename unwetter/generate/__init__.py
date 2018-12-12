#!/user/bin/env python3.6

import os

from .. import db
from .blocks import *
from .helpers import rreplace, upper_first


def headline(event):
    """
    Return text for headline
    """
    if event['msg_type'] == 'Alert':
        prefix = ''
    elif event['msg_type'] == 'Update':
        prefix = 'Aktualisierung: '
    elif event['msg_type'] == 'Cancel':
        prefix = 'Meldung aufgehoben: '
    else:
        prefix = 'Unbekannter Meldungstyp - '

    return f'{prefix}DETAILS zur amtlichen UNWETTERWARNUNG für NORDRHEIN-WESTFALEN des DWD'


def describe_new_event(event):
    text = f'''
{title(event)}

Warnstufe: {severities[event['severity']]}

Regionale Zuordnung: {region_list(event)}

Gültigkeit: {upper_first(dates(event))}.

Warnung vor: {parameters(event)}

Betroffene Kreise und Städte: {area_list(event)}

Verhaltenshinweise: {event['instruction'] or ''}


+++ Textvorschläge +++

Tweet: {tweet(event)}

TV-Crawl: {crawl(event)}

Meldung des DWD: {event['description']}

Hinweis: Textvorschläge für Twitter und den TV-Crawl werden im WDR automatisch generiert.


+++ Über diese Meldung +++

Diese Meldung basiert auf offiziellen Informationen des Deutschen Wetterdienstes:
https://www.dwd.de/DE/wetter/warnungen_gemeinden/warnkarten/warnWetter_nrw_node.html?bundesland=nrw

Die Bereitstellung dieser Information ist ein Projekt des Digitalen Wandels und wird aktiv weiterentwickelt.
Informationen und Kontakt: {os.environ["WDR_PROJECT_INFO_URL"]}
    '''.strip()

    for optional in ['Regionale Zuordnung:', 'Warnung vor:', 'Verhaltenshinweise:']:
        text = text.replace(f'{optional} \n\n', '')

    return text


def describe_update(event):

    old_event = db.latest_reference(event['references'])

    if old_event:
        old_time = old_event['sent'].strftime("%d.%m.%Y, %H:%M:%S Uhr")
    else:
        old_time = 'Unbekannt'

    text = f'''
{title(event)}


+++ Änderungen zur Meldung mit Agenturzeit {old_time} +++

{changes(event, old_event) if old_event else 'Unbekannt'}

+++ Details +++

Warnstufe: {severities[event['severity']]}

Regionale Zuordnung: {region_list(event)}

Gültigkeit: {upper_first(dates(event))}.

Warnung vor: {parameters(event)}

Betroffene Kreise und Städte: {area_list(event)}

Verhaltenshinweise: {event['instruction'] or ''}


+++ Textvorschläge +++

Tweet: {tweet(event)}

TV-Crawl: {crawl(event)}

Meldung des DWD: {event['description']}

Hinweis: Textvorschläge für Twitter und den TV-Crawl werden im WDR automatisch generiert.


+++ Über diese Meldung +++

Diese Meldung basiert auf offiziellen Informationen des Deutschen Wetterdienstes:
https://www.dwd.de/DE/wetter/warnungen_gemeinden/warnkarten/warnWetter_nrw_node.html?bundesland=nrw

Die Bereitstellung dieser Information ist ein Projekt des Digitalen Wandels und wird aktiv weiterentwickelt.
Informationen und Kontakt: {os.environ["WDR_PROJECT_INFO_URL"]}
    '''.strip()

    for optional in ['Regionale Zuordnung:', 'Warnung vor:', 'Verhaltenshinweise:']:
        text = text.replace(f'{optional} \n\n', '')

    return text


def description(event, short=False):
    """
    Return main body text
    """
    if event['msg_type'] == 'Alert':
        text = describe_new_event(event)
    else:
        text = describe_update(event)

    if short:
        # Delete generated texts
        text = text.split('+++ Textvorschläge +++')[0].strip()

    return text


def crawl(event):
    prefix = 'aktualisierte' if event['msg_type'] == 'Update' else ''

    warning = 'Unwetterwarnung' if event['severity'] in ('Severe', 'Extreme') else 'Wetterwarnung'

    if len(event['districts']) < 3:
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

    for lower_word in ('Heftig', 'Schwer', 'Starke', 'Extrem'):
        text = text.replace(lower_word, lower_word.lower())

    text = upper_first(text)

    the_crawl = (f'{prefix} amtliche {warning} des Deutschen Wetterdienstes für '
                 f'{location}. {text} möglich. Gültig {dates(event)}.'
                 '[Weitere Infos (nächste TV-Sendung, NUR wenn weniger als 2h bis '
                 'Sendungsbeginn), auf wdr.de und im Videotext auf S. 192.]').strip()

    the_crawl = the_crawl.replace(' (kein Ende der Gültigkeit angegeben)', '')

    return upper_first(the_crawl)


def tweet(event):
    prefix = 'aktualisierte' if event['msg_type'] == 'Update' else ''

    warning = 'Unwetterwarnung' if event['severity'] in ('Severe', 'Extreme') else 'Wetterwarnung'

    text = ' '.join(
        word.capitalize() if word.isupper() else word
        for word in event['event'].split()
    ).replace('Schwer', 'schwer')

    for lower_word in ('Heftig', 'Schwer', 'Starke', 'Extrem'):
        text = text.replace(lower_word, lower_word.lower())

    text = upper_first(text)

    areas = area_list(event)
    areas = rreplace(areas, ', ', ' und ', 1)

    regions_ = region_list(event)
    regions_ = rreplace(regions_, ', ', ' und ', 1)

    dates_ = dates(event)

    candidates = [
        '{prefix} amtliche #{warning} des Deutschen Wetterdienstes für '
        '{areas}. {text} möglich. Gültig {dates}. @DWD_presse',
        '{prefix} amtliche {warning} des Deutschen Wetterdienstes für '
        '{areas}. {text} möglich. Gültig {dates}.',
        '{prefix} amtliche #{warning} des Deutschen Wetterdienstes für '
        '{regions}. {text} möglich. Gültig {dates}. @DWD_presse',
        '{prefix} amtliche {warning} des Deutschen Wetterdienstes für '
        '{regions}. {text} möglich. Gültig {dates}.',
    ]

    for candidate in candidates:
        the_tweet = candidate.format(
            prefix=prefix, warning=warning, areas=areas, regions=regions_, text=text, dates=dates_)
        the_tweet = the_tweet.replace(' (kein Ende der Gültigkeit angegeben)', '').strip()
        if len(the_tweet) <= 280:
            break
    else:
        the_tweet = 'Tweet konnte nicht generiert werden, da zu lang'

    return upper_first(the_tweet)
