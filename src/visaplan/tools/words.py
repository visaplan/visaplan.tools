# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79 cc=+1
"""
words - split strings into words
"""

# Python compatibility:
from __future__ import absolute_import

import six
from six import string_types as six_string_types
from six import text_type as six_text_type

# Local imports:
from visaplan.tools.sequences import sequence_slide

__all__ = [
    'head',  # return the first fuzzy NN characters
    ]


def _head_kwargs(kw):
    """
    Inspect the keyword arguments for the `head` function.

    Modifies the given dict in-place.

    For our doctest, we'll use a little test helper:
    >>> def _hkw(**dic):
    ...     _head_kwargs(dic)
    ...     return sorted(dic.items())
    >>> _hkw(chars=50)	# doctest: +NORMALIZE_WHITESPACE
    [('chars', 50), ('ellipsis', '...'), ('fuzz', 5), ('strip', True), ('words', None)]
    >>> _hkw(chars=50, fuzz=2)	# doctest: +NORMALIZE_WHITESPACE
    [('chars', 50), ('ellipsis', '...'), ('fuzz', 2), ('strip', True), ('words', None)]
    >>> _hkw(chars=50, fuzz=0)	# doctest: +NORMALIZE_WHITESPACE
    [('chars', 50), ('ellipsis', '...'), ('fuzz', 0), ('strip', True), ('words', None)]
    >>> _hkw(words=10)	# doctest: +NORMALIZE_WHITESPACE
    [('chars', None), ('ellipsis', '...'), ('fuzz', None), ('strip', True), ('words', 10)]
    """
    for key in ('chars', 'words', 'fuzz'):
        num = kw.get(key)
        if num is not None:
            if not isinstance(num, int):
                raise ValueError('%(key)s=%(num)r: integer number expected!'
                                 % locals())
            elif key == 'fuzz':
                if num < 0:
                    raise ValueError('%(key)s=%(num)d: must be >= 0!'
                                     % locals())
            elif num <= 0:
                raise ValueError('%(key)s=%(num)d: must be > 0!'
                                 % locals())
        else:
            kw[key] = None
    chars = kw['chars']
    words = kw['words']
    if chars is None and words is None:
        raise TypeError("Neither 'chars' nor 'words' option given!")

    fuzz = kw['fuzz']
    if fuzz is None:
        if chars is not None and words is None:
            kw['fuzz'] = fuzz = int(chars * 0.1)

    strip = kw.get('strip')
    if strip is None:
        kw['strip'] = True
    elif strip not in (0, 1, True, False):
        raise ValueError('strip=%(strip)r: boolean value (including 0 or 1)'
                         ' expected!' % locals())

    ellipsis = kw.get('ellipsis')
    if ellipsis is None:
        kw['ellipsis'] = '...'
    elif not isinstance(ellipsis, six_string_types):
        raise ValueError('ellipsis=%(ellipsis)r: string expected!' % locals())

    strict = kw.pop('strict', True)
    if strict:
        invalid = set(['chars', 'words', 'fuzz',
                       'ellipsis', 'strip',
                       ]) - set(kw.keys())
        if invalid:
            raise TypeError('Unknown keyword argument(s)! %s'
                            % (tuple(sorted(invalid)),
                               ))


def head(s, **kwargs):
    r"""
    Return the leading part of a string.

    After the string, given positionally as the first argument, we need at
    least one keyword-only option of:

      chars -- the number of characters (approximated)
      words -- less useful, but more easily implemented than `chars`.

    Other options, for the details:

      fuzz -- with `chars` given, we need some tolerance; otherwise, we'd cut
              off the string in the middle of a word in most cases.
      strip -- Strip off leading (and trailing) whitespace first?
               (yes, by default)
      ellipsis -- the part appended to the result, if something (non-space) is
                 cut off at the end; '...' by default.

    >>> s1 = (' Now that Python is installed,  we would  like to be able to '
    ...       'easily run the interactive Python  interpreter from the '
    ...       'Command Prompt.')
    >>> s2 = (' The quick brown fox  jumps over the lazy dog. ')
    >>> s3 = (' The quick brown fox  jumps over the refrigerator. ')
    >>> s4 = ('There was a young lady in Riga\n  '
    ...       'who smiled when she rode on a tiger.\n  '
    ...       'They returned from the ride\n '
    ...       'with the lady inside\n   '
    ...       'and a smile on the face of the tiger.')

    First, the basic Python functionality:
    >>> s1[:50]
    ' Now that Python is installed,  we would  like to '

    ... and, a little bit nearer to what we want:
    >>> ' '.join(s1.split())[:50]
    'Now that Python is installed, we would like to be '
    >>> head(s1, chars=50, fuzz=0)
    'Now that Python is installed, we would like to be ...'

    Such a "hard" characters limit can cut your string off in the middle of a
    word:
    >>> head(s1, chars=20, fuzz=0)
    'Now that Python is i...'

    ... so we don't expect you to need this behaviour very often.
    With a non-zero fuzz value -- the default is 10% of the chars value --
    be prepared to get back strings of different lengths:
    >>> head(s1, chars=50)
    'Now that Python is installed, we would like to ...'
    >>> head(s1, chars=50, fuzz=10)
    'Now that Python is installed, we would like ...'
    >>> head(s2, chars=50, fuzz=10)
    'The quick brown fox jumps over the lazy ...'
    >>> head(s3, chars=50, fuzz=10)
    'The quick brown fox jumps over the refrigerator.'

    If the fuzz doesn't suffice to find word borders, we'll cut in the middle
    of a word, and the "netto" length equals the chars+fuzz value:
    >>> head(s3, chars=40, fuzz=2)
    'The quick brown fox jumps over the refrige...'
    >>> len('The quick brown fox jumps over the refrige')
    42

    With chars=50 and fuzz=10, the resulting string will be between 40 and 60
    characters long, plus the ellipsis:

    >>> len('Now that Python is installed, we would like ')
    44
    >>> len('The quick brown fox jumps over the lazy ')
    40

    If we have a words limit, we include the following non-word part:
    >>> head(s1, words=5)
    'Now that Python is installed, ...'

    Of course we append the ellipsis only when needed:
    >>> head(' There  are only five words.  ', words=5)
    'There are only five words.'

    Another difference to simply splitting and joining is that we preserve
    the first whitespace character in a sequence:

    >>> r4 = head(s4, chars=70)
    >>> r4
    'There was a young lady in Riga\nwho smiled when she rode on a tiger.\n...'
    >>> '\n' in r4
    True

    This is useful if you want to preserve linebreaks.

    Wrong usage:
    >>> head(s1)
    Traceback (most recent call last):
      ...
    TypeError: Neither 'chars' nor 'words' option given!
    >>> head(1, chars=20)
    Traceback (most recent call last):
      ...
    ValueError: string expected; found <type 'int'>!

    """
    kw = dict(kwargs)
    _head_kwargs(kw)
    if isinstance(s, six_text_type):
        joiner = u''
        numseps = set(u'.,')
    elif isinstance(s, str):
        joiner = ''
        numseps = set('.,')
    else:
        raise ValueError('string expected; found %s!' % (type(s),))

    if kw['strip']:
        s = s.strip()
    if not s:
        return s

    join = joiner.join
    tmp = []
    buf = []
    inword = 0
    prev_is_space = 0  # for collapsing

    NONGLOBAL = {
        'words': 0,
        'chars': 0,
        'chars_prev': 0,
        'result': None,
        }
    chars = kw['chars']
    words = kw['words']
    ellipsis = kw['ellipsis']
    if chars is not None:
        fuzz = kw['fuzz']
        minchars = chars - fuzz
        maxchars = chars + fuzz
        hardcut = not fuzz
        NONGLOBAL['done'] = 0
        if hardcut:
            def add():
                # hard chars limit, and optional words limit
                chunklen = len(buf)
                if chunklen and NONGLOBAL['done']:
                    tmp.append(ellipsis)
                    NONGLOBAL['result'] = join(tmp)
                    return 1

                charsleft = maxchars - NONGLOBAL['chars']
                if charsleft < chunklen:
                    chunk = join(buf[:charsleft])
                    tmp.extend([chunk, ellipsis])
                    NONGLOBAL['result'] = join(tmp)
                    return 1
                chunk = join(buf)
                del buf[:]
                tmp.append(chunk)
                if charsleft == chunklen:
                    NONGLOBAL['done'] = 1
                    # We might still need to append the ellipsis:
                    return 0

                NONGLOBAL['chars'] += chunklen

                if inword and words is not None:
                    if NONGLOBAL['words'] >= words:
                        tmp.append(ellipsis)
                        NONGLOBAL['result'] = join(tmp)
                        return 1
                    NONGLOBAL['words'] += 1
                return 0

        else:

            def add():
                # fuzzy chars limit, and optional words limit
                chunklen = len(buf)
                if (NONGLOBAL['done']
                        or NONGLOBAL['chars'] >= minchars and inword):
                    tmp.append(ellipsis)
                    NONGLOBAL['result'] = join(tmp)
                    return 1

                charsleft = maxchars - NONGLOBAL['chars']
                if charsleft < chunklen:
                    if charsleft > 0 and NONGLOBAL['chars'] < minchars:
                        chunk = join(buf[:charsleft])
                        tmp.append(chunk)
                    tmp.append(ellipsis)
                    NONGLOBAL['result'] = join(tmp)
                    return 1
                chunk = join(buf)
                del buf[:]
                tmp.append(chunk)
                if charsleft == chunklen:
                    NONGLOBAL['done'] = 1
                    # We might still need to append the ellipsis:
                    return 0

                NONGLOBAL['chars'] += chunklen

                if inword and words is not None:
                    if NONGLOBAL['words'] >= words:
                        tmp.append(ellipsis)
                        NONGLOBAL['result'] = join(tmp)
                        return 1
                    NONGLOBAL['words'] += 1
                return 0

    else:
        assert words is not None
        assert chars is None
        fuzz = None

        def add():
            # words limit only
            chunk = join(buf)
            del buf[:]
            if inword:
                if NONGLOBAL['words'] >= words:
                    tmp.append(ellipsis)
                    NONGLOBAL['result'] = join(tmp)
                    return 1
                NONGLOBAL['words'] += 1
            tmp.append(chunk)
            return 0

    for prevchar, ch, nextchar in sequence_slide(s):
        if ch.isalnum():  # include numbers here
            if not inword:
                if add():
                    return NONGLOBAL['result']
                inword = 1
            prev_is_space = 0
        elif (ch in numseps
              and prevchar is not None and prevchar.isdigit()
              and (nextchar is not None and nextchar.isdigit()
                   or nextchar is None)):
            # we are in the middle of a number
            assert inword
        else:
            if inword:
                if add():
                    return NONGLOBAL['result']
                inword = 0
            if ch.isspace():
                if prev_is_space:
                    continue
                prev_is_space = 1
            else:
                prev_is_space = 0
        buf.append(ch)
    if buf:
        # tmp.append((inword, join(buf)))
        add()
    return join(tmp)


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
