# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Tools for time calculations
"""

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (0,
           4,  # make_safe_decoder, now --> .coding
           9,  # unique_union,      now --> .sequences
           )
__version__ = '.'.join(map(str, VERSION))


# Standardmodule
from time import localtime, strftime, mktime, strptime

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
                                default_date_format='%Y-%m-%d'):
    """
    Gib eine Funktion zurück, die ein Standarddatum erzeugt, z. B. das
    Standard-Ablaufdatum einer TAN (--> @@tan.utils.default_expiration_date).

    >>> heute=strptime('2.5.2014', '%d.%m.%Y')
    >>> f = make_defaulttime_calculator(year=1, nextmonth=True)
    >>> f(today=heute)
    '2015-06-01'
    >>> f(today=heute, mask=None)
    1433109600.0
    >>> f2 = make_defaulttime_calculator(day=90, nextmonth=False)
    >>> f2(today=heute)
    '2014-07-31'
    >>> f2(today=heute, mask=None)
    1406757600.0
    """

    def calc_date(mask='', today=None, dateonly=dateonly):
        if today is None:
            today = localtime()
        elif isinstance(today, float):
            today = localtime(today)
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
            timelist = list(localtime(mktime(timelist)))
            if timelist[2] != 1:
                timelist[1] += 1
                timelist[2] = 1
        val = mktime(timelist)
        if mask is None:
            return val
        else:
            return strftime(mask or default_date_format, localtime(val))

    return calc_date


if __name__ == '__main__':
    import doctest
    doctest.testmod()
