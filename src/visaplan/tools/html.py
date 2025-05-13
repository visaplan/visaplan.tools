# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
r"""
visaplan.tools.html: classes, functions and data for HTML support

The `entity` object -- an `HtmlEntityProxy` instance -- resolves mnemonic entity
names to Unicode characters::

    >>> entity['uuml']
    u'\xfc'
    >>> print(entity['uuml'])  # doctest: +SKIP
    ...                        #          (because of normalization problem)
    ü

The `entity_aware` function generates the characters in a string which contains
entities, like e.g. returned by the lxml parser::

    >>> list(entity_aware('e.&thinsp;g.'))
    ['e', '.', '&thinsp;', 'g', '.']

It tries to handle multi-byte characters correctly::

    >>> list(entity_aware('Au&#195;&#159;en'))
    ['A', 'u', '&#195;&#159;', 'e', 'n']

It doesn't currently care about percent-encoded URIs; we don't consider it
likely someone needs a "head" of them::

    >>> list(entity_aware('%20'))
    ['%', '2', '0']

The make_picture function helps to create HTML picture elements (or, mostly: img
elements with srcset attributes) for simple standard cases::

    >>> kw = {'prefix': '/++images++/',
    ...       'source_mask': 'babyface-%(width)d.jpg',
    ...       'joiner': ' '}  # allow for whitespace normalization
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
          src="/++images++/babyface-300.jpg"
          alt="">'

The from_plain_text function converts simple text/plain strings to HTML,
supporting paragraphs and unordered lists:

    >>> plain = (u'''
    ... %(bull)s foo
    ... %(bull)s bar
    ...
    ... And now for something completely different %(hellip)s'''
    ... ) % entity
    >>> print(plain.encode('utf-8'))
    <BLANKLINE>
    • foo
    • bar
    <BLANKLINE>
    And now for something completely different …
    >>> from_plain_text(plain,
    ...                joiner=u' ')            # doctest: +NORMALIZE_WHITESPACE
    u'<ul> <li> foo <li> bar
     </ul>
      <p> And now for something completely different \u2026'

    >>> from_plain_text(u'''
    ... %(bull)s foo
    ... %(bull)s bar
    ...
    ... And now for something completely different %(hellip)s'''
    ... % entity, joiner=u' ')                 # doctest: +NORMALIZE_WHITESPACE
    u'<ul> <li> foo <li> bar
     </ul>
      <p> And now for something completely different \u2026'

"""

# Python compatibility:
from __future__ import absolute_import, print_function

from six import text_type as six_text_type
from six import unichr
from six.moves.html_entities import name2codepoint

# Standard library:
from codecs import BOM_UTF8
from string import whitespace

try:
    # Standard library:
    from html import escape as html_escape
except ImportError:
    # Standard library:
    from cgi import escape as cgi_escape
    def html_escape(s):
        return cgi_escape(s, quote=1)

# Local imports:
from visaplan.tools._builder import from_plain_text
from visaplan.tools.sequences import sequence_slide

__all__ = [
    'entity',  # an --> HtmlEntityProxy
    'entity_aware',
    'make_picture',
    'from_plain_text',
    ## caution; not stable yet, regarding breaking vs. non-breaking space:
    # 'collapse_whitespace',
    ]

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
WHITESPACE = set(six_text_type(whitespace))  # see additions below!
WHITESPACE_ENTITY_NAMES = [
        'nbsp',    # the most important one; universally supported
        'thinsp',  # &#8201; (breaking; not recommended)
        # narrow non-breaking space: &#8239;
        ]

_ENTITY_CHARS = {
        '&':   frozenset('abcdefghijklmnopqrstuvwxyz'
                         'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                         '0123456789_'),
        '&#':  frozenset('0123456789'),
        '&#x': frozenset('0123456789'
                         'abcdef'
                         'ABCDEF'),
        }
# ------------------------------------------------------ ] ... Daten ]

class HtmlEntityProxy(dict):
    r"""
    Zum schnellen und korrekten Zugriff auf symbolische HTML-Entitys

    >>> entity['nbsp']
    u'\xa0'

    Wird im Buchungsmodul verwendet (../browser/booking/utils.py):
    >>> entity['euro']
    u'\u20ac'

    Um z. B. Breadcrumbs zu erzeugen:
    >>> divider = u' %(rarr)s ' % entity
    >>> divider
    u' \u2192 '
    >>> divider.join((u'eins', u'zwei', u'drei'))
    u'eins \u2192 zwei \u2192 drei'
    """
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            val = unichr(name2codepoint[key])
            dict.__setitem__(self, key, val)
            return val


entity = HtmlEntityProxy()
for entity_name in WHITESPACE_ENTITY_NAMES:
    WHITESPACE.add(entity[entity_name])


def entity_aware(s):
    """
    Generate the characters of a string, counting character entities as one.

    >>> list(entity_aware('S&P'))
    ['S', '&', 'P']
    >>> list(entity_aware('S&amp;P'))
    ['S', '&amp;', 'P']
    >>> list(entity_aware('z.&nbsp;B.'))
    ['z', '.', '&nbsp;', 'B', '.']

    The '&#195;' entity is special:
    >>> list(entity_aware('Au&#195;&#159;en'))
    ['A', 'u', '&#195;&#159;', 'e', 'n']

    However, if normal text follows -- who are we to judge?
    >>> list(entity_aware('&#195;'))
    ['&#195;']
    >>> list(entity_aware('&#195;a'))
    ['&#195;', 'a']
    >>> list(entity_aware('&#195;&'))
    ['&#195;', '&']

    The special entity is never followed by named entities;
    in such cases, both are yielded separately:
    >>> list(entity_aware('&#195;&amp;'))
    ['&#195;', '&amp;']

    Empty entities are deconstructed:
    >>> list(entity_aware('&#;&;'))
    ['&', '#', ';', '&', ';']
    >>> list(entity_aware('&&'))
    ['&', '&']

    """
    buf = []

    v = {
        'entity_prefix': None,
        'onshelf': None,
        'in_entity': 0,
        }

    def flush(ch=None):
        if v['onshelf'] is not None:
            yield v['onshelf']
            v['onshelf'] = None

        prefix = v['entity_prefix']
        if prefix is not None:
            for lch in prefix:
                yield lch
            v['entity_prefix'] = None
        elif v['in_entity']:
            yield '&'

        for lch in buf:
            yield lch
        del buf[:]
        if ch is not None:
            yield ch
        v['in_entity'] = 0

    def complete_entity(ch):
        assert v['entity_prefix']
        assert v['in_entity']
        assert buf
        ent = v['entity_prefix'] + ''.join(buf) + ch
        del buf[:]
        v['entity_prefix'] = None
        v['in_entity'] = 0
        return ent

    for ch in s:
        if ch == '&':
            if v['onshelf'] is None:
                for item in flush():
                    yield item
            v['in_entity'] = 1
        elif buf:
            assert v['in_entity']
            assert v['entity_prefix']
            if ch == ';':
                ent = complete_entity(ch)
                if v['onshelf'] is not None:
                    yield v['onshelf'] + ent
                    v['onshelf'] = None
                elif ent == '&#195;':
                    v['onshelf'] = ent
                    continue
                else:
                    for item in flush(ent):
                        yield item
            elif ch in _ENTITY_CHARS[v['entity_prefix']]:
                buf.append(ch)
            else:
                # not a valid entity!
                for item in flush():
                    yield item
                if ch == '&':
                    v['in_entity'] = 1
                else:
                    yield ch
        elif v['entity_prefix'] is not None:
            if ch in _ENTITY_CHARS[v['entity_prefix']]:
                buf.append(ch)
            else:
                for item in flush(ch):
                    yield item
        elif v['in_entity']:  # we had found a '&'
            if ch == '#':
                v['entity_prefix'] = '&'+ch
            elif ch in _ENTITY_CHARS['&']:
                if v['onshelf'] is not None:
                    yield v['onshelf']
                    v['onshelf'] = None
                v['entity_prefix'] = '&'
                buf.append(ch)
            else:
                for item in flush(ch):
                    yield item
        else:
            for item in flush(ch):
                yield item
    for item in flush():
        yield item


def collapse_whitespace(s, preserve_edge=True):
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

    >>> html2=(u'<!DOCTYPE html>\n\n<html>\n    <body>\n        <p>\n'
    ... u'Sehr geehrte(r)\n            Tobias Herp,\n        </p>\n        <p>Ihr '
    ... u'gew\xfcnschter PDF-Export von \u201eHurz\u201c ist abgeschlossen. Sie '
    ... u'k\xf6nnen ihn unter <a '
    ... u'href="https://dev-de.unitracc.deknow-how/fachbuecher/demo-leitfaden-mikrotunnelbau/export_view">'
    ... u'https://dev-de.unitracc.deknow-how/fachbuecher/demo-leitfaden-mikrotunnelbau/export_view</a> '
    ... u'herunterladen.</p>\n        \n    </body>\n</html>\n\n')
    >>> collapse_whitespace(html2, preserve_edge=False)
    u'<!DOCTYPE html> <html> <body> <p> Sehr geehrte(r) Tobias Herp, </p> <p>Ihr gew\xfcnschter PDF-Export von \u201eHurz\u201c ist abgeschlossen. Sie k\xf6nnen ihn unter <a href="https://dev-de.unitracc.deknow-how/fachbuecher/demo-leitfaden-mikrotunnelbau/export_view">https://dev-de.unitracc.deknow-how/fachbuecher/demo-leitfaden-mikrotunnelbau/export_view</a> herunterladen.</p> </body> </html>'

    Achtung: die Unterstützung des charset-Arguments wurde hier vorsätzlich
    entfernt:
    - es wurde nie verwendet
    - wenn so eine Option einmal in der Welt ist, wird man sie nicht mehr los
    - es ist ohnehin schlauer, die Decodierung vorab oder mit einer zu
      übergebenden Funktion zu erledigen
    """
    buf = []
    has_whitespace = False
    for ch in _unicode_without_bom(s):
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


def _unicode_without_bom(s, charset='utf-8'):
    r"""
    Gib die übergebene Zeichenkette als Unicode-String zurück
    und entferne eine etwaige Byte-Order-Markierung (BOM; vim: set bomb?)

    >>> _unicode_without_bom('abc')
    u'abc'
    >>> BOM_UTF8
    '\xef\xbb\xbf'
    >>> _unicode_without_bom('\xef\xbb\xbfÄh')
    u'\xc4h'
    >>> _unicode_without_bom(u'def')
    u'def'
    """
    if isinstance(s, six_text_type):
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


def make_picture(**kw):
    r"""
    Create an HTML <img> element, wrapped in <picture> and / or <a> elements as needed

    What you get is only what you need (if implemented).
    If all you need is to save bandwith by delivering the smallest image
    needed, it should be perfectly fine to simply use an img element with a
    srcset attribute.

    Since this is primarily about saving bandwidth, we default to using the
    smallest resolution image in the src attribute:
    >>> kw = {'prefix': '/++images++/',
    ...       'source_mask': 'babyface-%(width)d.jpg',
    ...       'joiner': ' '}  # allow for whitespace normalization
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
          src="/++images++/babyface-300.jpg"
          alt="">'

    We can choose the largest size instead:
    >>> kw['use_largest'] = True
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
          src="/++images++/babyface-600.jpg"
          alt="">'

    or we can choose an arbitrary resolution explicitly:
    >>> kw['src_width'] = 450
    >>> make_picture(widths=(300, 450, 600),
    ...              **kw)                     # doctest: +NORMALIZE_WHITESPACE
    '<img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-450.jpg 450w,
                  /++images++/babyface-600.jpg 600w"
          src="/++images++/babyface-450.jpg"
          alt="">'

    (We specified that src_width in the widths here as well; otherwise the
    browser wouldn't know about it's size, and why shouldn't it!)

    Ok, let's put this aside and return to the default
    old-browsers-get-the-smallest-image behaviour:

    >>> del kw['src_width']
    >>> del kw['use_largest']

    If we specify an href attribute, the img is wrapped in an anchor element:
    >>> kw['href'] = '/some/fancy/link/'
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
         src="/++images++/babyface-300.jpg"
         alt="">
    </a>'

    Let's add a class to make the image adjust to it's parent element, rather
    than the whole viewport:
    >>> make_picture(widths=(300, 600),
    ...              img_class='img-responsive',
    ...              **kw)                     # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
         src="/++images++/babyface-300.jpg"
         alt=""
         class="img-responsive">
    </a>'

    A title attribute, if given, is always applied to the img element:
    >>> kw['title'] = 'Some fancy image'
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
         src="/++images++/babyface-300.jpg"
         alt=""
         title="Some fancy image">
    </a>'

    >>> kw2 = dict(prefix='/++thumbnail++/abc123-',
    ...            widths=(180, 240),
    ...            source_mask='%(width)d.jpg')
    >>> make_picture(**kw2)                    # doctest: +NORMALIZE_WHITESPACE
    '<img srcset="/++thumbnail++/abc123-180.jpg 180w,
                  /++thumbnail++/abc123-240.jpg 240w"
             src="/++thumbnail++/abc123-180.jpg"
          alt="">'

    To use a `name` option, which might be more convenient in a loop:
    >>> kw2['prefix'] = '/++thumbnail++/'
    >>> kw2.update({
    ...    'prefix':      '/++thumbnail++/',
    ...    'joiner':      ' ',
    ...    'source_mask': '%(name)s-%(width)d.jpg',
    ...    })
    >>> make_picture(name='cde456',
    ...              **kw2)                    # doctest: +NORMALIZE_WHITESPACE
    '<img srcset="/++thumbnail++/cde456-180.jpg 180w,
                  /++thumbnail++/cde456-240.jpg 240w"
             src="/++thumbnail++/cde456-180.jpg"
        alt="">'

    If giving a `rel`, we need to have an `href` as well:
    >>> make_picture(name='abc123',
    ...              rel='uid-abc123',
    ...              **kw2)                    # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
      ...
    TypeError: We need an "href" argument as well!
    >>> make_picture(name='abc123',
    ...              rel='uid-abc123',
    ...              href='/some/fancy/url',
    ...              **kw2)                    # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/url"
        rel="uid-abc123">
      <img srcset="/++thumbnail++/abc123-180.jpg 180w,
                   /++thumbnail++/abc123-240.jpg 240w"
              src="/++thumbnail++/abc123-180.jpg"
           alt="">
    </a>'

    Let's create a loop item for a foils view.
    Our existing preview thumbnails w/o width information are 240px wide,
    but we might have 120px versions as well already:

    >>> kw3 = dict([
    ...  ('joiner', ' '),
    ...  ('prefix', '/++thumbnail++/'),
    ...  ('source_mask', '%(name)s-%(width)d.jpg'),
    ...  ('img_mask', '%(name)s'),
    ...  ('widths', (120,))])
    >>> uid = 'abc123'
    >>> make_picture(name=uid, src=uid, **kw3)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    '<img srcset="/++thumbnail++/abc123-120.jpg 120w"
          src="/++thumbnail++/abc123"
          alt="">'

    We need a surrounding link:
    >>> kw3['href'] = '/oh/anywhere/@@ppt_view?uid=uid-abc123'
    >>> make_picture(name=uid, src=uid, **kw3)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    '<a href="/oh/anywhere/@@ppt_view?uid=uid-abc123">
     <img srcset="/++thumbnail++/abc123-120.jpg 120w"
             src="/++thumbnail++/abc123"
             alt="">
     </a>'

    We want a "rel" attribute:
    >>> kw3['rel'] = 'uid=uid-abc123'
    >>> make_picture(name=uid, src=uid, **kw3)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    '<a href="/oh/anywhere/@@ppt_view?uid=uid-abc123"
        rel="uid=uid-abc123">
     <img srcset="/++thumbnail++/abc123-120.jpg 120w"
             src="/++thumbnail++/abc123"
             alt="">
     </a>'

    And an ID:
    >>> kw3['id'] = 'foil-42'
    >>> make_picture(name=uid, src=uid, **kw3)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    '<a href="/oh/anywhere/@@ppt_view?uid=uid-abc123"
        id="foil-42"
        rel="uid=uid-abc123">
     <img srcset="/++thumbnail++/abc123-120.jpg 120w"
             src="/++thumbnail++/abc123"
             alt="">
     </a>'

    Our image should be responsive:

    >>> kw3['img_class'] = 'img-responsive'
    >>> make_picture(name=uid, src=uid, **kw3)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    '<a href="/oh/anywhere/@@ppt_view?uid=uid-abc123"
        id="foil-42"
        rel="uid=uid-abc123">
     <img srcset="/++thumbnail++/abc123-120.jpg 120w"
             src="/++thumbnail++/abc123"
             alt=""
             class="img-responsive">
     </a>'

    For this to work, we need an outer class as well, e.g.:

    >>> kw3['outer_class'] = 'col-lg-2 col-md-3 col-sm-4 col-xs-6'
    >>> make_picture(name=uid, src=uid, **kw3)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    '<a class="col-lg-2 col-md-3 col-sm-4 col-xs-6"
        href="/oh/anywhere/@@ppt_view?uid=uid-abc123"
        id="foil-42"
        rel="uid=uid-abc123">
     <img srcset="/++thumbnail++/abc123-120.jpg 120w"
             src="/++thumbnail++/abc123"
             alt=""
             class="img-responsive">
     </a>'

    >>> kw3['alt'] = 'Foil 42'
    >>> make_picture(name=uid, src=uid, **kw3)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    '<a class="col-lg-2 col-md-3 col-sm-4 col-xs-6"
        href="/oh/anywhere/@@ppt_view?uid=uid-abc123"
        id="foil-42"
        rel="uid=uid-abc123">
     <img srcset="/++thumbnail++/abc123-120.jpg 120w"
             src="/++thumbnail++/abc123"
             alt="Foil 42"
             class="img-responsive">
     </a>'

    Let's put together the options we have used:
    >>> kw3.update({'name': uid, 'src': uid})
    >>> sorted(kw3.items())                    # doctest: +NORMALIZE_WHITESPACE
    [('alt',            'Foil 42'),
     ('href',           '/oh/anywhere/@@ppt_view?uid=uid-abc123'),
     ('id',             'foil-42'),
     ('img_class',      'img-responsive'),
     ('img_mask',       '%(name)s'),
     ('joiner',         ' '),
     ('name',           'abc123'),
     ('outer_class',    'col-lg-2 col-md-3 col-sm-4 col-xs-6'),
     ('prefix',         '/++thumbnail++/'),
     ('rel',            'uid=uid-abc123'),
     ('source_mask',    '%(name)s-%(width)d.jpg'),
     ('src',            'abc123'),
     ('widths',         (120,))]

    If our image paths all share a longer common prefix, we may use it:
    >>> kw3['prefix'] += kw3.pop('name')
    >>> kw3.update({
    ...    'source_mask': '-%(width)d.jpg',
    ...    'img_mask':    '',})
    >>> sorted(kw3.items())                    # doctest: +NORMALIZE_WHITESPACE
    [('alt',            'Foil 42'),
     ('href',           '/oh/anywhere/@@ppt_view?uid=uid-abc123'),
     ('id',             'foil-42'),
     ('img_class',      'img-responsive'),
     ('img_mask',       ''),
     ('joiner',         ' '),
     ('outer_class',    'col-lg-2 col-md-3 col-sm-4 col-xs-6'),
     ('prefix',         '/++thumbnail++/abc123'),
     ('rel',            'uid=uid-abc123'),
     ('source_mask',    '-%(width)d.jpg'),
     ('src',            'abc123'),
     ('widths',         (120,))]

    The result is the same:
    >>> make_picture(**kw3)                    # doctest: +NORMALIZE_WHITESPACE
    '<a class="col-lg-2 col-md-3 col-sm-4 col-xs-6"
        href="/oh/anywhere/@@ppt_view?uid=uid-abc123"
        id="foil-42"
        rel="uid=uid-abc123">
     <img srcset="/++thumbnail++/abc123-120.jpg 120w"
             src="/++thumbnail++/abc123"
             alt="Foil 42"
             class="img-responsive">
     </a>'

    Those of us who have created responsive images before
    will wonder about the sizes attribute.
    If missing, and if the srcset contains width specification,
    the default value is '100vw'; but we can specify something else, of course:

    >>> kw['sizes'] = '(max-width: 500px) 100vw, 50vw'
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
         sizes="(max-width: 500px) 100vw, 50vw"
         src="/++images++/babyface-300.jpg"
         alt=""
         title="Some fancy image">
    </a>'
    >>> kw['img_style'] = 'max-width: 600px'
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
         sizes="(max-width: 500px) 100vw, 50vw"
         src="/++images++/babyface-300.jpg"
         alt=""
         style="max-width: 600px"
         title="Some fancy image">
    </a>'

    You might want to add some suffix to all URLs, to force the browser to load
    the image from disk instead of simply using a cached version.
    With widths, this can easily be achieved using the source_mask:
    >>> oldmask = kw['source_mask']
    >>> kw['source_mask'] += '?123'
    >>> kw['source_mask']
    'babyface-%(width)d.jpg?123'
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <img srcset="/++images++/babyface-300.jpg?123 300w,
                  /++images++/babyface-600.jpg?123 600w"
         sizes="(max-width: 500px) 100vw, 50vw"
         src="/++images++/babyface-300.jpg?123"
         alt=""
         style="max-width: 600px"
         title="Some fancy image">
    </a>'
    >>> kw['source_mask'] = oldmask

    Now, we provide some basic support for alternate image formats;
    this means, we'll need to create a picture element,
    and for the source element, at least, we'll need a mime-type specification.

    >>> kw['img_mask'] = kw['source_mask']
    >>> kw['source_mask'] = 'babyface-%(width)d.webp'
    >>> kw['source_type'] = 'image/webp'
    >>> del kw['img_style']
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
      ...
    ValueError: We don't support <picture ...> elements with "sizes" specifications yet!
    >>> del kw['sizes']
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <picture>
    <source srcset="/++images++/babyface-300.webp 300w,
                    /++images++/babyface-600.webp 600w"
            type="image/webp">
    <img alt=""
         src="/++images++/babyface-300.jpg"
         title="Some fancy image">
    </picture>
    </a>'

    Wait. This function creates an a[href], if an href argument is given.
    Couldn't it just create this hyperlink without a contained picture and/or
    img, if no image-related arguments are given?

    >>> make_picture(href='/e-journal/', title='E-Journal')
    '<a href="/e-journal/">E-Journal</a>'
    >>> make_picture(href='/e-journal/', title='E-Journal', id='ejournal-link')
    '<a href="/e-journal/" id="ejournal-link">E-Journal</a>'

    Finally, let's check some invalid and/or possibly evil input:
    >>> make_picture(href='#">harmless label<% do bad things %>',
    ...              joiner=' ',
    ...              title='E-Journal')        # doctest: +NORMALIZE_WHITESPACE
    '<a href="#&quot;&gt;harmless label&lt;% do bad things %&gt;">
    E-Journal
    </a>'

    Keyword arguments summary
    -------------------------

    source_mask     a string with '%(...)s'-style placeholders,
                    usually for 'width' and/or 'name'
    source_type     if we have both source_mask and img_mask, we need to create
                    a picture element; and if srcset and src differ in image
                    type, we should at least specify the former.

    prefix          a common prefix for all image resource paths
    joiner          a string, or a 2-tuple of strings
    img_class       a class attribute for the img element
    img_style       a style attribute for the img element
    img_mask        a string with '%(...)s'-style placeholders, usually for
                    'width' (if widths given) and/or 'name'.
                    May be the empty string.
    widths          a sequence of numbers, currently in ascending order,
                    to create the srcset attribute
    sizes           currently a fixed 'sizes' value to help the browser to
                    choose from the widhts; not yet supported for picture
                    elements
    src_width       the width of the src attribute resource
    use_largest     use the largest img source (default: False)

    outer_class     a class attribute for the outmost element.
                    This might be the img element itself, if we don't have a
                    reason to create anything else; however, if we have an
                    `img_class` (above) and no '<a>' to attach to, we create a
                    '<div>' to take it.

    href            a (usually local) URL; if given, we'll get an '<a>' element
                    to wrap the img and/or picture
    rel             as this applies to an '<a>', we require an `href` as well
    title           a title attribute for the img element, or the visible text
                    for an empty a[href]


    TO DO
    -----

    - If we create a srcset attribute with ...w specifications (width
      descriptors), we might need to create a sizes attribute as well!
      We support a fixed `sizes` value, for now.
    - We don't currently support multiple <source> elements.
      We don't currently need them, and we'd probably need a more complicated
      arguments signature.
    - We don't currently support a 'sizes' specification, like
      "(min-width: 400px) 33.3vw, 100vw"; attached to a an <img> with srcset,
      this would mean,

      - in a viewport of at least 400px width, the image takes 33.3% of it's
        with;
      - otherwise (in smaller viewports), take all.

      However, in <source> elements, no such list is supported; instead,
      the media query (including the parentheses) goes in a "media" attribute,
      and the corresponding size specification to the "sizes" attribute;
      for every of the comma-separated specifications, we'd need to create a
      separate <source> element (see above).
      We don't need this right now, and the arguments signature would require
      some consideration.
    """
    kwargs = dict(kw)  # we use our own copy here
    elem_joiner, attr_joiner = _pop_two_joiners(kwargs)
    pop = kwargs.pop
    source_mask = pop('source_mask', None)
    img_mask = pop('img_mask', None)
    prefix = kwargs.get('prefix')
    if prefix:
        insert_slash = pop('insert_slash', 'auto')
        source_mask = _prepend_prefix(source_mask, prefix, insert_slash)
        img_mask = _prepend_prefix(img_mask, prefix, insert_slash)

    widths = pop('widths', None)  # a sequence of integers, or None
    sizes = pop('sizes', None)  # effective default is '100vw'
    source_type = pop('source_type', None)
    img_type = pop('img_type', None)
    src_width = pop('src_width', None)
    use_largest = pop('use_largest',
                      False if widths and src_width is None
                      else None)
    if 'width' in kwargs:
        raise TypeError('Unsupported argument width=%(width)r!' % kwargs)
    outmost_elem = None
    need_picture = False
    need_anchor = False
    elements = []
    leadout_list = []
    srcset = []
    smallest = None

    outmost_attributes = {}
    for attr in ('href', 'id', 'rel'):
        tmp = pop(attr, None)
        if not tmp:
            continue
        if attr == 'href':
            outmost_elem = 'a'
            leadout_list.append('</a>')
        elif attr == 'rel':
            need_anchor = True
        outmost_attributes[attr] = tmp
    if need_anchor and not 'href' in outmost_attributes:
        raise TypeError('We need an "href" argument as well!')

    img_attributes = {}
    for attr in ('alt', 'title'):
        tmp = pop(attr, None)
        if attr == 'alt':
            if tmp is None:
                tmp = ''
        elif not tmp:
            continue
        img_attributes[attr] = tmp
    img_class = pop('img_class', None)
    if img_class:
        img_attributes['class'] = img_class
    img_style = pop('img_style', None)
    if img_style:
        img_attributes['style'] = img_style

    if (img_mask and source_mask):
        pass
    elif img_mask is None:
        img_mask = source_mask
    if source_type is not None:
        if img_type is not None and source_type != img_type:
            need_picture = True
        elif img_mask.endswith('.jpg') and source_type != 'image/jpeg':
            # well ... a frequent case!
            need_picture = True
    if outmost_elem is None:
        if need_picture:
            outmost_elem = 'picture'

    if need_picture:
        leadout_list.insert(0, '</picture>')
        if not source_type:
            raise ValueError('We need to create a picture element, '
                             " but we don't know the source_type!")

    outer_class = pop('outer_class', None)
    if outer_class is not None:
        if img_class is not None or outmost_elem is not None:
            outmost_attributes['class'] = outer_class
            if outmost_elem is None:
                outmost_elem = 'div'
                leadout_list.insert(0, '</div>')
        else:
            img_attributes['class'] = outer_class

    if widths is not None:
        if not source_mask:
            raise ValueError('With widths (=%(widths)r) given, '
                             'we need a source_mask as well, containing '
                             '%%(width)d placeholders!'
                             % locals())
        source_mask += ' %(width)dw'
        for prev_width, width, next_width in sequence_slide(widths):
            if prev_width is None:
                smallest = width
            if width <= prev_width:
                raise ValueError('Currently we expect the widths in ascending'
                                 ' order! (%(prev_width)r < %(width)r)'
                                 % locals())
            largest = kwargs['width'] = width
            srcset.append(source_mask % kwargs)

    try:
        if src_width:
            kwargs['width'] = src_width
        elif use_largest:
            kwargs['width'] = largest
        else:
            kwargs['width'] = smallest
        src = img_mask % kwargs
    except TypeError as e:
        if outmost_elem == 'a' and img_attributes.get('title'):
            src = None
        else:
            raise

    if src is None:
        # we don't have any image data ...
        return elem_joiner.join([_make_singleton('a', **outmost_attributes),
                                 html_escape(img_attributes['title']),
                                 '</a>',
                                 ])

    if outmost_elem is not None:
        tmp_liz = ['<'+ outmost_elem]
        for key in sorted(outmost_attributes.keys()):
            val = outmost_attributes.pop(key)
            tmp_liz.append('%s="%s"' % (key, html_escape(val)))
        elements.append(attr_joiner.join(tmp_liz) + '>')
        if need_picture and outmost_elem != 'picture':
            elements.append('<picture>')

    img_attributes.update(outmost_attributes)
    fancy_attributes = []
    if srcset:
        fancy_attributes.append(('srcset', ', '.join(srcset)))
        if sizes and not need_picture:
            fancy_attributes.append(('sizes', sizes))
        elif sizes:
            raise ValueError("We don't support <picture ...> elements "
                    'with "sizes" specifications yet!')
    if need_picture:
        fancy_attributes.append(('type', source_type))
        # we currently create one <source> element for the fancy parts
        # and leave src (and alt, title) for the fallback <img>
        elements.append(_make_singleton('source', *fancy_attributes))
        elements.append(_make_singleton('img', src=src, **img_attributes))
    else:
        fancy_attributes.append(('src', src))
        elements.append(_make_singleton('img',
                                        *fancy_attributes,
                                        **img_attributes))
    return elem_joiner.join(elements + leadout_list)


def _prepend_prefix(mask, prefix, insert_slash='auto'):
    """
    Helper for make_picture

    >>> _prepend_prefix('%(name)s-%(width)d.jpg', '/img', 'auto')
    '/img%(name)s-%(width)d.jpg'
    >>> _prepend_prefix('%(name)s-%(width)d.jpg', '/img/', 'auto')
    '/img/%(name)s-%(width)d.jpg'
    >>> _prepend_prefix('%(name)s-%(width)d.jpg', '/img/', True)
    '/img/%(name)s-%(width)d.jpg'
    >>> _prepend_prefix('%(name)s-%(width)d.jpg', '/img/', False)
    '/img/%(name)s-%(width)d.jpg'
    >>> _prepend_prefix('%(name)s-%(width)d.jpg', '/img', False)
    '/img%(name)s-%(width)d.jpg'
    >>> _prepend_prefix('%(name)s-%(width)d.jpg', None)
    '%(name)s-%(width)d.jpg'
    >>> _prepend_prefix(None, '/++static++/thumbnail/abc123')
    >>> _prepend_prefix('', '/++static++/thumbnail/abc123')
    '/++static++/thumbnail/abc123'
    """
    if not prefix:
        return mask
    elif mask is None:
        return None
    if insert_slash == 'auto':
        insert_slash = (not mask.startswith('/')
                        and '/' not in prefix)
    if prefix.endswith('/') or not insert_slash:
        return prefix + mask
    return '/'.join((prefix, mask))


def _make_singleton(elem, *attrs, **kwargs):
    """
    Make a simple singleton HTML element

    >>> _ms = _make_singleton
    >>> _ms('img', ('alt', ''), ('src', '/img.jpg'))
    '<img alt="" src="/img.jpg">'
    """
    liz = ['<'+elem]
    attr_joiner = kwargs.pop('attr_joiner', ' ')
    if kwargs:
        attrs += tuple(sorted(kwargs.items()))
    for key, val in attrs:
        liz.append(key + '="' + html_escape(val or '') + '"')
    # return attr_joiner, attrs, kwargs
    return attr_joiner.join(liz) + '>'


def _pop_two_joiners(dic):
    r"""
    A little helper for make_picture

    >>> p2j = _pop_two_joiners

    Here is what we get by default (no joiner specified):
    >>> dic = {'href': '#', 'widths': (300, 600)}
    >>> p2j(dic)
    ('', ' ')

    This will yield the most compact make_picture(...) result.

    We can specify a single joiner which will be used for elements:
    >>> dic = {'href': '#', 'joiner': '\n'}
    >>> p2j(dic)
    ('\n', ' ')
    >>> 'joiner' in dic
    False

    Or we can choose to be explicit about the attributes joiner as well:
    >>> dic = {'href': '#', 'joiner': ('\n\n', '\n')}
    >>> p2j(dic)
    ('\n\n', '\n')
    """
    joiner = dic.pop('joiner', None) or ('', ' ')
    if isinstance(joiner, tuple):
        elem_joiner = joiner[0] or ''
        if joiner[1:]:
            attr_joiner = joiner[1] or ' '
        else:
            attr_joiner = ' '
        return elem_joiner, attr_joiner
    else:
        return joiner or '', ' '


if __name__ == '__main__':
  if 0:
      from pdb import set_trace; set_trace()
      generator = entity_aware('Au&#195;&#159;en')
      res = list(generator)
      print(res)
  elif 0:
      from pdb import set_trace; set_trace()
      kw2 = {'source_mask': '%(name)s-%(width)d.jpg', 'prefix':
      '/++thumbnail++/', 'widths': (180, 240),
      'name': 'abc123', 'rel': 'uid-abc123',
      'joiner': ' '}
      print(make_picture(**kw2))
  elif 0:
      from pdb import set_trace; set_trace()
      kw3 = dict([('alt', 'Foil 42'),
       ('href',         '/oh/anywhere/@@ppt_view?uid=uid-abc123'),
       ('id',           'foil-42'),
       ('img_class',    'img-responsive'),
       ('img_mask',     ''),
       ('joiner',       ' '),
       ('outer_class',  'col-lg-2 col-md-3 col-sm-4 col-xs-6'),
       ('prefix',       '/++thumbnail++/abc123'),
       ('rel',          'uid=uid-abc123'),
       ('source_mask',  '-%(width)d.jpg'),
       ('src',          'abc123'),
       ('widths',       (120,)),
       ])
      print(make_picture(**kw3))

  else:
    # Standard library:
    import doctest
    doctest.testmod()
