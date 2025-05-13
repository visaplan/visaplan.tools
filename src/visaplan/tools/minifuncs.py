# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Very small functions
"""
# Python compatibility:
from __future__ import absolute_import, print_function

from six import string_types as six_string_types

# Standard library:
from decimal import Decimal

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"

__all__ = [
           'gimme_None',
           'gimme_True',
           'gimme_False',
           'gimmeConst__factory',
           'makeBool',
           'NoneOrBool',
           'NoneOrInt',
           'NoneOrString',
           'IntOrOther',
           'extract_float',
           'translate_dummy',
           'check_kwargs',
           ]
# -------------------------------------------- [ Daten ... [
LOWER_TRUE = frozenset('yes y ja j true on'.split() +
                       [True])
# würde für False nicht funktionieren ... daher:
LOWER_FALSE = frozenset('no n nein false off'.split())
# -------------------------------------------- ] ... Daten ]


def gimme_None(*args, **kwargs):
    return None


def gimme_True(*args, **kwargs):
    return True


def gimme_False(*args, **kwargs):
    return False


def gimmeConst__factory(val):
    def f(*args, **kwargs):
        return val
    f.__name__ = 'gimme%r' % val
    return f


def makeBool(val, default=None):
    """
    gib einen Wahrheits- oder Zahlenwert zurueck

    val -- ein Variablenwert, meistens der Wert einer Request-Variablen;
           ein String.
           ACHTUNG - wenn der Zahlenwert 0 uebergeben wird und default 'yes'
           oder aehnliches ist, wird das Ergebnis True sein!

    default -- Standardwert (ein String!) fuer den Fall, dass val leer ist
               (zumeist None oder der Leerstring); wenn leer, 'no'

    >>> makeBool('True')
    True
    >>> makeBool('')
    False
    >>> makeBool('', 'yes')
    True
    >>> makeBool(42)
    42
    >>> makeBool('1')
    1
    >>> makeBool(None)
    False

    Für den häufigen Fall, daß eine Option abgefragt wird:

    >>> options = {}
    >>> makeBool(options.get('verbose'), 'false')
    False

    Bei fehlerhaften Werten gibt es einen ValueError:

    >>> makeBool('vielleicht')
    Traceback (most recent call last):
    ...
    ValueError: invalid literal for int() with base 10: 'vielleicht'

    VORSICHT bei der Kombination von Zahlen mit default='yes'!
    Wenn die Zahl als String übergeben wird, ist alles gut:

    >>> makeBool('0', default='yes')
    0
    >>> makeBool('42', default='yes')
    42

    Nun kommt der Fehler.
    Wird 0 als fertige Zahl übergeben, gewinnt bisher der Vorgabewert:

    >>> makeBool(0, default='yes')
    True

    Hierauf bitte nicht verlassen!
    Dieses Verhalten wird mutmaßlich in einer späteren Version korrigiert werden.
    """
    try:
        if default is None:
            s = (val or 'no').strip().lower()
        else:
            s = (val or default or 'no').strip().lower()
    except (TypeError, AttributeError):
        s = val
    if s in LOWER_TRUE:
        return True
    if s in LOWER_FALSE:
        return False
    return int(s)


def NoneOrBool(val):
    """
    Für Fälle, wo ein logischer Wert eben doch None sein darf
    (um z. B. bei Query-String-Generierung übergangen zu werden).

    >>> NoneOrBool('')
    >>> NoneOrBool('True')
    True
    """
    if val in (None, '', 'None'):
        return None
    elif isinstance(val, six_string_types):
        val = val.strip().lower()
        if val in ('', 'none'):
            return None
        return bool(makeBool(val))
    else:
        return bool(val)


def NoneOrInt(val):
    """
    Eine valide Ganzzahl, oder None ("int('')" ergibt einen ValueError)

    >>> NoneOrInt(' ')
    >>> NoneOrInt(' 3 ')
    3
    """
    if val in (None, '', 'None'):
        return None
    elif isinstance(val, six_string_types) and not val.strip():
        return None
    try:
        return int(val)
    except KeyError:
        return None
    except (TypeError, ValueError) as e:
        print('*** NoneOrInt: Kann %(val)r nicht nach int konvertieren' % locals())
        raise


def NoneOrString(val):
    """
    Ein nicht-leerer String (ggf. um randständigen Leerraum gekürzt)
    oder None.

    >>> NoneOrString(' ')
    >>> NoneOrString(' honk ')
    'honk'
    """
    if val is None:
        return None
    val = val.strip()
    return val or None


def IntOrOther(val):
    """
    Zum Bauen von Datenbank-Abfragen:
    Gib eine Ganzzahl zurück, wenn möglich, und ansonsten einen String oder
    None.

    >>> IntOrOther('42')
    42
    >>> IntOrOther(' 42 ')
    42
    >>> IntOrOther(None)
    >>> IntOrOther('x')
    'x'
    """
    if val is None:
        return val
    try:
        return int(val)
    except ValueError:
        return val


def extract_float(s):
    """
    Extrahiere eine Zahl aus einem String, der eine Währungsangabe enthält.

    >>> extract_float('600,00 &euro;')
    600.0

    >>> extract_float('700.00 $')
    700.0

    Wenn der übergebene Wert bereits eine Zahl ist,
    gib ihn unverändert zurück:
    >>> extract_float(600.0)
    600.0
    """
    if isinstance(s, (float, int, Decimal)):
        return s
    if not s:
        raise ValueError("Can't extract float from %(s)r"
                         % locals())
    for subs in s.split():
        try:
            if ',' in subs:
                return float(subs.replace(',', '.'))
            else:
                return float(subs)
        except ValueError:
            pass
    raise


def translate_dummy(s, *args, **kwargs):
    """
    Eine Dummy-Funktion, die den übergebenen String unverändert zurückgibt.
    Zu verwenden, wenn eine _-Funktion eigentlich nichts zu tun hat -
    Standardfall: die Übersetzung wird vom message-Adapter erledigt -,
    aber zum Auffinden der Message-IDs benötigt wird.

    Um jegliche weitere Argumente zuzulassen, die der Parser ggf.
    auswertet (z. B. 'mapping'), werden diese ignoriert.

    >>> translate_dummy('test')
    'test'
    """
    return s


def check_kwargs(checked_kwargs, **my_kwargs):
    """
    A little helper for functions which accept many keyword arguments;
    checks for invalid keyword arguments in the given dict and (by default)
    raises the expected TypeError.

    >>> check_kwargs({'unknown': 42})
    Traceback (most recent call last):
    ...
    TypeError: Unknown option 'unknown' found!

    You can choose to continue processing even for unknown keys;
    in this case, the boolean result tells whether there have been warnings:
    >>> check_kwargs({'unknown': 42, 'strict': False})
    True

    In such cases you'll likely want some logging.
    >>> class MiniLog(object):
    ...     def __init__(self):
    ...         self._log = []
    ...     def warn(self, msg, mapping=None):
    ...         if mapping is not None:
    ...             msg %= mapping
    ...         self._log.append(msg)
    ...     def __str__(self):
    ...         return self._log[-1]

    If a logger is given, `strict` defaults to False, and warnings are logged:
    >>> logger=MiniLog()
    >>> check_kwargs({'unknown': 42}, logger=logger)
    True
    >>> str(logger)
    "Unknown option 'unknown' found!"

    It is quite common for the checked dictionary to be empty:
    >>> check_kwargs({})
    False

    The checking function itself accepts named-only options, and of course it
    checks whether it is called correctly.
    It is always strict when it comes to its own options, and it checks its own
    options first:
    >>> check_kwargs({'any': 42}, bogus=42)
    Traceback (most recent call last):
    ...
    TypeError: Unknown option 'bogus' found!
    >>> check_kwargs({'any': 42})
    Traceback (most recent call last):
    ...
    TypeError: Unknown option 'any' found!

    NOTE that currently this check is performed *only* if a non-empty checked
    arguments dict was given; this is because we had a recursion problem
    otherwise:

    >>> check_kwargs({}, bogus=42)
    False

    This means you might have an error in your usage and not be aware of it
    until the function finds a non-empty (while possibly still acceptable)
    input dictionary.

    We consider this acceptable, since you'll get an information about the
    rejected option name, and the exception raised is the same.

    Now for the more exotic options.
    You might have a convention which uses another option name than 'strict':

    >>> check_kwargs({'pingelig': False})
    Traceback (most recent call last):
    ...
    TypeError: Unknown option 'pingelig' found!

    You can tell the function about this name:

    >>> check_kwargs({'pingelig': False}, strict_key='pingelig')
    False

    You might put your options in a dict for easier reusing them:
    >>> check_kw = dict(strict_key='pingelig', logger=logger)
    >>> check_kwargs({'pingelig': False, 'bogus': 42}, **check_kw)
    True
    >>> str(logger)
    "Unknown option 'bogus' found!"

    But you can override the laxness from the checked dict and choose to be
    strict anyway:
    >>> check_kwargs({'pingelig': False, 'bogus': 42}, strict=True, **check_kw)
    Traceback (most recent call last):
    ...
    TypeError: Unknown option 'bogus' found!

    The `strict` key is considered to be aimed for this checking function,
    so it is consumed by default:

    >>> opt = {'strict': True}
    >>> check_kwargs(opt)
    False
    >>> opt
    {}

    You can retain it, however, for further use:

    >>> opt = {'strict': True}
    >>> check_kwargs(opt, strict_pop=False)
    False
    >>> opt
    {'strict': True}

    And finally, you can decide you don't want this `strict` handling at all,
    and tell the function you don't have a `strict_key`:

    >>> check_kwargs({'strict': False}, strict_key=None)
    Traceback (most recent call last):
    ...
    TypeError: Unknown option 'strict' found!

    """
    # short-circuit check: if the given dict is empty, it can't contain unknown
    # keys. NOTE that in this case, the keyword arguments of the checking
    # function itself are not checked!  This is to avoid a recursion problem.
    if not checked_kwargs:
        return False

    pop = my_kwargs.pop
    allowed = pop('allowed', None)
    if allowed is None:
        allowed = set()
    elif isinstance(allowed, six_string_types):
        raise ValueError('allowed option must be a non-string sequence,'
                         ' preferably a set! (%(allowed)r)'
                         % locals())
    else:
        allowed = set(allowed)

    logger = pop('logger', None)
    strict_pop = pop('strict_pop', True)
    strict_key = pop('strict_key', 'strict')
    strict_default = pop('strict_default', logger is None)
    strict = None
    if 'strict' in my_kwargs:
        strict = pop('strict')

    # We make sure *this function* is called correctly.
    check_kwargs(my_kwargs)

    if strict is not None:
        pass
    elif not strict_key:
        strict = True
    else:
        if strict_pop:
            strict = checked_kwargs.pop(strict_key, strict_default)
        else:
            strict = checked_kwargs.get(strict_key, strict_default)
            allowed.add(strict_key)
    res = False
    for key in checked_kwargs.keys():
        if key in allowed:
            continue
        elif strict:
            raise TypeError('Unknown option %(key)r found!' % locals())
        else:
            res = True
            if logger is not None:
                # TODO: we might want to extract some information
                #       from the stacktrace here ...
                logger.warn('Unknown option %(key)r found!', locals())
    return res


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
