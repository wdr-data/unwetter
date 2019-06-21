#!/user/bin/env python3.6

import os

from .. import db
from .blocks import *
from .helpers import rreplace, upper_first
from . import urls
from ..config import SEVERITY_FILTER, STATES_FILTER


def describe_new_event(event):
    text = f'''
{title(event)}


+++ Gültigkeit +++

{upper_first(dates(event))}.

Regionale Zuordnung: {region_list(event)}

Betroffene Kreise und Städte: {district_list(event)}

Karten-Grafik Download:
{urls.events(event)}


+++ Wetterlage +++

Warnstufe: {severities[event['severity']]}

{event['description']}

Warnung vor: {parameters(event)}

Verhaltenshinweise: {event['instruction'] or ''}


+++ Textvorschläge +++

TWEET: {tweet(event)}

TV-CRAWL: {crawl(event)}

Hinweis: Textvorschläge werden nach redaktionellen Vorgaben automatisch generiert.


+++ DWD +++
Die Eilmeldung des DWD erreicht OpenMedia in der Regel wenige Minuten nach dieser Meldung.
(In einigen Fällen, z.B. kurze Gültigkeit und/oder kleines Gebiet, kann eine Meldung des DWD entfallen!)

Website des Deutschen Wetterdienstes:
https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html

Telefon DWD: 069-8062-6900


+++ Allgemeine Information +++
Die aufgeführten Informationen dürfen als Quelle zur Abwicklung des Unwetter-Workflows genutzt werden.

Die Bereitstellung dieser Information erfolgt durch den Unwetter-Warnassistenten (UWA), ein Produkt des Newsrooms. 
Der UWA wird aktiv weiterentwickelt.
Kontakt und weitere Informationen: {os.environ["WDR_PROJECT_INFO_URL"]}
'''.strip()

    for optional in ['Regionale Zuordnung:', 'Warnung vor:', 'Verhaltenshinweise:']:
        text = text.replace(f'{optional} \n\n', '')

    return text


def describe_update(event):
    old_events = [event for event in db.by_ids(event['references']) if event.get('published')]
    change_details = []

    for old_event in old_events:
        old_time = local_time(old_event['sent']).strftime("%H:%M %d.%m.%y")

        if event['msg_type'] == 'Cancel' or event['response_type'] == 'AllClear':
            change_title = 'Aufhebung von'
            the_changes = ''
        elif event['special_type'] == 'Irrelevant' and event['severity'] not in SEVERITY_FILTER:
            change_title = 'Herabstufung von'
            the_changes = (changes(event, old_event) if old_event else 'Unbekannt')
        elif event['special_type'] == 'Irrelevant' and not any(state in event['states'] for state in STATES_FILTER):
            change_title = 'Änderungen zur'
            the_changes = f'Die Unwetterregion befindet sich nicht ' \
                          f'mehr im Bundesland {", ".join(STATES_FILTER)}.\n\n ' \
                          f'Andere Unwetterregionen kônnen noch in NRW aktiv sein! ' \
                          f'Vergleiche dazu die UWA und DWD Karten.'
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
+++ Gültigkeit +++

{upper_first(dates(event))}.

Regionale Zuordnung: {region_list(event)}

Betroffene Kreise und Städte: {district_list(event)}

Karten-Grafik Download:
{urls.events(event)}


+++ Wetterlage +++

Warnstufe: {severities[event['severity']]}

{event['description']}

Warnung vor: {parameters(event)}

Verhaltenshinweise: {event['instruction'] or ''}


+++ Textvorschläge +++

TWEET: {tweet(event)}

TV-CRAWL: {crawl(event)}


Hinweis: Textvorschläge werden nach redaktionellen Vorgaben automatisch generiert.

+++ DWD +++
Die Eilmeldung des DWD erreicht OpenMedia in der Regel wenige Minuten nach dieser Meldung.
(In einigen Fällen, z.B. kurze Gültigkeit und/oder kleines Gebiet, kann eine Meldung des DWD entfallen!)

Website des Deutschen Wetterdienstes:
https://www.dwd.de/DE/wetter/warnungen/warnWetter_node.html

Telefon DWD: 069-8062-6900


+++ Allgemeine Information +++
Die aufgeführten Informationen dürfen als Quelle zur Abwicklung des Unwetter-Workflows genutzt werden.

Die Bereitstellung dieser Information erfolgt durch den Unwetter-Warnassistenten (UWA), ein Produkt des Newsrooms. 
Der UWA wird aktiv weiterentwickelt.
Kontakt und weitere Informationen: {os.environ["WDR_PROJECT_INFO_URL"]}
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
            '{areas} zurückgezogen.',
        ]
    elif event['response_type'] == 'AllClear':
        candidates = [
            'Amtliche #{warning} des Deutschen Wetterdienstes für '
            '{areas} vorzeitig aufgehoben.',
        ]
    else:
        candidates = [
            '{prefix} amtliche #{warning} des Deutschen Wetterdienstes für '
            '{districts}. {text} möglich. Gültig {dates}.',
            '{prefix} amtliche {warning} des Deutschen Wetterdienstes für '
            '{districts}. {text} möglich. Gültig {dates}.',
            '{prefix} amtliche #{warning} des Deutschen Wetterdienstes für '
            '{regions}. {text} möglich. Gültig {dates}.',
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
