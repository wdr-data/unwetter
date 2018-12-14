#!/user/bin/env python3.6
from ..config import filter_event
from ..db import by_ids


def rreplace(s, old, new, occurrence=-1):
    """
    Replace old with new starting from end of the string
    :param s: The string to be transformed
    :param old: Search string
    :param new: Replacement string
    :param occurrence: Number of replacements to do
    :return:
    """
    li = s.rsplit(old, occurrence)
    return new.join(li)


def upper_first(s):
    if len(s) == 0:
        return s

    return s[0].upper() + s[1:]


def pad(text):
    return f'\n{text}\n'


def special_type(event):
    if event['msg_type'] != 'Update':
        return

    if not filter_event(event):
        return

    refs = by_ids(event['references'])

    if any('was_published' in event and event['was_published'] or filter_event(event)
           for event in refs):
        return 'ReAlert'
    else:
        return 'UpdateAlert'
