# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Coding/Decoding tools
"""

# Python compatibility:
from __future__ import absolute_import, print_function

from six import text_type as six_text_type
from six.moves import map

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (0,
           4,  # make_safe_decoder
           1,  # Bugfix (__all__)
           )
__version__ = '.'.join(map(str, VERSION))


__all__ = [
           'safe_decode',
           'make_safe_decoder',
           'make_safe_stringdecoder',  # toleriert Nicht-Strings
           'make_safe_recoder',
           'make_safe_stringrecoder',  # toleriert Nicht-Strings
           'safe_encode',
           'make_safe_encoder',
           'purge_inapt_whitespace',
           'make_whitespace_purger',
           ]


def make_safe_decoder(preferred='utf-8', preflist=None, errors='replace',
                      logger=None, devel=False,
                      refinefunc=None):
    r"""
    Erzeuge eine Funktion safe_decode, die für jeden basestring Unicode
    zurückgibt

    >>> from visaplan.tools.htmlohmy import _prefixed
    >>> def d(f, *args, **kw): return _prefixed(repr(f(*args, **kw)))
    >>> def t(f, *args, **kw):
    ...     res = f(*args, **kw)
    ...     print('is (unicode) str:', isinstance(res, six_text_type))
    ...     print('is bytes:        ', isinstance(res, bytes))
    ...     print(res)
    >>> safe_decode = make_safe_decoder()
    >>> t(safe_decode, 'äöü') # doctest: +NORMALIZE_WHITESPACE
    is (unicode) str: True
    is bytes:         False
    äöü

    Wenn schon Unicode übergeben wird, kommt dieser unverändert zurück:
    >>> t(safe_decode, u'\xe4\xf6\xfc')  # doctest: +NORMALIZE_WHITESPACE
    is (unicode) str: True
    is bytes:         False
    äöü
    >>> _prefixed(u'\xe4\xf6\xfc'.encode('latin1'))
    b'\xe4\xf6\xfc'

    Latin-1-Strings werden standardmäßig als zweite Möglichkeit in Betracht
    gezogen:
    >>> t(safe_decode, '\xe4\xf6\xfc')  # doctest: +NORMALIZE_WHITESPACE
    is (unicode) str: True
    is bytes:         False
    äöü

    Um nur utf-8 in Betracht zu ziehen und Decoding-Fehler nicht zu maskieren
    (aber Unicode unverändert zurückzugeben):

    >>> unicode_or_utf8 = make_safe_decoder(preflist=['utf-8'],
    ...                                     errors='strict')
    >>> t(unicode_or_utf8, '\xe4\xf6\xfc')
    ...                               # doctest: +NORMALIZE_WHITESPACE
    is (unicode) str: True
    is bytes: False
    äöü

    Es kann eine zusätzliche Funktion übergeben werden, um das Ergebnis noch
    weiter zu verarbeiten, z. B. um für lxml unverdaulichen Leerraum zu
    entsorgen:

    >>> lxml_safe = make_safe_decoder(refinefunc=purge_inapt_whitespace)
    >>> val = lxml_safe('Verbau entfernen und Baugrube verfüllen\v')
    >>> _prefixed(val[-1])
    u'n'
    """
    if preflist is None:
        preflist = ['utf-8', 'latin-1']
    if preferred and preferred not in preflist:
        preflist.insert(0, preferred)

    def handle_e(s, encoding, e, logger, devel):
        if devel:  # evtl. bessere Fehlernachricht entwickeln:
            print(str(e))
            mask = '%-10s %r'
            for a in ['args', 'encoding',
                      'start', 'end',
                      'object',
                      'reason',
                      'message']:
                print(mask % (a, getattr(e, a)))
            evil = s[start:end]
            print(mask % (' evil:', evil))
        if logger is not None:
            logger.warn("Assuming %(encoding)r, can't decode %(s)r",
                        locals())

    def safe_decode_inner(s):
        """
        Nimm einen beliebigen Basestring und gib ihn als Unicode zurück
        """
        if isinstance(s, six_text_type):
            return s
        for encoding in preflist:
            try:
                return s.decode(encoding, 'strict')
            except UnicodeDecodeError as e:
                handle_e(s, encoding, e, logger, devel)
        if errors != 'strict' and preferred:
            return s.decode(preferred, errors)
        raise

    def safe_decode_refined(s):
        """
        Nimm einen beliebigen Basestring und gib ihn als Unicode zurück.
        Abschließend wird die der Factory übergebene Refine-Funktion
        ausgeführt
        """
        try:
            res = None
            if isinstance(s, six_text_type):
                res = s
            else:
                for encoding in preflist:
                    try:
                        res = s.decode(encoding, 'strict')
                    except UnicodeDecodeError as e:
                        handle_e(s, encoding, e, logger, devel)
                    else:
                        break
                if res is None:
                    if errors != 'strict' and preferred:
                        res = s.decode(preferred, errors)
                    else:
                        raise
        finally:
            if res is not None:
                return refinefunc(res)

    if refinefunc is None:
        return safe_decode_inner
    else:
        return safe_decode_refined

safe_decode = make_safe_decoder()


def make_safe_stringdecoder(*args, **kwargs):
    """
    Wie make_safe_decoder, aber unter Tolerierung von Nicht-Strings,
    die unverändert zurückgegeben werden

    >>> from visaplan.tools.htmlohmy import _prefixed
    >>> f = make_safe_stringdecoder()
    >>> f(42)
    42
    >>> _prefixed(f('42'))
    u'42'
    >>> _prefixed(f(u'42'))
    u'42'
    """
    f_inner = make_safe_decoder(*args, **kwargs)
    def safe_decoder(s):
        try:
            return f_inner(s)
        except (AttributeError, ValueError):
            return s
    return safe_decoder


def make_safe_recoder(preferred='utf-8', *args, **kwargs):
    r"""
    Wie make_safe_decoder; die erzeugte Funktion gibt jedoch nicht Unicode,
    sondern einen codierten String (preferred-Encoding) zurück.

    >>> from visaplan.tools.htmlohmy import _prefixed
    >>> def d(f, *args, **kw): return _prefixed(repr(f(*args, **kw)))
    >>> def t(f, *args, **kw):
    ...     res = f(*args, **kw)
    ...     print('is (unicode) str / bytes:',
    ...           isinstance(res, six_text_type),
    ...           isinstance(res, bytes))
    ...     if isinstance(res, bytes):
    ...         print(_prefixed(res))
    ...     else:
    ...         print(res)

    >>> recode = make_safe_recoder()
    >>> t(recode, u'ä')
    is (unicode) str / bytes: False True
    b'\xc3\xa4'

    Ein codierter String wird gemäß der Präferenzliste decodiert
    und in der präferierten Codierung zurückgegeben:

    >>> t(recode, '\xa4')
    is (unicode) str / bytes: False True
    b'\xc2\xa4'

    """
    if not preferred:
        raise ValueError('An encoding is needed; '
                         'got %(preferred)r'
                         % locals())
    decode = make_safe_decoder(preferred, *args, **kwargs)
    def safe_recoder(s):
        return decode(s).encode(preferred)

    return safe_recoder


def make_safe_stringrecoder(*args, **kwargs):
    """
    Wie make_safe_recoder, aber unter Tolerierung von Nicht-Strings,
    die unverändert zurückgegeben werden
    """
    f_inner = make_safe_recoder(*args, **kwargs)
    def safe_recoder(s):
        try:
            return f_inner(s)
        except (AttributeError, ValueError):
            return s
    return safe_recoder


def safe_encode(s, charset='utf-8', errors='strict'):
    r"""
    Nimm einen beliebigen Basestring und gib ihn als nicht-Unicode-String
    zurück

    >>> from visaplan.tools.htmlohmy import _prefixed
    >>> def _se(*args, **kw): return _prefixed(safe_encode(*args, **kw))
    >>> _prefixed(_se(u'äöü'))
    b'\xc3\xa4\xc3\xb6\xc3\xbc'
    >>> _prefixed(_se('äöü'))
    b'\xc3\xa4\xc3\xb6\xc3\xbc'

    Hu?!

    (This *should* work, but our test fails ...)
    >>> _se('äöü', 'ascii', 'xmlcharrefreplace')  # doctest: +SKIP
    b'\xc3\xa4\xc3\xb6\xc3\xbc'
    """
    if not s:
        return ''
    # schon ein codierter String: einfach verwenden
    if not isinstance(s, six_text_type):
        return s
    try:
        return s.encode(charset, 'strict')
    except UnicodeEncodeError as e:
        print(e)
        print("Can't encode %(s)r" % locals())
        if errors == 'strict':
            raise
        return s.encode(charset, errors)


def make_safe_encoder(charset='utf-8', errors='replace',
                      logger=None, devel=False):
    """
    Erzeuge eine Funktion safe_encode, die für jeden basestring einen einfachen
    (Nicht-Unicode-) String zurückgibt
    """

    def safe_encode_inner(s):
        r"""
        Nimm einen beliebigen Basestring und gib ihn als nicht-Unicode-String
        zurück
        """
        if not s:
            return ''
        # schon ein codierter String: einfach verwenden
        if not isinstance(s, six_text_type):
            return s
        try:
            return s.encode(charset, 'strict')
        except UnicodeEncodeError as e:
            if logger is not None:
                dest, txt, start, end, msg = e.args
                vorl = (errors == 'strict'
                        and 'endgueltig'
                        or  'vorlaeufig')
                logger.error('Encoding %(vorl)s fehlgeschlagen (-> %(dest)s, msg: %(msg)s', locals())
                logger.error('Zeichen %d/%d: %r', start, len(txt), txt[start:end])
                logger.error('(max.) %d Zeichen davor: %r', 20, txt[start-20:start])
                logger.exception(e)
            if devel:
                # Logging / Debugging:
                from pdb import set_trace
                set_trace()
            if errors == 'strict':
                raise
            if logger:
                logger.info('Zweiter Versuch mit errors=%r', errors)
            return s.encode(charset, errors)

    return safe_encode_inner


NON_XML_WHITESPACE_U = u'\v\f'
def make_whitespace_purger(uchars=NON_XML_WHITESPACE_U):
    r"""
    Erzeuge eine Funktion purge_inapt_whitespace, die einen Unicode-String um
    ungeeigneten Leerraum bereinigt (z. B. vertikale Tab-Zeichen, 0x0b bzw. \v),
    die etree unverdaulich findet.

    Da die Funktion als Nachstufe für safe_decode gedacht ist, akzeptiert sie
    wirklich nur Unicode!

    >>> from visaplan.tools.htmlohmy import _prefixed
    >>> purge_whitespace = make_whitespace_purger()
    >>> def piw(*args, **kw): return _prefixed(purge_whitespace(*args, **kw))
    >>> piw(u'Verbau entfernen und Baugrube verf\xfcllen\x0b')
    u'Verbau entfernen und Baugrube verfüllen'
    >>> piw(u'Verbau entfernen und Baugrube verf\xfcllen\x0b (Fortsetzung)')
    u'Verbau entfernen und Baugrube verfüllen (Fortsetzung)'
    """
    if not isinstance(uchars, six_text_type):
        raise ValueError('Ich will Unicode! (%r)' % (uchars,))
    ucharset = frozenset(uchars)

    def purge_inapt_whitespace(u):
        r"""
        Bereinige den übergebenen unicode-String bzgl. ungeeigneten Leerraums,
        z. B. vertikaler Tab-Zeichen (0x0b bzw. \v), die etree unverdaulich findet.
        """
        if not isinstance(u, six_text_type):
            raise ValueError('Ich will Unicode! (%r)' % (u,))
        if not ucharset.intersection(u):
            return u
        u = u.strip(uchars)
        if not ucharset.intersection(u):
            return u
        for ch in uchars:
            u = u.replace(ch+u' ', u' ')
        for ch in uchars:
            u = u.replace(ch, u' ')
        return u

    return purge_inapt_whitespace

purge_inapt_whitespace = make_whitespace_purger()


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
