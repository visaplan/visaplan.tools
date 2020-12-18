# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Tools for time calculations
"""

# Python compatibility:
from __future__ import absolute_import

from six.moves import map

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (0,
           4,  # make_safe_decoder, now --> .coding
           9,  # unique_union,      now --> .sequences
           )
__version__ = '.'.join(map(str, VERSION))


# Standard library:
from calendar import timegm
from time import gmtime, localtime, mktime, strftime, strptime

# Local imports:
from visaplan.tools.minifuncs import check_kwargs

__all__ = [
           'makeDeltaTime',
           'make_defaulttime_calculator',
           ]


SUFFIX = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 3600 * 24,
        }
def makeDeltaTime(val):
    """
    Zopes DateTime-Objekte unterstützen die Addition von Zahlenwerten;
    die Zahl 1 entspricht einem Tag.

    Die Funktion konvertiert Zeitangaben mit Suffixen in Tagesbruchteile;
    eine Zahl ohne Suffix wird als Sekundenangabe interpretiert.
    Mehrere Angaben können kombiniert werden (mit Leerzeichen getrennt)
    und werden aufsummiert.

    >>> makeDeltaTime('1d')
    1.0
    >>> makeDeltaTime('1d 5m')
    1.0034722222222223
    """
    secs = 0
    for s in val.split():
        try:
            # Absicht: Sekundenbruchteile erfordern Suffix s!
            secs += int(s)
        except ValueError:
            suff = s[-1]
            fact = SUFFIX[suff]
            secs += float(s[:-1]) * fact
    return (secs * 1.0) / SUFFIX['d']


def make_defaulttime_calculator(year=0, month=0, day=0,
                                nextmonth=False,
                                dateonly=True,
                                default_date_format='%Y-%m-%d',
                                **kwargs):
    """
    Gib eine Funktion zurück, die ein Standarddatum erzeugt, z. B. das
    Standard-Ablaufdatum einer TAN (--> @@tan.utils.default_expiration_date).

    By default the time.localtime function is used; you can force e.g.
    time.gmtime to be used by the keyword-only option "utc".
    We need this for testability:

    >>> kw = dict(utc=True)

    Preparation of test data:

    >>> heute=gmtime(1406808000.0)
    >>> heute
    time.struct_time(tm_year=2014, tm_mon=7, tm_mday=31, tm_hour=12, tm_min=0, tm_sec=0, tm_wday=3, tm_yday=212, tm_isdst=0)
    >>> timegm(heute)
    1406808000

    Create a function f which adds at least one year and increases single
    days until the 1st day of a month is reached:

    >>> f = make_defaulttime_calculator(year=1, nextmonth=True, **kw)

    By default, the result is formatted according to the default_date_format:

    >>> f(today=heute)
    '2015-08-01'

    By specifying mask=None, you can get a number:

    >>> num = f(today=heute, mask=None)
    >>> num
    1438387200

    By default, the time part is set to 0:00:

    >>> gmtime(num)
    time.struct_time(tm_year=2015, tm_mon=8, tm_mday=1, tm_hour=0, tm_min=0, tm_sec=0, tm_wday=5, tm_yday=213, tm_isdst=0)

    However, you can suppress this behaviour:

    >>> gmtime(f(today=heute, mask=None, dateonly=False))
    time.struct_time(tm_year=2015, tm_mon=8, tm_mday=1, tm_hour=12, tm_min=0, tm_sec=0, tm_wday=5, tm_yday=213, tm_isdst=0)

    Create a function f2 which adds 90 days:

    >>> f2 = make_defaulttime_calculator(day=90, nextmonth=False, **kw)
    >>> f2(today=heute)
    '2014-10-29'
    >>> f2(today=heute, mask=None)
    1414540800
    """
    pop = kwargs.pop
    utc = pop('utc', False)

    check_kwargs(kwargs)  # raises TypeError if necessary

    if utc:
        time_factory = gmtime
        time_to_secs = timegm
    else:
        time_factory = localtime
        time_to_secs = mktime

    def calc_date(mask='', today=None, dateonly=dateonly):
        if today is None:
            today = time_factory()
        elif isinstance(today, float):
            today = time_factory(today)
        timelist = list(today)
        if year or month or day or dateonly:
            if year:
                timelist[0] += year
            if month:
                timelist[1] += month
            if day:
                timelist[2] += day
            if dateonly:
                timelist[3:6] = [0, 0, 0]
        if nextmonth:
            timelist = list(time_factory(timegm(timelist)))
            if timelist[2] != 1:
                timelist[1] += 1
                timelist[2] = 1
        val = time_to_secs(timelist)
        if mask is None:
            return val
        else:
            return strftime(mask or default_date_format, time_factory(val))

    return calc_date


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
