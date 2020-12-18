# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Tools für Python-Dictionarys
"""
# Python compatibility:
from __future__ import absolute_import

from six import string_types as six_string_types
from six.moves import filter

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"

# Standard library:
from collections import defaultdict
from string import strip

# Local imports:
from visaplan.tools.minifuncs import NoneOrString

__all__ = (
           'subdict',
           'subdict_onekey',
           'subdict_forquery',  # see as well --> .sql.subdict_ne
           # Ergänzung von Schlüsseln:
           'make_key_injector',
           # Extraktion von Werten, mit Vorgabe und Factorys:
           'getOption',  # von einem Dict (z. B. für Transmogrifier)
           # kleine Helferlein:
           'updated',  # ungefähr analog sorted; für dict-Objekte
           'update_dict',  # changes and deletions
           )


def subdict(form, keys=None, defaults={},
            defaults_factory=None,
            factory_map={},
            keyfunc=None,
            **kwargs):
    """
    Extrahiere die übergebenen Schlüssel aus dem übergebenen dict
    (mutmaßlich einem von Zope generierten REQUEST.form-Objekt);
    mit do_pop=True werden die Schlüssel dabei entfernt.

    >>> bsp = {'user': 'heinz', 'password': 'geheim',
    ...        'confirm_password': 'geheim',
    ...        'other': 'otherval',
    ...        }
    >>> subdict(bsp, ['user'])
    {'user': 'heinz'}

    Wenn ein <defaults>-Dict übergeben wird, werden diesem die fehlenden
    Werte entnommen; ob dabei ggf. ein KeyError auftritt, hängt von diesem Dict
    ab (ggf. ein defaultdict verwenden, oder aber vorzugsweise eine
    <defaults_factory>).

    >>> deflts = defaultdict(lambda: 'gips doch')
    >>> subdict(bsp, ['gipsnich'], deflts)
    {'gipsnich': 'gips doch'}

    Das zurückgegebene dict-Objekt enthält *genau* die als <keys> angegebenen
    Schlüssel; wenn <defaults> für alle ggf. Schlüssel Werte enthält *oder* die
    fehlenden Werte von der <defaults_factory> erzeugt werden können, wird das
    auch sicher klappen.

    Mit do_pop=1 (nur als Schlüsselwortargument) werden die extrahierten
    Schlüssel entfernt:

    >>> subdict(bsp, ['other'], do_pop=1)
    {'other': 'otherval'}
    >>> sorted(bsp.items())
    [('confirm_password', 'geheim'), ('password', 'geheim'), ('user', 'heinz')]

    Für global definierte <defaults> ist es üblicherweise nicht erwünscht,
    daß fehlende Werte durch Abfrage im Einzelfall erzeugt werden;
    in diesem Fall eine <defaults_factory> übergeben, die zum Erzeugen eines
    defaultdict-Objekts verwendet wird.

    Wenn <keys> keine Sequenz von Schlüsseln, sondern None ist, werden alle
    existierenden Schlüssel des <form>-Dictionarys verwendet.  Das ergibt genau
    dann einen Sinn, wenn eine <factory_map> übergeben wird.

    Die <factory_map> gibt für jeden Schlüssel eine Funktion zurück,
    die den entsprechenden Wert "normalisiert":

    >>> def strip(a):
    ...     try:
    ...         return a.strip()
    ...     except (AttributeError, TypeError):
    ...         return a
    >>> sd = subdict({'username': 'heinz ',
    ...               'age': 18,
    ...               'nothing': None,
    ...               'name': u'Heinz Kunz '},
    ...              factory_map=defaultdict(lambda: strip))
    >>> sorted(sd.items())
    [('age', 18), ('name', u'Heinz Kunz'), ('nothing', None), ('username', 'heinz')]

    Wenn eine Funktion <keyfunc> übergeben wird (vorerst nur mit keys=None),
    werden nur Schlüssel extrahiert, für die diese Funktion True zurückgibt:

    >>> subdict(bsp, keyfunc=lambda k: not 'password' in k)
    {'user': 'heinz'}
    """
    do_pop = kwargs.pop('do_pop', False)
    if do_pop:
        get = form.pop
    else:
        get = form.get
    if defaults_factory is not None:
        defdict = defaultdict(defaults_factory)
        defdict.update(defaults)
    else:
        defdict = defaults
    res = {}
    aliases = {}
    if keys is None:
        keys = list(form.keys())
    else:
        # Alternativer Name für ersten Schlüssel
        primary_fallback = kwargs.pop('primary_fallback', None)
        if primary_fallback is not None:
            assert primary_fallback not in keys, \
                    'Das Alias darf keiner der normalen Schluessel sein'
            aliases[keys[0]] = primary_fallback

    if keyfunc is not None:
        keys = list(filter(keyfunc, keys))

    for key in keys:
        if key in form:
            val = get(key)
            try:
                func = factory_map[key]
            except KeyError:
                res[key] = val
            else:
                res[key] = func(val)
        elif key in aliases and aliases[key] in form:
            val = get(aliases[key])
            try:
                func = factory_map[key]
            except KeyError:
                res[key] = val
            else:
                res[key] = func(val)
        else:
            res[key] = defdict[key]
    return res


def subdict_onekey(form, firstof, strict=True):
    """
    Für ähnliche Zwecke wie --> subdict, aber zur Extraktion nur eines Schlüssels

    >>> given = {'project_id': 42, 'p2_result': None}
    >>> subdict_onekey(given, ['p2_result', 'project_id'])
    {'project_id': 42}
    """
    for key in firstof:
        try:
            val = form[key]
        except KeyError:
            if strict:
                raise
        else:
            if val is not None:
                return {key: val}
    return {}


def subdict_forquery(*args, **kwargs):
    """
    Zur Verwendung mit Datenbank-Funktionen (Erzeugen von query_data):
    Es soll vermieden werden, eine leere Bedingung zu übergeben, z. B. um nicht
    versehentlich alle Datensätze einer Tabelle zu ändern oder zu löschen.

    Aufruf von --> subdict mit anschließender Modifikation des Ergebnisses:
    Es werden alle Schlüssel verworfen, die auf einen Wert None verweisen.

    >>> src = {'a': 1, 'b': None, 'c': 3}
    >>> kwargs = {'keys': None}
    >>> sorted(subdict(src, **kwargs).items())
    [('a', 1), ('b', None), ('c', 3)]
    >>> sorted(subdict_forquery(src, **kwargs).items())
    [('a', 1), ('c', 3)]

    Wenn das Ergebnis leer ist, tritt ein ValueError auf:
    >>> kwargs = {'keys': ['b']}
    >>> subdict(src, **kwargs)
    {'b': None}
    >>> subdict_forquery(src, **kwargs)
    Traceback (most recent call last):
      ...
    ValueError: subdict {'b': None} not sufficient for Query!

    Dies kann mit strict=False unterbunden werden:
    >>> kwargs['strict'] = False
    >>> subdict_forquery(src, **kwargs)
    {}
    """
    strict = kwargs.pop('strict', True)
    tmp = subdict(*args, **kwargs)
    res = dict([tup
                for tup in tmp.items()
                if tup[1] is not None
                ])
    if strict and not res:
        raise ValueError('subdict %(tmp)s not sufficient for Query!'
                         % locals())
    return res


# ------------ [ aus Products.unitracc.tools.visaplan.tools.misc ... [
# (alter Name: key_injector)
def make_key_injector(srckey, func, destkey, errmask):
    """
    Erzeuge eine Subroutine, die das übergebene dict-Objekt um einen
    Schlüssel mit Wert ergänzt, der mit Hilfe der übergebenen Funktion
    berechnet wird:
    "Verwende <func>, um für jedes <dic> aus <dic>[<srckey>] den Wert
    <dic>[<destkey>] zu ermitteln.
    Die Funktion <func> gibt ein dict zurück, das den Schlüssel <destkey>
    enthält; der verwiesene Wert wird verwendet.
    Verwende im Fehlerfall die Textmaske <errmask>, um aus <dic> eine Text zu
    erzeugen, der anstelle eines "richtigen" Werts verwendet wird."

    >>> dic = {'group_id': 'group_abc'}
    >>> srckey = 'group_id'
    >>> func = lambda x: {'group_title': '%s-Gruppe' % x.split('_', 1)[-1].upper()}
    >>> destkey = 'group_title'
    >>> errmask = 'Unknown group "%(group_id)s"'
    >>> extend = make_key_injector(srckey, func, destkey, errmask)
    >>> extend(dic)
    >>> dic
    {'group_id': 'group_abc', 'group_title': 'ABC-Gruppe'}

    Im Unterschied zu den dict-Klassen aus visaplan.tools.classes wird hier keine
    dict-Unterklasse angelegt, sondern eine Hilfsfunktion zur Manipulation
    völlig gewöhnlicher dict-Objekte erzeugt.
    """
    cachedict = {}

    def inject_key(dic):
        # das übergebene dict hat *immer* den Schlüssel <srckey>:
        valin = dic[srckey]
        try:
            dic[destkey] = cachedict[valin]
            # print valin, '-->', cachedict[valin]
        except KeyError:
            try:
                gotdic = func(valin)
            except KeyError:
                # evtl. noch weitere Exceptions abfangen; im Anwendungsfall
                # "Gruppeninformationen ermitteln" tritt bei nicht vorhandenen
                # Gruppen ein KeyError auf
                valout = errmask % dic
            else:
                # das Ergebnis-dict hat *immer* den Schlüssel <destkey>:
                valout = gotdic[destkey]
            cachedict[valin] = valout
            # print valin, '==>', valout
            dic[destkey] = valout
    return inject_key
# ------------ ] ... aus Products.unitracc.tools.visaplan.tools.misc ]


def updated(dic, **kwargs):
    """
    Gib das übergebene dict mit etwaigen Modifikationen zurück

    >>> dic = {'eins': 1}
    >>> dic
    {'eins': 1}
    >>> sorted(updated(dic, zwei=2).items())
    [('eins', 1), ('zwei', 2)]
    >>> dic
    {'eins': 1}

    Eine Kopie wird nur erstellt, wenn kwargs nicht leer ist:

    >>> dic2 = updated(dic)
    >>> dic2 is dic
    True

    """
    if not kwargs:
        return dic
    res = dict(dic)
    res.update(kwargs)
    return res


def update_dict(form, changes, deletions):
    """
    Ändere das übergebene dict in-place und nimm Löschungen vor; da das Objekt
    selbst geändert wird (vergleichbar der Methode dict.update), wird stets
    None zurückgegeben.

    >>> dic1 = {'eins': 1, 'zwei': 2, 'drei': 3}
    >>> update_dict(dic1, {'zwei': 22, 'vier': 4}, ['drei'])
    >>> sorted(dic1.items())
    [('eins', 1), ('vier', 4), ('zwei', 22)]

    Es wird erst gelöscht und dann "upgedatet"; ein Schlüssel aus <deletions>
    kann somit im Resultat durchaus vorhanden sein, wenn er in den
    anzuwendenden <changes> enthalten ist:

    >>> dic1 = {'eins': 1, 'zwei': 2, 'drei': 3}
    >>> update_dict(dic1, {'zwei': 22, 'vier': 44}, ['zwei', 'drei'])
    >>> sorted(dic1.items())
    [('eins', 1), ('vier', 44), ('zwei', 22)]

    See as well --> .classes.ChangesCollector
    """
    for key in deletions:
        if key in form:
            del form[key]
    if changes:
        form.update(changes)
    return


# --------------------------- [ aus Products.unitracc.tools.misc ... [
def getOption(odict, key, default=None, factory=NoneOrString,
              choices=None,
              use_default=2,
              label=None,
              reverse=None):
    r"""
    Z. B. für Transmogrifier: Optionenauswertung mit Behandlung der Frage von
    nicht oder leer angegebenen Werten

    odict - ein dict mit Optionen; als Werte werden Strings erwartet, die ggf.
            mit der jeweils angegebenen factory konvertiert werden.
    key - der Optionsname
    default - siehe auch use_default. Wenn ein String, wird ggf. die
              factory-Funktion angewendet.
    factory - Funktion zur Transformation von Strings
    choices - für string-Optionen: erlaubte Werte.
              Wenn indizierbar, wird ggf. der erste Wert als Vorgabe verwendet
    use_default -
        wenn >= 1, verwenden wenn kein Wert vorhanden
        wenn >= 2, auch dann, wenn ein leerer Wert (Leerstring) vorhanden ist
    label - IGNORIERT
              (in Dict-Objekten, die zum Aufruf verwendet werden, ggf. die
              Beschriftung einer Option)
    reverse - IGNORIERT
              (in Dict-Objekten, die zum Aufruf verwendet werden, ggf. eine
              "Umkehrfunktion" zur <factory> - also z.B. string_of_list zur
              Factory makeListOfStrings)

    >>> o = dict(path='\n\n eins \n', doit='  yes ')
    >>> getOption(o, 'path')
    'eins'
    >>> from visaplan.tools.lands0 import makeListOfStrings
    >>> getOption(o, 'path', None, makeListOfStrings)
    ['eins']
    >>> getOption(o, 'nowhere', None, makeListOfStrings)
    >>> from visaplan.tools.minifuncs import makeBool, NoneOrInt
    >>> getOption(o, 'doit', 'no', makeBool)
    True
    >>> getOption(o, 'doit', factory=makeBool)
    True
    >>> getOption(o, 'gipsnich', factory=makeBool)
    >>> getOption(o, 'gipsnich', factory=makeBool, default='false')
    False
    >>> getOption(o, 'max-recursions', factory=NoneOrInt)
    >>> getOption(o, 'max-recursions', '10', factory=NoneOrInt)
    10
    >>> getOption(o, 'path', choices=('eins', 'zwei'))
    'eins'
    >>> getOption(o, 'path', choices=('zwei', 'drei')) # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValueError: 'eins': only one of ('zwei', 'drei') allowed!
    >>> getOption(o, 'path', default='eins', choices=('zwei', 'drei'))
    'eins'
    >>> o['empty'] = ' '
    >>> getOption(o, 'empty', '', choices=('eins', 'zwei'))
    """
    if key not in odict:
        if use_default >= 1:
            if factory is None:
                return default
            if default is None:
                return default
            return factory(default)
        else:
            raise KeyError(key)
    val = odict[key]
    if factory is not None and isinstance(val, six_string_types):
        val = factory(val)
    if choices:
        try:
            if default is None and use_default >= 1:
                default = choices[0]
        except TypeError:  # z. B. choices ist ein Set:
            pass
    if val is None and use_default >= 2:
        if factory is None:
            val = default
        else:
            val = factory(default)
    if choices:
        if val in choices:
            return val
        if default is not None:
            # also angegeben; nach Anwendung einer factory-Funktion ist auch
            # None möglich:
            if factory is None:
                if val == default:
                    return val
            else:
                if val == factory(default):
                    return val
        raise ValueError("%(val)r: only one of %(choices)s allowed!"
                         % locals())
    return val
# --------------------------- ] ... aus Products.unitracc.tools.misc ]


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
