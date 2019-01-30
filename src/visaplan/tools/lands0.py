# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
lands0 -- "lists and strings 0"

Die Funktionen dieses Moduls haben mit Strings und Listen zu tun;
ihre Namen, Signaturen etc. sind noch vorläufig
"""

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"

# Standardmodule
from string import strip


__all__ = [
           # -------------- [ aus unitracc.tools.forms ... [
           'list_of_strings',
           'string_of_list',
           'as_new_list',
           'lines_to_list',
           # -------------- ] ... aus unitracc.tools.forms ]
           # --------------- [ aus unitracc.tools.misc ... [
           'makeListOrNone',
           'makeListOfStrings',
           'makeSet',          # verdaut auch None usw.
           'groupstring',      # wie tomcom-Adapter groupstring
           # --------------- ] ... aus unitracc.tools.misc ]
           ]


# ------------------------- [ aus unitracc.tools.forms ... [
def list_of_strings(val, splitchar=None, splitfunc=None):
    r"""
    Gib eine Liste zurück, ohne allerdings - wie es die eingebaute
    list-Funktion tun würde - einen String automatisch in eine Liste seiner
    Zeichen aufzusplitten.

    >>> a_list = list('abc')
    >>> a_list
    ['a', 'b', 'c']
    >>> list_of_strings('abc')
    ['abc']

    Tupel werden zu Listen konvertiert, Sets dabei sortiert;
    None ergibt eine leere Liste;
    Listen werden direkt zurückgegeben:
    >>> a_tuple = tuple('abc')
    >>> list_of_strings(a_tuple)
    ['a', 'b', 'c']
    >>> list_of_strings(a_list) is a_list
    True
    >>> list_of_strings(None)
    []

    "Leere Zeilen" werden *nicht* ausgefiltert
    (hierfür ist besser --> lines_to_list zu verwenden):
    >>> leading_empty = '\neins\nzwei'
    >>> list_of_strings(leading_empty, '\n')
    ['', 'eins', 'zwei']
    """
    if val is None:
        return []
    elif isinstance(val, list):
        # aus Performanzgründen nur das erste Element prüfen:
        if val and not isinstance(val[0], basestring):
            raise ValueError('list_of_strings: list contains non-strings!'
                             ' [%r%s]' % (val[0],
                                          val[1:] and ', ...' or ''))
        return val
    elif isinstance(val, set):
        return list_of_strings(sorted(val))
    elif isinstance(val, basestring):
        pass
    else:
        return list_of_strings(list(val))

    if splitfunc is None:
        if splitchar is None:
            return [val]
        else:
            return val.split(splitchar)
    elif splitchar is None:
        return splitfunc(val)
    else:
        raise ValueError('list_of_strings(%(val)r):'
                         ' *either* splitchar (%(splitchar)r)'
                         ' *or* splitfunc (%(splitfunc)r)!'
                         % locals())


def string_of_list(val, splitchar='\n', transform=strip):
    r"""
    Gib einen String zurück:
    - Wenn <val> ein String ist, unverändert;
    - wenn eine Liste oder ein Tupel, unter Verwendung von <splitchar>
      verkettet (Bezeichnung angelehnt an --> list_of_strings)

    Nützlich im Zusammenhang mit Formularen, bei denen Stringwerte benötigt
    werden, um Eingabeelemente vorzubelegen, deren Werte in Listen konvertiert
    werden (z. B. :lines-Suffix)

    >>> string_of_list(['a', 'b'])
    'a\nb'
    >>> string_of_list('a\nb')
    'a\nb'

    Wenn die Transformationsfunktion nicht None ist (Standardwert:
    string.strip), werden auch leere Zeilen ausgefiltert:

    >>> string_of_list(['a', '', 'b'])
    'a\nb'

    """
    if val is None:
        return ''
    elif isinstance(val, basestring):
        if transform is not None:
            return transform(val)
        return val
    elif transform is None:
        return splitchar.join(val)
    else:
        return splitchar.join([a
                               for a in [transform(line)
                                         for line in val]
                               if a])


def lines_to_list(s):
    r"""
    Konvertiere einen "mehrzeiligen" String in eine Liste

    >>> leading_empty = '\neins\nzwei'
    >>> lines_to_list(leading_empty)
    ['eins', 'zwei']

    >>> lines_to_list('')
    []
    """
    if isinstance(s, basestring):
        s = s.splitlines()
    return filter(None, [item.strip()
                         for item in s])


def as_new_list(val, splitfunc=None):
    """
    >>> as_new_list('eins,zwei')
    ['eins', 'zwei']
    >>> liz1 = as_new_list('eins')
    >>> liz1
    ['eins']
    >>> liz2 = as_new_list(liz1)
    >>> liz2 == liz1
    True
    >>> liz2 is liz1
    False
    """
    if val is None:
        return []
    if not isinstance(val, basestring):
        return list(val)
    if splitfunc is None:
        return [s.strip() for s in val.split(',')]
    return splitfunc(val)
# ------------------------- ] ... aus unitracc.tools.forms ]

# -------------------------- [ aus unitracc.tools.misc ... [
def makeListOrNone(val, default=None, ch=','):
    """
    Gib eine gefüllte Liste oder None zurück.

    >>> makeListOrNone('eins')
    ['eins']
    >>> makeListOrNone('eins,zwei')
    ['eins', 'zwei']
    >>> makeListOrNone('')
    >>> makeListOrNone(', ,')
    >>> makeListOrNone(None, ', ,')
    >>> makeListOrNone(None, 'drei')
    ['drei']
    >>> makeListOrNone(None, default=['null'])
    ['null']
    """
    if val is None:
        if default is None:
            return default
        else:
            return makeListOrNone(default)
    elif not val:
        return None
    elif isinstance(val, basestring):
        val = val.split(ch)
        tmp = [s.strip() for s in val]
        return [s for s in tmp
                if s] or None
    else:
        return list(val) or None


def makeListOfStrings(s, default=None):
    r"""
    für Transmogrifier: String ggf. mit splitlines aufsplitten
    und leere Strings weglassen

    >>> s = '\n  eins \n zwei drei \n \n'
    >>> makeListOfStrings(s)
    ['eins', 'zwei drei']
    >>> makeListOfStrings('  ', ['default'])
    ['default']
    """
    if isinstance(s, (list, tuple)):
        return list(s)
    res = []
    for chunk in s.splitlines():
        val = chunk.strip()
        if val:
            res.append(val)
    if default is not None and not res:
        return default
    return res


def makeSet(s, **kwargs):
    r"""
    Gib jedenfalls ein Set zurück (außer in dem entarteten Fall,
    daß als default explizit ein Nicht-Set übergeben wurde)

    >>> s = '\n  \n zwei drei \n \n'
    >>> makeSet(s)
    set(['zwei drei'])
    >>> makeSet('  ')
    set([])
    >>> makeSet(None)
    set([])
    >>> makeSet('  ', default=None)
    >>> makeSet(42)
    set([42])
    """
    try:
        default = kwargs.pop('default')
    except KeyError:
        has_default = False
    else:
        has_default = True
    if s is None:
        if has_default:
            return default
        return set()
    elif isinstance(s, set):
        pass
    elif isinstance(s, (list, tuple)):
        s = set(s)
    elif isinstance(s, basestring):
        tmp = set()
        for chunk in s.splitlines():
            val = chunk.strip()
            if val:
                tmp.add(val)
        s = tmp
    else:
        return set([s])
    if s:
        return s
    elif has_default:
        return default
    return set()


def groupstring(s, size=2):
    """
    Wie TomCom-Adapter groupstring: Teile einen String in gleiche Häppchen
    einer Maximalgröße <size> auf

    >>> groupstring('abcdef')
    ['ab', 'cd', 'ef']
    >>> groupstring('abc')
    ['ab', 'c']
    """
    return [s[i:i + size]
            for i in xrange(0, len(s), size)
            ]
# -------------------------- ] ... aus unitracc.tools.misc ]


if __name__ == '__main__':
    class MockRequest(dict):
        # kopiert ins mock-Modul
        def __init__(self, referer=None, **kwargs):
            self['HTTP_REFERER'] = referer
            self['ACTUAL_URL'] = kwargs.pop('actual_url', referer)
            self.form = kwargs

    import doctest
    doctest.testmod()