#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79

# Die direkte Verwendung von htmlentitydefs.entitydefs ergibt leider nicht
# zuverlässig das korrekte Unicode-Zeichen, z.B. im Falle von &nbsp;

from htmlentitydefs import name2codepoint
from string import whitespace
from codecs import BOM_UTF8


__all__ = ('entity',  # ein HtmlEntityProxy
           'collapse_whitespace',
           )

# ------------------------------------------------------ [ Daten ... [

# Blockelemente: hier als solche Elemente verstanden, die in einem <p>, <span>
# oder <a> nicht vorkommen dürfen
BLOCK_ELEMENT_NAMES = set([
    'div', 'p',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'dl', 'ol', 'ul',
    'dt', 'dd',
    'table', # strenggenommen, lt. CSS 2.1: display: table
    ])
# <http://www.cs.tut.fi/~jkorpela/html/empty.html#html>:
EMPTY_ELEMENT_NAMES = set([
     'area', 'base', 'basefont', 'br', 'col', 'frame',
     'hr', 'img', 'input', 'isindex', 'link', 'meta',
     'param',
     ])
REPLACED_ELEMENT_NAMES = set([
     'hr', 'img', 'br',
     ])
# Da gäbe es noch mehr; erstmal der ständig verwendete Kandidat:
WHITESPACE_ENTITY_NAMES = ['nbsp']
# ------------------------------------------------------ ] ... Daten ]

class HtmlEntityProxy(dict):
    r"""
    Zum schnellen und korrekten Zugriff auf symbolische HTML-Entitys

    >>> entity['nbsp']
    u'\xa0'

    Wird im Buchungsmodul verwendet (../browser/booking/utils.py):
    >>> entity['euro']
    u'\u20ac'
    """
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            val = unichr(name2codepoint[key])
            dict.__setitem__(self, key, val)
            return val


entity = HtmlEntityProxy()
WHITESPACE = set(unicode(whitespace))
# print sorted(WHITESPACE)
for entity_name in WHITESPACE_ENTITY_NAMES:
    WHITESPACE.add(entity[entity_name])
# print sorted(WHITESPACE)


def collapse_whitespace(s, preserve_edge=True, charset='utf-8'):
    r"""
    Für Konversion von HTML zu text/plain:
    Kollabiere jeglichen Leerraum des übergebenen Strings.
    Der String wird als reiner Text behandelt und *nicht* auf HTML-Elemente
    untersucht!

    s -- ein String. Wenn nicht Unicode, wird er mit dem übergebenen
         Zeichensatz decodiert.
    preserve_edge - Wenn True (Vorgabe), wird Leerraum am Anfang und Ende
                    (wie im Innern) kollabiert;
                    wenn False, wird er entfernt.
    charset - Vorgabewert: 'utf-8'

    >>> html = '  <div> <p>  Bla\n  Blubb  </p> </div>  '
    >>> collapse_whitespace(html)
    u' <div> <p> Bla Blubb </p> </div> '
    >>> collapse_whitespace(html, preserve_edge=False)
    u'<div> <p> Bla Blubb </p> </div>'
    >>> footertxt = ('http://www.unitracc.de'
    ...              ' %(nbsp)s|%(nbsp)s '
    ...              'http://www.unitracc.com'
    ...              ) % entity
    >>> collapse_whitespace(footertxt)
    u'http://www.unitracc.de | http://www.unitracc.com'
    """
    buf = []
    has_whitespace = False
    for ch in unicode_without_bom(s):
        if ch in WHITESPACE:
            if buf or preserve_edge:
                has_whitespace = True
            continue
        if has_whitespace:
            buf.append(' ')
            has_whitespace = False
        buf.append(ch)
    if preserve_edge and has_whitespace:
        buf.append(' ')
    return u''.join(buf)


def unicode_without_bom(s, charset='utf-8'):
    r"""
    Gib die übergebene Zeichenkette als Unicode-String zurück
    und entferne eine etwaige Byte-Order-Markierung (BOM; vim: set bomb?)

    >>> unicode_without_bom('abc')
    u'abc'
    >>> BOM_UTF8
    '\xef\xbb\xbf'
    >>> unicode_without_bom('\xef\xbb\xbfÄh')
    u'\xc4h'
    >>> unicode_without_bom(u'def')
    u'def'
    """
    if isinstance(s, unicode):
        return s
    # BOM-Präfix ist kein Unicode, sondern eine Bytes-Folge
    # --> implizit ausgelöste Decodierung von s
    # --> schlägt fehl bei Umlauten und Standard-Encoding ASCII  
    # ... also oben Unicode vorab behandeln
    if s.startswith(BOM_UTF8):
        s = s[len(BOM_UTF8):]
        if charset is None:
            charset = 'utf-8'
        elif charset.lower() != 'utf-8':
            charset = 'utf-8'
    return s.decode(charset, 'replace')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
