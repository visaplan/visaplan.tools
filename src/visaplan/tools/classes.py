# -*- coding: utf-8 -*-
"""
unitracc.tools.classes - kleine nützliche Hilfsklassen

Autor: Tobias Herp
"""
from posixpath import normpath as normpath_posix


__all__ = [# dict-Klassen: Standardwert ...
           'Mirror',      # ... der Schlüssel (key)
           'Counter',     # ... 0
           'WriteProtected',
           'ChangeProtected',
           'RecursiveMap',
           'make_frozen_shadow',  # FrozenShadow-Klasse
           'DictOfSets',  # z. B. für Workflow
           'RootsDict',   # ... speziell für Pfade
           'Once',
           # (nun eine Factory:)
           'Proxy',       # ... Ergebnis von Funktion(key)
           # (Kandidaten für Konversion zu Factory-Aufrufen:) 
           'SetterDict',  # ... setKey
           'CheckedSetterDict',
           'GetterDict',  # ... getKey
           #  dto., ... mit Factory für Hilfsfunktion: 
           'PrefixingMap', 'make_width_getter',
           # list-Klassen:
           'UniqueStack',
           ]
# siehe auch .misc.key_injector


class Mirror(dict):
    """
    Gib für jeden Schlüssel seinen eigenen Wert zurück -
    außer, wenn ein anderer Wert explizit zugewiesen wurde.

    >>> mirror = Mirror()
    >>> mirror['eins'] = 'zwei'
    >>> mirror['null']
    'null'
    >>> mirror['eins']
    'zwei'

    Es bestehen dieselben Initialisierungsmöglichkeiten wie bei einem
    normalen dict-Objekt:

    >>> mirror = Mirror({'flip': 'flop'})
    >>> mirror['flip']
    'flop'
    >>> mirror['flap']
    'flap'
    """

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            dict.__setitem__(self, key, key)
            return dict.__getitem__(self, key)


class SetterDict(dict):
    """
    Halte für Attribute die Namen der Setter-Methoden vor

    >>> setter = SetterDict()
    >>> setter['date']
    'setDate'
    """

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            val = 'set%s%s' % (key[0].upper(), key[1:])
            dict.__setitem__(self, key, val)
            return dict.__getitem__(self, key)


class CheckedSetterDict(SetterDict):
    """
    Wie --> SetterDict:
    Halte für Attribute die Namen der Setter-Methoden vor ...

    >>> setter = CheckedSetterDict()
    >>> setter['date']
    'setDate'

    ... aber behandle bestimmte Werte speziell:

    >>> setter['title']
    >>> setter['id']
    Traceback (most recent call last):
    ...
    ValueError: 'id' must not be set directly!
    """

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if key == 'id':
                raise ValueError('%(key)r must not be set directly!' % locals())
            elif key == 'title':
                # kein Setter, sondern direkte Zuweisung mit setattr: 
                val = None
            elif not key:
                raise ValueError('Invalid key %(key)r!' % locals())
            else:
                val = 'set%s%s' % (key[0].upper(), key[1:])
            dict.__setitem__(self, key, val)
            return dict.__getitem__(self, key)


class GetterDict(dict):
    """
    Halte für Attribute die Namen der Getter-Methoden vor

    >>> getter = GetterDict()

    Als Getter ist das möglich:
    >>> getter['id']
    'getId'

    Bekannter Sonderfall wg. Dublin Core:
    >>> getter['date']
    'Date'
    """

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            val = 'get%s%s' % (key[0].upper(), key[1:])
            dict.__setitem__(self, key, val)
            return dict.__getitem__(self, key)

    def __init__(self, seed=None):
        """
        Initialisiere das GetterDict mit den bekannten Sonderfällen
        """
        dict.__init__(self)
        if seed is None:
            seed = {key: key.capitalize()
                    for key in 'title date description language creator'.split()
                    }
        if seed:
            dict.update(self, seed)


def Proxy(func, *args, **kwargs):
    """
    Factory, die einen Proxy für die Funktion <func> erzeugt,
    der also die Ergebnisse ihrer Funktionsaufrufe zwischenspeichert.

    >>> func = lambda a: a*3
    >>> proxy = Proxy(func)
    >>> proxy[2]
    6

    Optionale Argumente, stets benannt zu übergeben:
    aggressive - wenn True, wird mit Exceptions gearbeitet;
                 sinnvoll, wenn die Wahrscheinlichkeit für "Cache-Hits" sehr groß ist,
                 oder notfalls, wenn None ein sinnvoller Wert ist
                 (Auswirkung auf das Laufzeitverhalten, aber nicht auf das Ergebnis)

    normalize - eine Funktion zur Normalisierung des Schlüssels:

    >>> def n(liz):
    ...     return tuple(sorted(set(liz)))
    >>> p = Proxy(list, normalize=n)
    >>> p['einszwei']
    ['e', 'i', 'n', 's', 'w', 'z']
    >>> p['zweieins']
    ['e', 'i', 'n', 's', 'w', 'z']
    >>> len(p)
    1
    >>> p.keys()
    [('e', 'i', 'n', 's', 'w', 'z')]
    """
    aggressive = kwargs.pop('aggressive', False)
    normalize = kwargs.pop('normalize', None)
    if kwargs:
        raise TypeError('Unknown arguments! (%(kwargs)r)' % locals())

    getitem = dict.__getitem__
    setitem = dict.__setitem__

    class PoliteProxy(dict):
        def __getitem__(self, key):
            if key in self:
                val = getitem(self, key)
            else:
                val = func(key)
                setitem(self, key, val)
            return val

    class AggressiveProxy(dict):
        def __getitem__(self, key):
            try:
                return getitem(self, key)
            except KeyError:
                val = func(key)
                setitem(self, key, val)
                return val

    if aggressive:
        proxycls = AggressiveProxy
    else:
        proxycls = PoliteProxy

    if normalize is not None:
        class NormalizingProxy(proxycls):
            def __getitem__(self, key):
                key = normalize(key)
                return proxycls.__getitem__(self, key)

            def __setitem(self, key, val):
                key = normalize(key)
                return dict.__setitem__(self, key, val)
        return NormalizingProxy(*args)

    return proxycls(*args)


class DictOfSets(dict):
    """
    Ein Dict, das benannte Sets enthält,
    z.B. für die Erledigung von Workflow-Statusänderungen

    >>> done = DictOfSets(keys=['published', 'visible'])
    >>> len(done)
    0
    >>> not done
    True

    >>> done.add('abc123', 'published')
    >>> done['published']
    set(['abc123'])
    >>> not done
    False
    >>> len(done)
    1

    Neue Schlüssel werden bei Bedarf erzeugt:
    >>> done.add('cde456', 'restricted')
    >>> done['restricted']
    set(['cde456'])

    Die "Länge" des Objekts entspricht der Summe der Längen der
    benannten Sets, wobei Mehrfachvorkommen von Elementen nicht
    untersucht werden.
    Die drei enthaltenen Sets umfassen nun insgesamt 2 Elemente:
    >>> len(done)
    2

    Die Reihenfolge der Schlüssel ist signifikant und wird erhalten:
    >>> done.ordered_keys()
    ['published', 'visible', 'restricted']

    Sets können auch leer hinzugefügt werden,
    um eine bestimmte Rangfolge zu bewirken:
    >>> done.add_set('inherit')
    >>> done.ordered_keys()
    ['published', 'visible', 'restricted', 'inherit']

    In einem üblichen Szenario ist es möglich, daß derselbe Eintrag
    einem weiteren Set hinzugefügt wird:
    >>> done.add('abc123', 'visible')
    >>> 'abc123' in done['visible']
    True

    Da jedoch der Schlüssel 'published' im Beispiel vor 'visible' kommt,
    wird bei der entsprechenden Abfrage 'published' zurückgegeben:
    >>> done.first_hit('abc123')
    'published'

    Wenn nur Treffer bis zum Schlüssel 'visible' interessieren,
    kann dieser zusätzlich übergeben werden:
    >>> done.first_hit('abc123', 'visible')
    'published'
    >>> done.first_hit('cde456', 'visible')
    >>> done.first_hit('cde456')
    'restricted'
    """

    def __init__(self, keys=None, **kwargs):
        self._ordered_keys = []
        if keys is not None:
            for key in keys:
                self.add_set(key)
        for key, val in kwargs:
            self.add_set(key)
            self[key] = set(val)

    def _add_set(self, key):
        key = self._check_key(key)
        tmp = self[key] = set()
        thelist = self._ordered_keys
        if key not in thelist:
            thelist.append(key)
        return tmp

    def _check_key(self, key):
        """
        einfache Validierung und ggf. Normalisierung
        """
        if key is None:
            raise ValueError('Disallowed key %(key)r!' % locals())
        return key

    def add_set(self, key):
        key = self._check_key(key)
        tmp = None
        try:
            tmp = self[key]
        except KeyError:
            tmp = self[key] = set()
        else:
            if not isinstance(tmp, set):
                raise ValueError('None-set %(tmp)r found as %(key)r!'
                                 % locals())
        finally:
            thelist = self._ordered_keys
            if key not in thelist:
                thelist.append(key)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self._add_set(key)
        
    def add(self, item, key):
        self[key].add(item)

    def ordered_keys(self):
        return list(self._ordered_keys)

    def first_hit(self, item, last_key=None):
        for key in self.ordered_keys():
            if item in self[key]:
                return key
            if key == last_key:
                break

    def __len__(self):
        """
        Die kumulierte Länge der enthaltenen benannten Sets
        """
        res = 0
        for val in self.values():
            res += len(val)
        return res


class RootsDict(DictOfSets):
    """
    Zur Verwaltung geerbter Eigenschaften, wie etwa Workflow-Status

    >>> rd = RootsDict()
    >>> rd.add('/pfad/ohne/slash', 'published')

    Die Einträge werden normalisiert;
    >>> rd['published']
    set([('', 'pfad', 'ohne', 'slash')])
    >>> f = rd._check_item
    >>> fmt = lambda x: '/'.join(x)
    >>> sorted(map(f, '/pfad1/ /pfad2 /pfad1/unterverz'.split()))
    [('', 'pfad1'), ('', 'pfad1', 'unterverz'), ('', 'pfad2')]
    >>> map(fmt, sorted(map(f, '/pfad1/ /pfad2 /pfad1/unterverz'.split())))
    ['/pfad1', '/pfad1/unterverz', '/pfad2']

    >>> rd.add('/pfad/ganz/woanders', 'visible')
    >>> rd.first_hit('/pfad/ohne/slash/mit/unterseite')
    'published'

    Wie bei DictOfSets kann auch hier eine Rangfolge initial erzeugt werden:
    >>> rd = RootsDict(['published', 'visible', 'restricted'])
    >>> rd.add('/pfad/ohne/slash', 'restricted')
    >>> rd.add('/pfad/ohne/slash', 'published')
    >>> rd._cached_data()
    ([('/pfad/ohne/slash', 100, 'published'), ('/pfad/ohne/slash', 98, 'restricted')], {'visible': 99, 'restricted': 98, 'published': 100}, {98: 'restricted', 99: 'visible', 100: 'published'})
    >>> rd.first_hit('/pfad/ohne/slash/mit/unterseite')
    'published'

    Unbekannte Pfade zeitigen den Vorgabewert None:
    >>> rd.first_hit('/voellig/unbekannter/pfad/')

    ... es sei denn, use_default ist abgeschaltet:
    >>> rd.configure(use_default=False)
    >>> rd.first_hit('/voellig/unbekannter/pfad/')
    Traceback (most recent call last):
    ...
    KeyError: "No match for '/voellig/unbekannter/pfad'!"

    Wenn beim Aufruf ein Vorgabewert übergeben wird, wird dieser natürlich verwendet:
    >>> rd.first_hit('/voellig/unbekannter/pfad/', default=None)
    >>> rd.first_hit('/voellig/unbekannter/pfad/', default='gipsnich')
    'gipsnich'
    """

    def __init__(self, *args, **kwargs):
        self._settings = {}
        if 'default' in kwargs:
            default = kwargs.pop('default')
        else:
            default = None
        use_default = kwargs.pop('use_default', True)
        settings = {'default': default,
                    'use_default': use_default,
                    }
        self.configure(**settings)
        DictOfSets.__init__(self, *args, **kwargs)
        self._dirty = True  # bislang nicht "thread-safe"!

    def configure(self, **kwargs):
        self._settings.update(kwargs)

    def _check_item(self, item):
        return tuple(normpath_posix(item).split('/'))

    def add(self, item, key):
        key = self._check_key(key)
        item = self._check_item(item)
        self[key].add(item)
        self._dirty = True

    def _cached_data(self):
        if self._dirty:
            united = []
            key2num = {}
            num2key = {}
            i = 0
            for key in self.ordered_keys():
                thisnum = key2num[key] = 100-i
                num2key[thisnum] = key
                for item in sorted(self[key]):
                    united.append(('/'.join(item), thisnum, key))
                i += 1  # rückwärts suchen!
            united.sort()
            self._united = list(reversed(united))
            self._key2num = key2num
            self._num2key = num2key
            self._dirty = False
        return self._united, self._key2num, self._num2key
        
    def first_hit(self, item, last_key=None, **kwargs):
        item = '/'.join(self._check_item(item))
        united, key2num, num2key = self._cached_data()
        match = item.startswith
        if last_key is None:
            for tup in united:
                storeditem, num = tup[:2]
                if match(storeditem):
                    return num2key[num]
        else:
            quorum = key2num[last_key]
            for tup in united:
                storeditem, num = tup[:2]
                if match(storeditem) and num >= quorum:
                    return num2key[num]
        # kein Treffer; Vorgabe verwenden? 
        if 'default' in kwargs:
            default = kwargs.pop('default')
            use_default = kwargs.pop('use_default', True)
        else:
            use_default = kwargs.pop('use_default',
                                     self._settings['use_default'])
            default = self._settings['default']
        if use_default:
            return default
        raise KeyError('No match for %(item)r!' % locals())


def make_proxy(func, normalize=None):
    """
    *Veraltet* - bitte direkt die allgemeinere Factory --> Proxy verwenden!

    Erzeugt ein "Proxy-Objekt" (Achtung: existiert so nicht mehr als Klasse!)
    und gibt es zurück.
    Optionen:

    normalize -- zur Normalisierung des Schlüssels

    >>> def n(liz):
    ...     return tuple(sorted(set(liz)))
    >>> p = make_proxy(list, n)
    >>> p['einszwei']
    ['e', 'i', 'n', 's', 'w', 'z']
    >>> p['zweieins']
    ['e', 'i', 'n', 's', 'w', 'z']
    >>> len(p)
    1
    >>> p.keys()
    [('e', 'i', 'n', 's', 'w', 'z')]
    """

    if normalize is None:
        return Proxy(func)

    return Proxy(func, normalize=normalize)


class WriteProtected(dict):
    """
    Ein dict, das nur einmal beschrieben werden kann;
    insbesondere können vorhandene Werte nicht überschrieben werden.

    >>> wp=WriteProtected()
    >>> wp[1]=1
    >>> wp[1]=1
    Traceback (most recent call last):
        ...
    ValueError: Error adding 1 as 1: Can't override existing value 1
    >>> wp[2]=2
    >>> wp.freeze()
    >>> wp[3]=3  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: Can't add 3 as 3: <WriteProtected at ...> is frozen
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._frozen = False

    def __setitem__(self, key, val):
        if self._frozen:
            raise ValueError("Can't add %r as %r: %r is frozen"
                             % (val, key, self))
        if key in self:
            raise ValueError('Error adding %r as %r:'
                             " Can't override existing value %r"
                             % (val, key, self[key]))
        return dict.__setitem__(self, key, val)

    def freeze(self):
        self._frozen = True

    def __repr__(self):
        return '<%s at 0x%x>' % (
                self.__class__.__name__,
                id(self),
                )


class ChangeProtected(WriteProtected):
    """
    Ein dict, dessen Schlüssel (außer mit gleichen Werten)
    nur einmal geschrieben werden können.

    >>> cp=ChangeProtected(eins=1)

    Auch der Typ darf sich nicht ändern:

    >>> cp['eins']=1.0
    Traceback (most recent call last):
        ...
    ValueError: Error adding 1.0 as 'eins': Can't override existing value 1
    >>> cp['eins']=2
    Traceback (most recent call last):
        ...
    ValueError: Error adding 2 as 'eins': Can't override existing value 1

    Wird der Schlüssel explizit gelöscht, kann er neu geschrieben werden:
    >>> del cp['eins']
    >>> cp['eins']=2

    Auch ChangeProtected-Objekte können "eingefroren" werden:

    >>> cp.freeze()
    >>> cp['eins']=2
    >>> cp['drei']=3    # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: Can't add 3 as 'drei': <ChangeProtected at 0x...> is frozen
    >>> cp['eins']=2.0
    Traceback (most recent call last):
        ...
    ValueError: Error adding 2.0 as 'eins': Can't override existing value 2
    """

    def __setitem__(self, key, val):
        if key in self:
            oldval = self[key]
            if val != oldval:
                raise ValueError('Error adding %r as %r:'
                                 " Can't override existing value %r"
                                 % (val, key, oldval))
            elif type(val) != type(oldval):
                raise ValueError('Error adding %r as %r:'
                                 " Can't override existing value %r"
                                 % (val, key, oldval))
        elif self._frozen:
            raise ValueError("Can't add %r as %r: %r is frozen"
                             % (val, key, self))
        return dict.__setitem__(self, key, val)


def make_width_getter(ref, splitter=None):
    """
    >>> ref = {'mini': (240, 240),
    ...        'icon': (32, 32)}
    >>> f = make_width_getter(ref)
    >>> f('anyprefix_mini')
    240
    """
    if splitter is None:
        splitter = lambda s: s.split('_', 1)
    def inner(key):
        prefix, key = splitter(key)
        return ref[key][0]

    return inner


class PrefixingMap(dict):
    """
    >>> ref = {'mini': (240, 240),
    ...        'icon': (32, 32)}
    >>> f = make_width_getter(ref)
    >>> p = PrefixingMap(f)
    >>> p['image_mini']
    240
    >>> dict(p)
    {'image_mini': 240}
    """
    def __init__(self, func, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._func = func

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            val = self._func(key)
            self[key] = val
            return val


class Once(dict):
    """
    Gibt bei jedem ersten Lesezugriff auf einen Schlüssel True zurück, danach False
    (vorbehaltlich abweichender Zuweisungen)

    >>> once = Once()
    >>> once['test']
    True
    >>> once['test']
    False
    >>> once['test']
    False
    """
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            self[key] = False
            return True


class RecursiveMap(dict):
    """
    Ein dict, dessen Werte potentiell wiederum Schlüssel sind.

    >>> map = RecursiveMap(eins='zwei', zwei='drei')
    >>> dict(map)
    {'eins': 'zwei', 'zwei': 'drei'}
    >>> map['eins']
    'drei'
    >>> sorted(map.values())
    ['drei']

    Im Unterschied zum Standard-dict sind mehrfache Werte in der values-Liste
    nicht interessant:

    >>> map['vier'] = 'drei'
    >>> sorted(map.values())
    ['drei']

    Endlosschleifen werden aufgelöst und ggf. None zurückgegeben:

    >>> map['drei'] = 'eins'
    >>> map['eins'] is None
    True

    Direkte Zuweisungen mit einem Wert gleich dem Schlüssel bleiben
    jedoch möglich:

    >>> map.update({'vier': 'vier',
    ...             'drei': 'vier',
    ...             })
    >>> map['drei']
    'vier'
    >>> map['vier']
    'vier'

    Sonstige Funktionalitäten von dict-Objekten sind unverändert:

    >>> map.get('fumf', 5)
    5
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._settings = {'limit': 5,
                          'raise': False,
                          }

    def __getitem__(self, key, limit=None):
        if limit is None:
            limit = abs(self._settings['limit'])
        keys = set()
        first = True
        result = None
        while limit:
            try:
                val = dict.__getitem__(self, key)
            except KeyError:
                return result
            else:
                if val in keys:
                    return None
                elif val == key:
                    return val
                result = val
                keys.add(key)
                key = val
                limit -= 1
        return None

    def values(self):
        """
        Generiere die Werte.

        Werte, die auch als Schlüssel vorkommen, werden ausgefiltert:

        >>> map = RecursiveMap(eins='zwei', zwei='drei')
        >>> sorted(map.values())
        ['drei']
        >>> sorted(dict(map).values())
        ['drei', 'zwei']

        Wenn der Wert gleich dem Schlüssel ist, bleibt er aber erhalten:

        >>> map['vier'] = 'vier'
        >>> sorted(map.values())
        ['drei', 'vier']

        Im Unterschied zum Standard-dict sind mehrfache Werte in der values-Liste
        nicht interessant:

        >>> map['vier'] = 'drei'
        >>> sorted(dict(map).values())
        ['drei', 'drei', 'zwei']
        >>> sorted(map.values())
        ['drei']
        """
        skip = set()
        # sic - wir testen die Werte als Schlüssel ... 
        for key in dict.values(self):
            if key in skip:
                continue
            try:
                val = dict.__getitem__(self, key)
            except KeyError:
                yield key
                skip.add(key)
            else:
                if val == key:
                    yield key
                skip.add(key)


# aus @@groupsharing.utils wieder entfernt, weil die Werte vom shadow-dict
# doch nur einfache Listen waren; vor Verwendung ggf. debuggen ...
def make_frozen_shadow(well):
    """
    Für dict-Objekte, deren Werte Listen sind (üblicherweise Listen von
    Schlüsseln): Erzeuge ein "Schatten-Dict", dessen Werte frozenset-Objekte
    sind.

    >>> dic = {'group_a': ['group_b', 'group_c'],
    ...        'group_b': ['user_a', 'user_b'],
    ...        'group_c': ['user_c'],
    ...        }
    >>> shadow = make_frozen_shadow(dic)
    >>>
    >x> shadow['group_c']
    frozenset(['user_c'])
    """
    class FrozenShadow(dict):
        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                val = frozenset(well[key])
                self.__setitem__(key, val)
                return val

    return FrozenShadow(well)


class UniqueStack(list):
    """
    Ein Stack, der jeden Eintrag nur einmal enthält;
    verhält sich ansonsten wie eine Liste.

    >>> ust = UniqueStack('abc')
    >>> ust
    ['a', 'b', 'c']

    Wenn ein anzuhängender Eintrag schon vorhanden ist,
    wird er an der alten Stelle gelöscht und hinten angehängt:

    >>> ust.append('a')
    >>> ust
    ['b', 'c', 'a']

    >>> ust.append('d')
    >>> ust
    ['b', 'c', 'a', 'd']

    Das UniqueStack-Objekt kann zur Liste konvertiert werden:
    >>> list(ust)
    ['b', 'c', 'a', 'd']

    Die extend-Methode wird in append-Aufrufe aufgeteilt:
    >>> ust.extend(['d', 'e', 'e'])
    >>> ust
    ['b', 'c', 'a', 'd', 'e']

    Das Objekt kann mit Listen direkt verglichen werden:

    >>> thelist = list(ust)
    >>> ust == thelist
    True
    >>> thelist == ust
    True
    >>> ust is thelist
    False
    >>> ust.append('a')
    >>> ust == thelist
    False
    """

    def append(self, val):
        try:
            oldidx = self.index(val)
        except ValueError:
            pass
        else:
            del self[oldidx]
        return list.append(self, val)

    def extend(self, seq):
        if not seq:
            return
        a = self.append
        for item in seq:
            a(item)


# ab Python 2.7: collections.Counter
class _Counter(dict):
    """
    >>> cnt = _Counter()
    >>> cnt['test']
    0
    >>> cnt['test'] += 1
    >>> cnt['test']
    1
    """

    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        else:
            return 0

try:
    from collections import Counter
    # ... oder defaultdict(int) 
except ImportError:
    Counter = _Counter


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# vim: ts=8 sts=4 sw=4 si et
