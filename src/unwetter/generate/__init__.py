#!/user/bin/env python3.6

import os

from .. import db, config
from .blocks import *
from .helpers import rreplace, upper_first
from . import urls


def describe_new_event(event):
    text = f'''
{title(event)}

Warnstufe: {severities[event['severity']]}

Regionale Zuordnung: {region_list(event)}

Karte: {urls.map(event)}

Gültigkeit: {upper_first(dates(event))}.

Warnung vor: {parameters(event)}

Betroffene Kreise und Städte: {district_list(event)}

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
    old_events = [event for event in db.by_ids(event['references']) if config.filter_event(event)]
    change_details = []

    for old_event in old_events:
        old_time = local_time(old_event['sent']).strftime("%d.%m.%Y, %H:%M:%S Uhr")

        if event['msg_type'] == 'Cancel' or event['response_type'] == 'AllClear':
            change_title = 'Aufhebung von'
            the_changes = ''
        elif event['special_type'] == 'Irrelevant':
            change_title = 'Aufhebung von'
            the_changes = (changes(event, old_event) if old_event else 'Unbekannt')
        else:
            change_title = 'Änderungen zur'
            the_changes = (changes(event, old_event) if old_event else 'Unbekannt') + '\n'

        change_details.append(f'''
+++ {change_title} Meldung mit Agenturzeit {old_time} +++

{the_changes}'''.strip())

    joined = '\n\n'.join(change_details)
    all_changes = f'\n{joined}\n' if change_details else ''

    text = f'''
{title(event)}
{all_changes}
+++ Details +++

Warnstufe: {severities[event['severity']]}

Regionale Zuordnung: {region_list(event)}

Karte: {urls.map(event)}

Gültigkeit: {upper_first(dates(event))}.

Warnung vor: {parameters(event)}

Betroffene Kreise und Städte: {district_list(event)}

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
    if event['msg_type'] == 'Alert' or event['special_type'] == 'UpdateAlert':
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
        location = district_list(event)
    else:
        location = region_list(event, accusative=True)

    if not location:
        location = district_list(event)

    location = rreplace(location, ', ', ' und ', 1)

    text = ' '.join(
        word.capitalize() if word.isupper() else word
        for word in event['event'].split()
    ).replace('Schwer', 'schwer')

    for lower_word in ('Heftig', 'Schwer', 'Starke', 'Extrem'):
        text = text.replace(lower_word, lower_word.lower())

    text = upper_first(text)

    if event['msg_type'] == 'Cancel':
        the_crawl = (f'Amtliche {warning} des Deutschen Wetterdienstes für '
                     f'{location} zurückgezogen.')

    elif event['response_type'] == 'AllClear':
        the_crawl = (f'Amtliche {warning} des Deutschen Wetterdienstes für '
                     f'{location} vorzeitig aufgehoben.')

    else:
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

    districts = district_list(event)
    districts = rreplace(districts, ', ', ' und ', 1)

    regions_ = region_list(event, accusative=True)
    regions_ = rreplace(regions_, ', ', ' und ', 1)

    dates_ = dates(event)

    if event['msg_type'] == 'Cancel':
        candidates = [
            'Amtliche #{warning} des Deutschen Wetterdienstes für '
            '{areas} zurückgezogen. @DWD_presse',
        ]
    elif event['response_type'] == 'AllClear':
        candidates = [
            'Amtliche #{warning} des Deutschen Wetterdienstes für '
            '{areas} vorzeitig aufgehoben. @DWD_presse',
        ]
    else:
        candidates = [
            '{prefix} amtliche #{warning} des Deutschen Wetterdienstes für '
            '{districts}. {text} möglich. Gültig {dates}. @DWD_presse',
            '{prefix} amtliche {warning} des Deutschen Wetterdienstes für '
            '{districts}. {text} möglich. Gültig {dates}.',
            '{prefix} amtliche #{warning} des Deutschen Wetterdienstes für '
            '{regions}. {text} möglich. Gültig {dates}. @DWD_presse',
            '{prefix} amtliche {warning} des Deutschen Wetterdienstes für '
            '{regions}. {text} möglich. Gültig {dates}.',
        ]

    for candidate in candidates:
        the_tweet = candidate.format(
            prefix=prefix,
            warning=warning,
            districts=districts,
            regions=regions_,
            text=text,
            dates=dates_)
        the_tweet = the_tweet.replace(' (kein Ende der Gültigkeit angegeben)', '').strip()
        if len(the_tweet) <= 280:
            break
    else:
        the_tweet = 'Tweet konnte nicht generiert werden, da zu lang'

    return upper_first(the_tweet)
