# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Tools for sequences
"""

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (0,
           4,  # make_safe_decoder, nun --> .coding
           9,  # unique_union
           )
__version__ = '.'.join(map(str, VERSION))


__all__ = [
           'inject_indexes',
           'sequence_slide',   # (prev, current, next)-Tupel
           'matrixify',
           'next_of',
           'nonempty_lines',
           'unique_union',
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


def nonempty_lines(s):
    r"""
    Gib alle nicht-leeren Zeilen einer Zeichenkette zurück:

    >>> s = '\neins  \r\n zwei drei \n \n'
    >>> list(nonempty_lines(s))
    ['eins', 'zwei drei']
    """
    for item in s.splitlines():
        short = item.strip()
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


if __name__ == '__main__':
    import doctest
    doctest.testmod()
