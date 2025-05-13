# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79 cc=+1
"""
words - split strings into words
"""

# Python compatibility:
from __future__ import absolute_import, print_function

from six import string_types as six_string_types
from six import text_type as six_text_type

# Local imports:
from visaplan.tools.htmlohmy import entity_aware
from visaplan.tools.sequences import sequence_slide

__all__ = [
    'head',  # return the first fuzzy NN characters (NO HTML input!)
    ]


def _head_kwargs(kw):
    """
    Inspect the keyword arguments for the `head` function.

    Modifies the given dict in-place.

    For our doctest, we'll use a little test helper:
    >>> def _hkw(**dic):
    ...     _head_kwargs(dic)
    ...     return sorted(dic.items())
    >>> _hkw(chars=50)                         # doctest: +NORMALIZE_WHITESPACE
    [('chars', 50),
     ('detect_entities', False),
     ('ellipsis', '...'), ('fuzz', 5),
     ('return_tuple', False),
     ('strip', True), ('words', None)]
    >>> _hkw(chars=50, fuzz=2)                 # doctest: +NORMALIZE_WHITESPACE
    [('chars', 50),
     ('detect_entities', False),
     ('ellipsis', '...'), ('fuzz', 2),
     ('return_tuple', False),
     ('strip', True), ('words', None)]
    >>> _hkw(chars=50, fuzz=0)                 # doctest: +NORMALIZE_WHITESPACE
    [('chars', 50),
     ('detect_entities', False),
     ('ellipsis', '...'), ('fuzz', 0),
     ('return_tuple', False),
     ('strip', True), ('words', None)]
    >>> _hkw(words=10)                         # doctest: +NORMALIZE_WHITESPACE
    [('chars', None),
     ('detect_entities', False),
     ('ellipsis', '...'), ('fuzz', None),
     ('return_tuple', False),
     ('strip', True), ('words', 10)]
    >>> _hkw(words=10, detect_entities=1)      # doctest: +NORMALIZE_WHITESPACE
    [('chars', None),
     ('detect_entities', 1),
     ('ellipsis', '...'), ('fuzz', None),
     ('return_tuple', False),
     ('strip', True), ('words', 10)]

    Since we don't consider it likely you have 200-letter words, even in texts
    with 1000 characters, we have a default limit for the fuzzyness:
    >>> _hkw(chars=1000)                       # doctest: +NORMALIZE_WHITESPACE
    [('chars', 1000),
     ('detect_entities', False),
     ('ellipsis', '...'), ('fuzz', 10),
     ('return_tuple', False),
     ('strip', True), ('words', None)]
    >>> _hkw(chars=1000, max_fuzz=25)          # doctest: +NORMALIZE_WHITESPACE
    [('chars', 1000),
     ('detect_entities', False),
     ('ellipsis', '...'), ('fuzz', 25),
     ('return_tuple', False),
     ('strip', True), ('words', None)]
    >>> _hkw(chars=100, max_fuzz=25)           # doctest: +NORMALIZE_WHITESPACE
    [('chars', 100),
     ('detect_entities', False),
     ('ellipsis', '...'), ('fuzz', 10),
     ('return_tuple', False),
     ('strip', True), ('words', None)]

    Invalid use:
    >>> _hkw(chars=100, max_fuzz='honk')       # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
      ...
    ValueError: max_fuzz='honk': integer number expected!
    >>> _hkw(chars=100, words=20)
    Traceback (most recent call last):
      ...
    TypeError: Currently, we only support either 'chars' or 'words'!
    >>> _hkw(chars=None, words=None)
    Traceback (most recent call last):
      ...
    TypeError: Neither 'chars' nor 'words' option given!
    >>> _hkw(words=5, return_tuple=1)
    Traceback (most recent call last):
      ...
    ValueError: The return_tuple option requires a 'chars' specification!

    There is one argument which won't appear in the returned dict
    but affects the proposed 'ellipsis' value:
    >>> kw={'chars': 20, 'got_bytes': 1}
    >>> _head_kwargs(kw)
    >>> 'ellipsis' in kw
    True
    >>> kw={'chars': 20, 'got_bytes': 0}
    >>> _head_kwargs(kw)
    >>> 'ellipsis' in kw
    True

    """
    got_bytes = kw.pop('got_bytes', 1)
    for key in ('chars', 'words', 'fuzz', 'max_fuzz'):
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
        elif key == 'max_fuzz':
            kw[key] = 10
        else:
            kw[key] = None
    chars = kw['chars']
    words = kw['words']
    max_fuzz = kw.pop('max_fuzz')
    if chars is None:
        if words is None:
            raise TypeError("Neither 'chars' nor 'words' option given!")
    elif words is not None:
        raise TypeError("Currently, we only support either 'chars' or 'words'!")

    fuzz = kw['fuzz']
    if fuzz is None:
        if chars is not None and words is None:
            kw['fuzz'] = fuzz = min(max_fuzz, int(chars * 0.1))

    strip = kw.get('strip')
    if strip is None:
        kw['strip'] = True
    elif strip not in (0, 1, True, False):
        raise ValueError('strip=%(strip)r: boolean value (including 0 or 1)'
                         ' expected!' % locals())

    detect_entities = kw.get('detect_entities')
    if detect_entities is None:
        kw['detect_entities'] = False
    elif detect_entities not in (0, 1, True, False):
        raise ValueError('detect_entities=%(detect_entities)r: '
                         'boolean value (including 0 or 1)'
                         ' expected!' % locals())

    ellipsis = kw.get('ellipsis')
    if ellipsis is None:
        if got_bytes:
            kw['ellipsis'] = '...'
        else:
            kw['ellipsis'] = u'...'
    elif not isinstance(ellipsis, six_string_types):
        raise ValueError('ellipsis=%(ellipsis)r: string expected!' % locals())

    return_tuple = kw.get('return_tuple')
    if return_tuple is None:
        kw['return_tuple'] = False
    elif return_tuple not in (0, 1, True, False):
        raise ValueError('return_tuple=%(return_tuple)r: '
                         'boolean value (including 0 or 1)'
                         ' expected!' % locals())

    if chars is None and return_tuple:
        raise ValueError('The return_tuple option requires'
                " a 'chars' specification!")

    strict = kw.pop('strict', True)
    if strict:
        invalid = (set(kw.keys())
                   - set(['chars', 'words', 'fuzz',
                          'ellipsis', 'strip',
                          'detect_entities',
                          'return_tuple',
                          ]))
        if invalid:
            raise TypeError('Unknown keyword argument(s)! %s'
                            % (tuple(sorted(invalid)),
                               ))


def head(s, **kwargs):
    r"""
    Return the leading part of a string.

    After the string, given positionally as the first argument, we need
    exactly one of the following keyword-only options:

      chars -- the number of characters (approximated)
      words -- less useful, but more easily implemented than `chars`.

    Other options, for the details:

      fuzz -- with `chars` given, we need some tolerance; otherwise, we'd cut
              off the string in the middle of a word in most cases.
      strip -- Strip off leading (and trailing) whitespace first?
               (yes, by default)
      ellipsis -- the part appended to the result, if something (non-space) is
                 cut off at the end; '...' by default.
      detect_entities -- when processing HTML, the parser might produce text
                         with entities, which we don't want to destroy
                         accidently (and count each as one character).
      return_tuple -- currently supported for chars limit only,
                      NOT (yet) for words

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

    The head function gives us a ellipsis here, since something was cut off:
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
    >>> head(s3, chars=40, fuzz=2, return_tuple=1)
    ('The quick brown fox jumps over the refrige...', 45)

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
    >>> head(1, chars=20)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    ValueError: string expected; found <... 'int'>!

    Processing HTML, you'll likely face strings which contain character
    entities, e.g.:
    >>> ex1 = 'D&#195;&#188;sen b&#195;&#188;rsten au&#195;&#159;en und innen'
    >>> head(ex1, chars=20)
    'D&#195;&#188;sen b&#...'

    Oops! With the entities unescaped, our example text would read
    'Düsen bürsten außen und innen', and we'd certainly like to get more than
    'Düsen b' and a broken entity.
    The detect_entities option comes to the rescue:
    >>> head(ex1, chars=20, detect_entities=1)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    'D&#195;&#188;sen b&#195;&#188;rsten au&#195;&#159;en ...'

    That's more like it, right?

    Note that this entity recognition doesn't imply correct HTML prcessing:
    >>> head('<p>Some paragraph with <strong>additional markup</strong>',
    ...      chars=30, fuzz=0)
    '<p>Some paragraph with <strong...'

    It is rather useful for internal use by the .extract.head function
    of our visaplan.kitchen package, which you should use for HTML input.

    Well, the calling code might be interested to know how many characters we
    consider our result to contain.  That's a task for the `return_tuple`
    option:
    >>> head(ex1, chars=20, detect_entities=1, return_tuple=1)
    ('D&#195;&#188;sen b&#195;&#188;rsten au&#195;&#159;en ...', 23)
    >>> len('D?sen b?rsten au?en ...')
    23
    >>> head(ex1, chars=18, detect_entities=1, return_tuple=1, fuzz=0)
    ('D&#195;&#188;sen b&#195;&#188;rsten au&#195;&#159;e...', 21)
    >>> head(ex1, chars=20, detect_entities=1, return_tuple=1)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    ('D&#195;&#188;sen b&#195;&#188;rsten au&#195;&#159;en ...', 23)
    >>> len('D?sen b?rsten au?en ...')
    23
    >>> len('D&#195;&#188;sen b&#195;&#188;rsten au&#195;&#159;en ...')
    56
    """
    kw = dict(kwargs)
    if isinstance(s, bytes):
        kw['got_bytes'] = 1
        joiner = b''
        numseps = set(b'.,')
    elif isinstance(s, six_text_type):
        kw['got_bytes'] = 0
        joiner = u''
        numseps = set(u'.,')
    else:
        raise ValueError('string expected; found %s!' % (type(s),))
    _head_kwargs(kw)

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
    ellipsis_list = list(ellipsis)

    if kw['return_tuple']:
        def RESULT():
            return join(tmp), len(tmp)
    else:
        def RESULT():
            return join(tmp)

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
                if buf and NONGLOBAL['done']:
                    tmp.extend(ellipsis_list)
                    return 1

                charsleft = maxchars - NONGLOBAL['chars']
                if charsleft < chunklen:
                    tmp.extend(buf[:charsleft])
                    tmp.extend(ellipsis_list)
                    return 1
                tmp.extend(buf)
                del buf[:]
                if charsleft == chunklen:
                    NONGLOBAL['done'] = 1
                    # We might still need to append the ellipsis:
                    return 0

                NONGLOBAL['chars'] += chunklen

                if inword and words is not None:
                    if NONGLOBAL['words'] >= words:
                        tmp.extend(ellipsis_list)
                        return 1
                    NONGLOBAL['words'] += 1
                return 0

        else:

            def add():
                # fuzzy chars limit, and optional words limit
                chunklen = len(buf)
                if (NONGLOBAL['done']
                        or NONGLOBAL['chars'] >= minchars and inword):
                    tmp.extend(ellipsis_list)
                    return 1

                charsleft = maxchars - NONGLOBAL['chars']
                if charsleft < chunklen:
                    if charsleft > 0 and NONGLOBAL['chars'] < minchars:
                        tmp.extend(buf[:charsleft])
                    tmp.extend(ellipsis_list)
                    return 1
                tmp.extend(buf)
                del buf[:]
                if charsleft == chunklen:
                    NONGLOBAL['done'] = 1
                    # We might still need to append the ellipsis:
                    return 0

                NONGLOBAL['chars'] += chunklen

                if inword and words is not None:
                    if NONGLOBAL['words'] >= words:
                        tmp.extend(ellipsis_list)
                        return 1
                    NONGLOBAL['words'] += 1
                return 0

    else:  # chars is None
        assert words is not None
        assert chars is None
        fuzz = None

        def add():
            # words limit only
            if inword:
                if NONGLOBAL['words'] >= words:
                    tmp.extend(ellipsis_list)
                    return 1
                NONGLOBAL['words'] += 1
            tmp.extend(buf)
            del buf[:]
            return 0

    if kw['detect_entities']:
        s = entity_aware(s)
    for prevchar, ch, nextchar in sequence_slide(s):
        if ch.isalnum():  # include numbers here
            if not inword:
                if add():
                    return RESULT()
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
                    return RESULT()
                inword = 0
            if ch.isspace():
                if prev_is_space:
                    continue
                prev_is_space = 1
            else:
                prev_is_space = 0
        buf.append(ch)
    if buf:
        add()
    return RESULT()


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
