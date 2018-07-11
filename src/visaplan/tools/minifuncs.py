# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Very small functions
"""

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
    gib einen Wahrheitswert zurueck

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
    >>> makeBool('1')
    1
    >>> makeBool(None)
    False

    Für den häufigen Fall, daß eine Option abgefragt wird:

    >>> options = {}
    >>> makeBool(options.get('verbose'), 'false')
    False
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
    elif isinstance(val, basestring):
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
    elif isinstance(val, basestring) and not val.strip():
        return None
    try:
        return int(val)
    except KeyError:
        return None
    except (TypeError, ValueError) as e:
        print '*** NoneOrInt: Kann %(val)r nicht nach int konvertieren' % locals()
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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
