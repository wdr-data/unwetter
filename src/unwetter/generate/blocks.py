#!/user/bin/env python3.6

from datetime import datetime, timedelta

from ..config import STATES_FILTER
from ..dwd import state_for_cell_id
from ..regions import REGIONS
from .grammar import *
from .helpers import upper_first, local_time

severities = {
    'Minor': 'Wetterwarnung',
    'Moderate': 'Markante Wetterwarnung',
    'Severe': '🔴 Amtliche Unwetterwarnung',
    'Extreme': '🔴 Amtliche Extreme Unwetterwarnung',
}


def qualify_region(region_tuple, accusative=False):
    name, relevance = region_tuple[:2]

    if relevance < 0.2:
        prefix = 'einzelne Teile'
    elif relevance < 0.6:
        prefix = 'Teile'
    elif relevance < 0.8:
        prefix = 'weite Teile'
    elif relevance < 1.0:
        prefix = 'den Großteil' if accusative else 'der Großteil'
    else:
        return definite_article(REGIONS[name], 'gesamte', 'ganz')

    return f'{prefix} {genitive(REGIONS[name])}'


def region_list(event, accusative=False):
    return ', '.join(qualify_region(region, accusative=accusative) for region in event['regions'])


def filter_districts(event):
    return [
        district for district in event['districts']
        if state_for_cell_id(district['warn_cell_id']) in STATES_FILTER
    ]


def filter_communes(event):
    return [
        commune for commune in event['areas']
        if state_for_cell_id(commune['warn_cell_id']) in STATES_FILTER
    ]


def district_list(event, all=False):
    return ', '.join(
        district['name'] for district in
        (event['districts'] if all else filter_districts(event))
    )


def commune_list(event, all=False):
    return ', '.join(
        commune['name'] for commune in
        (event['areas'] if all else filter_communes(event))
    )


def keywords(event):
    # f'{severities[event["severity"]]}, {region_list(event) or "Nicht NRW"}'
    parameter_keys = ', '.join(
        f'{param}' for param, value in event['parameters'].items()
    )

    return f'Unwetter, UWA, Warnung, {parameter_keys}'


def title(event, variant='default'):
    """
    Return first sentence of main body text

    variant can be 'default' or 'wina_headline'
    """

    extentions = {
        'default': {
            'new_event': '🚨 Neue Meldung',
            'event_relevant_again': '🚨 Erneut relevante Meldung',
            'cancelled_prematurely': '🚫 Meldung vorzeitig aufgehoben',
            'updated': '🔁 Meldung aktualisiert',
            'cancelled_wrong': '🚫 Meldung zurückgezogen',
            'irrelevant': '🔁  Meldung aktualisiert',
            'unknown': '⁉️ Unbekannter Meldungstyp',
        },
        'wina_headline': {
            'new_event': '',
            'event_relevant_again': ' - Erneut relevant',
            'cancelled_prematurely': ' - Vorzeitige Aufhebung',
            'updated': ' - Aktualisierung',
            'cancelled_wrong': ' - Meldung zurückgezogen',
            'irrelevant': ' - Aktualisierung',
            'unknown': ' - Unbekannter Meldungstyp',
        }
    }

    if event['msg_type'] == 'Alert':
        extention = extentions[variant]['new_event']
    elif event['msg_type'] == 'Update':
        if event['response_type'] == 'AllClear':
            extention = extentions[variant]['cancelled_prematurely']
        elif event['special_type'] == 'ReAlert':
            extention = extentions[variant]['event_relevant_again']
        elif event['special_type'] == 'UpdateAlert':
            extention = extentions[variant]['new_event']
        elif event['special_type'] == 'Irrelevant':
            extention = extentions[variant]['irrelevant']
        else:
            extention = extentions[variant]['updated']
    elif event['msg_type'] == 'Cancel':
        extention = extentions[variant]['cancelled_wrong']
    else:
        extention = extentions[variant]['unknown']

    if variant == 'default':
        return f'{extention}: {event["headline"]}'
    elif variant == 'wina_headline':
        return f'Amtliche Unwetterwarnung des DWD {extention}'


def dates(event):
    onset = local_time(event['onset'])
    expires = event['expires'] and local_time(event['expires'])
    today = local_time(datetime.utcnow()).date()

    if onset.date() == today:
        onset_date = f'Heute ({onset.strftime("%d.%m.%y")})'
    elif onset.date() == today + timedelta(days=1):
        onset_date = f'Morgen ({onset.strftime("%d.%m.%y")})'
    else:
        onset_date = onset.strftime("%d.%m.%y")

    if expires:
        if expires.date() == today:
            expires_date = f'Heute ({expires.strftime("%d.%m.%y")})'
        elif expires.date() == today + timedelta(days=1):
            expires_date = f'Morgen ({expires.strftime("%d.%m.%y")})'
        else:
            expires_date = expires.strftime("%d.%m.%y")

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

    if dates(old_event)[-9:] != dates(event)[-9:]:
        # Editorial request to check only, if expires time changed, since every update has new onset-time
        # Format of dates : 'HH:MM Uhr'
        text += f'Gültigkeit: {dates(event)} (zuvor "{dates(old_event)}")\n\n'

    if district_list(old_event) != district_list(event):
        districts_now = {
            district['name'] for district in event['districts']
            if state_for_cell_id(district['warn_cell_id']) in STATES_FILTER
        }
        districts_before = {
            district['name'] for district in old_event['districts']
            if state_for_cell_id(district['warn_cell_id']) in STATES_FILTER
        }

        added = districts_now - districts_before
        removed = districts_before - districts_now

        if added:
            text += f'Neue Kreise/Städte: {", ".join(sorted(added))}\n'

        if removed:
            text += f'Nicht mehr betroffene Kreise/Städte: {", ".join(sorted(removed))}\n'

        if region_list(old_event) != region_list(event):
            text += f'Regionale Zuordnung: {upper_first(region_list(event))} ' \
                    f'(zuvor: "{upper_first(region_list(old_event))}")\n\n'
        else:
            text += f'Regionale Zuordnung unverändert: {upper_first(region_list(event))}\n\n'

    '''
    # Editorial choice --> No relevant information due to relatively small area --> Thus, no update

    elif commune_list(old_event) != commune_list(event):
        text += 'Regionale Zuordnung: Änderung der betroffenen Gemeinden\n\n'
    '''

    return text
