# -*- coding: utf-8 -*-  äöü vim: sw=4 sts=4 si et tw=79 cc=+1
"""
Support for batches: split sequences into batches of a given equal (maximum)
size
"""

# Python compatibility:
from __future__ import absolute_import

__all__ = [
    'batch_tuples',  # generate (sublist, txt) tuples
    ]

def batch_tuples(seq, batch_size, **kwargs):
    """
    Generate batches of a given `batch_size`, and descriptive strings

    >>> seq = (int(ch)*10 for ch in list('123456789'))
    >>> len(seq)
    Traceback (most recent call last):
    ...
    TypeError: object of type 'generator' has no len()
    >>> gen = batch_tuples(seq, 3)
    >>> gen  # doctest: +ELLIPSIS
    <generator object batch_tuples at 0x...>
    >>> next(gen)
    ([10, 20, 30], 'items 1 to 3 (batch 1)')
    >>> next(gen)
    ([40, 50, 60], 'items 4 to 6 (batch 2)')
    >>> next(gen)
    ([70, 80, 90], 'items 7 to 9 (batch 3)')

    If the sequence has a known length (i.e., it is not a generator),
    the number of batches is known as well, so it is included in the yielded
    strings:

    >>> seq = list(int(ch)*11 for ch in list('123456789'))
    >>> list(batch_tuples(seq, 3))
    [([11, 22, 33], 'items 1 to 3 (batch 1 of 3)'), ([44, 55, 66], 'items 4 to 6 (batch 2 of 3)'), ([77, 88, 99], 'items 7 to 9 (batch 3 of 3)')]

    ... unless you don't want it to (because the length detection might be an
    expensive operation):
    >>> list(batch_tuples(seq, 3, get_length=False))
    [([11, 22, 33], 'items 1 to 3 (batch 1)'), ([44, 55, 66], 'items 4 to 6 (batch 2)'), ([77, 88, 99], 'items 7 to 9 (batch 3)')]

    Of course the last batch is shorter in most cases:
    >>> list(batch_tuples(seq, 5))
    [([11, 22, 33, 44, 55], 'items 1 to 5 (batch 1 of 2)'), ([66, 77, 88, 99], 'items 6 to 9 (batch 2 of 2)')]

    ... but sometimes it will just fit:
    >>> list(batch_tuples(seq[:-1], 4))
    [([11, 22, 33, 44], 'items 1 to 4 (batch 1 of 2)'), ([55, 66, 77, 88], 'items 5 to 8 (batch 2 of 2)')]

    You may customize the generated strings.
    Here is a summary of all keyword-only options, with defaults:

    thingies -- text snippet for the items; default: 'items' (see above)
    mask_knownlength -- text mask for sequences iwth known length, containing
                    "number of batches" information; get_length=True)
    mask_openend -- text mask for "open ended" sequences (without "number of
                    batches" information; get_length=False)
    get_length -- detect and use the length of the sequence? Default is True,
                  for non-generator sequences.

    The masks use "%" syntax; you must double the "%" for the variables which
    change for every tuple. The keys are:

    - first -- the 1-based number of the first item in a batch
    - last -- the 1-based number of the last item in a batch
    - batch -- the 1-based number of the batch
    - thingies -- "items", or the thingies option

    and, for mask_knownlength only:

    - total -- the total number of items
    - batches -- the total number of generated batch tuples

    The first, last and batch variables vary during the loop and thus can't be
    expanded beforehand; thus, you'll get a KeyError if you specify a single `%`
    only (as soon as you start using the generator):

    >>> gen = batch_tuples(seq, 5, mask_openend='processing objects %(first)d'
    ...                    ' to %%(last)d (batch %%(batch)d)', get_length=0)
    >>> next(gen)
    Traceback (most recent call last):
    ...
    KeyError: 'first'

    You might use the mask_... options e.g. to generate translated strings.
    """
    pop = kwargs.pop
    get_length = pop('get_length', True)
    thingies = pop('thingies', None) or 'items'

    try:
        if get_length:
            total = len(seq)
        else:
            total = None
    except TypeError:
        total = None
    if total is None:
        mask_mask = pop('mask_openend',
                        '%(thingies)s %%(first)d to %%(last)d (batch %%(batch)d)')
    else:
        batches, rest = divmod(total, batch_size)
        if rest:
            batches += 1
        mask_mask = pop('mask_knownlength',
                        '%(thingies)s %%(first)d to %%(last)d (batch %%(batch)d of %(batches)d)')
    mask = mask_mask % locals()

    liz = []
    i = 0
    first = 1
    batch = 1
    for thingy in seq:
        i += 1
        liz.append(thingy)
        if not i % batch_size:
            last = i
            yield (liz, mask % locals())
            first = i + 1
            batch += 1
            liz = []
    if liz:
        last = i
        yield (liz, mask % locals())
    return


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
