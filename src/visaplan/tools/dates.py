# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Tools zur Transformation von Datumswerten
"""

# Python compatibility:
from __future__ import absolute_import

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"


# Standard library:
from datetime import date
from time import strftime, strptime

__all__ = (
           'make_date_parser',
           'parse_date',  # erzeugt durch Aufruf von --> make_date_parser
           'make_date_formatter',
           )


# -------------------------- [ aus Products.unitracc.tools.forms ... [
def make_date_parser(cls=date, fmt='%d.%m.%Y'):
    """
    Erzeuge eine Funktion, die ein Datum parst und einen Datumswert zurückgibt

    cls -- Klasse (oder Factory), die aus drei unbenannten Argumenten (y, m, d)
           ein Datum erzeugt

    fmt -- das zuerst zu probierende strftime-Datumsformat

    >>> import datetime
    >>> pd = make_date_parser()
    >>> pd('2.5.2016')
    datetime.date(2016, 5, 2)
    >>> pd('2016-05-03')
    datetime.date(2016, 5, 3)

    Wenn die Klasse als None angegeben wird, wird ein Tupel zurückgegeben:
    >>> pdt = make_date_parser(cls=None)
    >>> pdt('4.5.2016')
    (2016, 5, 4)

    Siehe auch unitracc@@groupsharing.utils.makedate
    (mit default-Wert, ohne Verwendung von strptime)
    """
    if isinstance(fmt, (list, tuple)):
        formats = list(fmt)
    else:
        formats = [fmt]
    formats.extend(['%d.%m.%Y', '%Y-%m-%d'])
    try_formats = []
    for df in formats:
        if df not in try_formats:
            try_formats.append(df)

    def parse_date(start):
        if not isinstance(start, tuple):
            tup = None
            for df in try_formats:
                try:
                    tup = strptime(start, df)
                except ValueError:
                    pass
                else:
                    break
            if tup is None:
                raise ValueError("Didn't understand date specification '%(start)s'"
                                 % locals())
        if cls is None:
            return tup[:3]
        return cls(*tup[:3])

    return parse_date

parse_date = make_date_parser()
# -------------------------- ] ... aus Products.unitracc.tools.forms ]

# ------------------ [ aus Products.unitracc@@groupsharing.utils ... [
def make_date_formatter(context=None, **kwargs):
    """
    Gib eine Funktion zurück, die Datumswerte formatiert;
    die Datumswerte dürfen leer sein (wie z. B. beim Lesen aus einer Datenbank)

    Das Datumsformat könnte vom Kontext abhängen, insbesondere von der aktiven
    Sprache; daher wird die Funktion jeweils zur (i.d.R. mehrfachen) Verwendung
    erzeugt.

    >>> f = make_date_formatter()

    Es können datetime.date-Werte übergeben werden:

    >>> d1 = date(2018, 8, 15)
    >>> d1
    datetime.date(2018, 8, 15)
    >>> f(d1)
    '15.08.2018'

    Es können auch Sequenzen (Listen oder Tupel) nach der von strftime
    verstandenen Konvention übergeben werden. Da strftime ein 9-Tupel oder eine
    entsprechend lange Liste erwartet, werden die fehlenden Angaben ergänzt.

    >>> f((2018, 8, 14))
    '14.08.2018'
    >>> f([2018, 8, 16])
    '16.08.2018'

    "Leere" Werte führen zur Rückgabe von None:

    >>> f(0)
    >>> f(())
    """
    fmt = kwargs.pop('fmt', '%d.%m.%Y')
    nine = (None, None, None,
            0, 0, 0, 0, 0, -1)

    def format_date(val):
        if not val:
            return None
        if isinstance(val, (tuple, list)):
            L = len(val)
            if L < 9:
                return strftime(fmt, tuple(val)+nine[L:])
            return strftime(fmt, val)
        return val.strftime(fmt)

    return format_date
# ------------------ ] ... aus Products.unitracc@@groupsharing.utils ]


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
