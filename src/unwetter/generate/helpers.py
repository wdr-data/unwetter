#!/user/bin/env python3.6
import pytz


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


def local_time(dt):
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(pytz.timezone('Europe/Berlin'))
