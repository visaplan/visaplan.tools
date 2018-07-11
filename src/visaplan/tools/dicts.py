# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Tools für Formulare
"""

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"


# Standardmodule
from collections import defaultdict
from string import strip


__all__ = (
           'subdict',
           'subdict_onekey',
           'subdict_forquery',
           # kleine Helferlein:
           'updated',  # ungefähr analog sorted; für dict-Objekte
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
        keys = form.keys()
    else:
        # Alternativer Name für ersten Schlüssel
        primary_fallback = kwargs.pop('primary_fallback', None)
        if primary_fallback is not None:
            assert primary_fallback not in keys, \
                    'Das Alias darf keiner der normalen Schluessel sein'
            aliases[keys[0]] = primary_fallback

    if keyfunc is not None:
        keys = filter(keyfunc, keys)

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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
