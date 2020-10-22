# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Tools for sequences
"""
# Python compatibility:
from __future__ import absolute_import

from six import string_types as six_string_types
from six.moves import map, range

# Standard library:
from string import strip

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (0,
           4,  # make_safe_decoder, nun --> .coding
           10, # make_names_tupelizer, make_dict_sequencer
           )
__version__ = '.'.join(map(str, VERSION))


__all__ = [
           'inject_indexes',
           'sequence_slide',   # (prev, current, next)-Tupel
           'matrixify',
           'next_of',
           'nonempty_lines',
           # aus Products.unitracc.tools.misc:
           'unique_union',
           'make_names_tupelizer',
           'make_dict_sequencer',
           'columns',
           ]


def inject_indexes(seq, missing=None):
    """
    Iteriere über eine Sequenz und generiere 4-Tupel:
    - das Listenelement
    - voriger Index (für das erste Element: None)
    - aktuellen Index (für das erste Element: 0)
    - nächster Index (für das letzte Element: None)

    >>> list(inject_indexes('ABC'))
    [('A', None, 0, 1), ('B', 0, 1, 2), ('C', 1, 2, None)]

    >>> list(inject_indexes(''))
    []
    """
    first = True
    prev_item = None
    prev_idx = missing
    idx = 0
    for item in seq:
        if first:
            prev_idx = missing
            prev_item = item
            first = False
            continue
        yield (prev_item, prev_idx, idx, idx+1)
        prev_item = item
        prev_idx = idx
        idx += 1

    if not first:
        yield (prev_item, prev_idx, idx, missing)


def sequence_slide(seq, missing=None):
    """
    Iteriere über eine Sequenz und generiere (prev, current, next)-Tupel

    >>> list(sequence_slide('ab'))
    [(None, 'a', 'b'), ('a', 'b', None)]
    >>> list(sequence_slide('abc'))
    [(None, 'a', 'b'), ('a', 'b', 'c'), ('b', 'c', None)]
    >>> list(sequence_slide('a'))
    [(None, 'a', None)]
    >>> list(sequence_slide('abcd'))
    [(None, 'a', 'b'), ('a', 'b', 'c'), ('b', 'c', 'd'), ('c', 'd', None)]

    Eine leere Sequenz ergibt eine leere Sequenz von Tupeln:
    >>> list(sequence_slide(''))
    []
    """
    buf = [missing]
    bufsize = 0
    after_head = False
    for item in seq:
        if after_head:
            yield tuple(buf)
            del buf[0]
        else:
            bufsize += 1
            if bufsize >= 2:
                after_head = True
        buf.append(item)

    buf.append(missing)
    for i in range(bufsize):
        yield tuple(buf[i:i+3])


def matrixify(seq, chunksize):
    """
    Gib für eine "flache" Sequenz eine Liste von Listen zurück
    (wie der Tomcom-Adapter "maxlist"):

    >>> list(matrixify(map(int, list('1234567')), 3))
    [[1, 2, 3], [4, 5, 6], [7]]
    """
    i = 0
    liz = []
    for item in seq:
        liz.append(item)
        i += 1
        if i >= chunksize:
            yield liz
            liz, i = [], 0
    if i:
        yield liz


def next_of(top, current, step=1):
    """
    Zur Auswahl des nächsten Indexes einer Liste,
    z. B. bei Ausgabe von Werbung:

    >>> liz = list('abcde')
    >>> top = len(liz)
    >>> next_of(top, 0)
    1
    >>> next_of(top, 3)
    4
    >>> next_of(top, 4)
    0
    >>> next_of(top, 4, step=2)
    1
    """
    val = current + step
    if val >= top:
        return val % top
    return val


def nonempty_lines(s, func=strip):
    r"""
    Gib alle nicht-leeren Zeilen einer Zeichenkette zurück:

    >>> s = '\neins  \r\n zwei drei \n \n'
    >>> list(nonempty_lines(s))
    ['eins', 'zwei drei']
    """
    for item in s.splitlines():
        short = func(item)
        if short:
            yield short


def unique_union(*seqs):
    """
    Gib eine Vereinigungsmenge der übergebenen Sequenzen als Liste zurück,
    wobei die jeweilige Reihenfolge erhalten bleibt.
    Doppelte Elemente werden hingegen nur bei ihrem ersten Auftreten
    berücksichtigt.

    >>> unique_union(list('ottosmops'), list('hopstfort'))
    ['o', 't', 's', 'm', 'p', 'h', 'f', 'r']
    """
    done = set()
    res = []
    for seq in seqs:
        for item in seq:
            if item in done:
                continue
            done.add(item)
            res.append(item)
    return res


def nocomments_split(s):
    r"""
    Split a multiline string, skipping comments.

    >>> f = nocomments_split
    >>> f('''one.two three
    ... # ignored comment line
    ... four # ignored trailing comment
    ...    # another comment line
    ... five
    ... ''')
    ['one.two', 'three', 'four', 'five']
    >>> f('  \t')
    []
    >>> f('  # ignored')
    []
    >>> f('one\r\n  # ignored \rtwo \n  # another comment\n three')
    ['one', 'two', 'three']

    >>> '   '.split()
    []
    """
    res = []
    for line in s.splitlines():
        if '#' in line:
            line, comment = line.split('#', 1)
        for word in line.split():
            res.append(word)
    return res


# --------------------------- [ aus Products.unitracc.tools.misc ... [
def make_names_tupelizer(forbidden,
                         onerror='error',
                         logger=None):
    """
    Erzeuge eine Funktion, die aus einer Sequenz von Feldnamen ein sortiertes
    Tupel erzeugt

    >>> forbidden='href getURL getPath'.split()
    >>> class Logger:
    ...     def error(self, *args, **kwargs):
    ...         pass
    >>> logger = Logger()
    >>> nice = make_names_tupelizer(forbidden, onerror='remove', logger=logger)
    >>> nice(['href', 'Title'])
    ('Title',)
    >>> strict = make_names_tupelizer(forbidden, onerror='error', logger=logger)
    >>> strict(['href', 'Title'])
    Traceback (most recent call last):
      ...
    ValueError: Forbidden names found! (set(['href'])

    """
    forbidden = set(forbidden)

    def strict(liz):
        if isinstance(liz, six_string_types):
            raise TypeError('non-string sequence expected; got: %(liz)r'
                            % locals())
        unique = set(liz)
        invalid = unique.intersection(forbidden)
        if invalid:
            raise ValueError('Forbidden names found! (%(invalid)r'
                             % locals())
        return tuple(sorted(unique))

    def forgiving(liz):
        if isinstance(liz, six_string_types):
            raise TypeError('non-string sequence expected; got: %(liz)r'
                            % locals())
        unique = set(liz)
        invalid = unique.intersection(forbidden)
        if invalid:
            logger.error('make_names_tupelizer: removing invalid names'
                         ' %(invalid)s', locals())
            unique.difference_update(invalid)
        return tuple(sorted(unique))

    if onerror == 'error':
        return strict
    elif onerror == 'remove':
        if logger is None:
            raise ValueError('onerror=%(onerror)r: logger needed'
                             % locals())
        return forgiving
    else:
        raise ValueError('onerror=%(onerror)r (error or remove expected)'
                         % locals())


def make_dict_sequencer(firstkey=None,
                        key='key', val_key='val',
                        selected_key='selected',
                        convert_nondict=None,
                        **kwargs):
    """
    Erzeuge eine Funktion, die ein Dict in eine Sequenz von Dicts umwandelt
    (z. B., um ein Formular zu generieren).

    >>> raw1 = {'default': 'Vorgabe', 'other': 'Abweichung'}
    >>> raw1copy = dict(raw1)
    >>> convert = make_dict_sequencer('default')
    >>> list(convert(raw1))
    [{'key': 'default', 'val': 'Vorgabe'}, {'key': 'other', 'val': 'Abweichung'}]

    Durch die Verarbeitung wird (wenn firstkey nicht None ist) das Eingabe-Dict
    geändert:

    >>> raw1 != raw1copy
    True

    Wenn das Dict schon Dicts enthält, erfolgt eine Konsistenzprüfung:

    >>> def si(dic):
    ...     return sorted(dic.items())
    >>> gen1 = convert({'default': {'key': 'default', 'val': 'Vorgabe 2'},
    ...                 'other': {'val': 'Abweichung 2'}})
    >>> list([si(dic) for dic in gen1])
    [[('key', 'default'), ('val', 'Vorgabe 2')], [('key', 'other'), ('val', 'Abweichung 2')]]
    >>> gen2 = convert({'default': {'key': 'FEHLER', 'val': 'Vorgabe 2'},
    ...                 'other': {'val': 'Abweichung 2'}})

    Zunächst wird nur der Generator erzeugt; beim Iterieren fällt der Fehler
    dann auf:
    >>> list([si(dic) for dic in gen2])
    Traceback (most recent call last):
      ...
    ValueError: item={'val': 'Vorgabe 2', 'key': 'FEHLER'}, item['key']='FEHLER', thiskey='default'

    >>> gen3 = convert({'default': {'key': 'default', 'val': 'Vorgabe 2'},
    ...                 'other': {'val': 'Abweichung 2'}}, curval='other')
    >>> list([si(dic) for dic in gen3])
    [[('key', 'default'), ('selected', False), ('val', 'Vorgabe 2')], [('key', 'other'), ('selected', True), ('val', 'Abweichung 2')]]
    """
    if convert_nondict is None:
        def convert_nondict(val):
            return {val_key: val}

    def checked_item_1(item, thiskey, k, vk):
        if not isinstance(item, dict):
            item = convert_nondict(item)
        # der Schlüssel k ist in item schon vorhanden
        if k in item:
            if item[k] != thiskey:
                raise ValueError('item=%r, item[%r]=%r, thiskey=%r'
                                 % (item, k, item[k], thiskey,
                                    ))
        item[k] = thiskey
        return item

    def checked_item_2(item, thiskey, k, vk, curval):
        if not isinstance(item, dict):
            item = convert_nondict(item)
        # der Schlüssel k ist in item schon vorhanden
        if k in item:
            if item[k] != thiskey:
                raise ValueError('item=%r, item[%r]=%r, thiskey=%r'
                                 % (item, k, item[k], thiskey,
                                    ))
        item[k] = thiskey
        item[selected_key] = thiskey == curval
        return item

    def dict_to_dicts_sequence(dic, curval=None):
        args = [key, val_key]
        if curval is None:
            checked_item = checked_item_1
        else:
            checked_item = checked_item_2
            args.append(curval)
        if firstkey is not None:
            item = dic.pop(firstkey)
            yield checked_item(item, firstkey, *args)

        for k in sorted(dic.keys()):
            item = dic[k]
            if not isinstance(item, dict):
                item = convert_nondict(item)
            yield checked_item(item, k, *args)

    return dict_to_dicts_sequence


def columns(seq, *args):
    """
    Gib soviele "Spalten" (i.e. Listen) von Elementen zurück
    wie weitere Argumente (nach der Sequenz) übergeben wurden, in der Regel: 2.
    Jedes Argument muß eine ganze Zahl sein;
    nur das letzte darf 0 sein.

    >>> columns(map(int, list('1234567')), 2, 3)
    ([1, 2], [3, 4, 5])
    >>> columns(map(int, list('1234567')), 2, 0)
    ([1, 2], [])
    >>> columns(map(int, list('1')), 2, 3)
    ([1], [])
    """
    assert args, 'columns(%r, *args): ganze Zahlen erwartet' % (seq, )
    res = []
    argl = list(args)
    i = 0
    for item in seq:
        if i == 0:
            if not argl:
                break
            lastlist = []
            res.append(lastlist)
            thismax = argl.pop(0)
            assert isinstance(thismax, int), \
                    '%r: ganze Zahl erwartet' % (thismax, )
            if thismax == 0:
                assert not argl, \
                        ('columns(%r, %s): 0 nur als letztes Argument erlaubt!'
                         ' (%s)'
                         % (seq, ', '.join(map(str, args)), argl))
                continue
        lastlist.append(item)
        i += 1
        if i >= thismax:
            if argl:
                i = 0
            else:
                break
    for i in range(len(res), len(args)):
        res.append([])
    return tuple(res)
# --------------------------- ] ... aus Products.unitracc.tools.misc ]


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
