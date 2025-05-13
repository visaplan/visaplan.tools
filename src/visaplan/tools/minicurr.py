# -*- coding: utf-8 -*-
"""
Minimal currency support

We are aware of the iso4217 installable package
which provides an enum containing currency info
(using the enum34 package to provide Python 3.4 enums for pre-3.4 Pythons),
but that's not what we currently need.

The ISO4217 Mirror dict maps some popular currency specifications to their
respective ISO 4217 symbols:

>>> ISO4217['euro']
'EUR'
"""

# Python compatibility:
from __future__ import absolute_import

__all__ = [
    'ISO4217',
    ]

try:
    # Local imports:
    from .classes import Mirror
except (ImportError, ValueError):
    if __name__ == '__main__':
        Mirror = dict
    else:
        raise

_Aliases = {
    'EUR': [u'€', 'Euro', 'euro'],
    'JPY': [u'¥', 'yen', 'Yen', 'YEN'],
    'USD': ['US$', '$'],
    }

ISO4217 = Mirror()
for key, aliases in _Aliases.items():
    keys = set(aliases)
    keys.add(key)
    for ali in keys:
        ISO4217[ali] = key


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()

# vim: ts=8 sts=4 sw=4 si et
