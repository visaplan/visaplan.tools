#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79

# Die direkte Verwendung von htmlentitydefs.entitydefs ergibt leider nicht
# zuverlässig das korrekte Unicode-Zeichen, z.B. im Falle von &nbsp;

# Python compatibility:
from __future__ import absolute_import

import six
from six import unichr
from six.moves.html_entities import name2codepoint

# Local imports:
from visaplan.tools.sequences import sequence_slide

try:
    # Standard library:
    from html import escape as html_escape
except ImportError:
    # Standard library:
    from cgi import escape as cgi_escape
    def html_escape(s):
        return cgi_escape(s, quote=1)

# Standard library:
from codecs import BOM_UTF8
from string import whitespace

__all__ = ('entity',  # ein HtmlEntityProxy
           'collapse_whitespace',
           'make_picture',
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
WHITESPACE = set(six.text_type(whitespace))
# print sorted(WHITESPACE)
for entity_name in WHITESPACE_ENTITY_NAMES:
    WHITESPACE.add(entity[entity_name])
# print sorted(WHITESPACE)


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
    if isinstance(s, six.text_type):
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
    create an HTML <img> element, wrapped in <picture> and / or <a> elements as needed

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

    A title attribute is always applied to the img element:
    >>> kw['title'] = 'Some fancy image'
    >>> make_picture(widths=(300, 600), **kw)  # doctest: +NORMALIZE_WHITESPACE
    '<a href="/some/fancy/link/">
    <img srcset="/++images++/babyface-300.jpg 300w,
                  /++images++/babyface-600.jpg 600w"
         src="/++images++/babyface-300.jpg"
         alt=""
         title="Some fancy image">
    </a>'

    Now, we provide some basic support for alternate image formats;
    this means, we'll need to create a picture element,
    and for the source element, at least, we'll need a mime-type specification.

    >>> kw['img_mask'] = kw['source_mask']
    >>> kw['source_mask'] = 'babyface-%(width)d.webp'
    >>> kw['source_type'] = 'image/webp'
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
    ...              title='E-Journal')  # doctest: +NORMALIZE_WHITESPACE
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
    img_mask        a string with '%(...)s'-style placeholders, usually for
                    'width' (if widths given) and/or 'name'
    widths          a sequence of numbers, currently in ascending order,
                    to create the srcset attribute
    src_width       the width of the src attribute resource
    use_largest     use the largest img source (default: False)

    href            a (usually local) URL; if given, we'll get an '<a>' element
                    to wrap the img and/or picture
    title           a title attribute for the img element, or the visible text
                    for an empty a[href]


    TO DO
    -----

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
    src_width = pop('src_width', None)
    use_largest = pop('use_largest',
                      False if widths and src_width is None
                      else None)
    if 'width' in kwargs:
        raise TypeError('Unsupported argument width=%(width)r!' % kwargs)
    outmost_elem = None
    need_picture = False
    elements = []
    leadout_list = []
    srcset = []
    smallest = None

    outmost_attributes = {}
    for attr in ('href', 'id'):
        tmp = pop(attr, None)
        if not tmp:
            continue
        if attr == 'href':
            outmost_elem = 'a'
            leadout_list.append('</a>')
        outmost_attributes[attr] = tmp

    img_attributes = {}
    for attr in ('alt', 'title'):
        tmp = pop(attr, None)
        if attr == 'alt':
            if tmp is None:
                tmp = ''
        elif not tmp:
            continue
        img_attributes[attr] = tmp
    tmp = pop('img_class', None)
    if tmp:
        img_attributes['class'] = tmp

    if (img_mask and source_mask):
        need_picture = True
    elif not img_mask:
        img_mask = source_mask
    if outmost_elem is None:
        if need_picture:
            outmost_elem = 'picture'
    if need_picture:
        leadout_list.insert(0, '</picture>')
        if not source_type:
            raise ValueError('We need to create a picture element, '
                             " but we don't know the source_type!")
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
    >>> _prepend_prefix(None, '/img/')
    >>> _prepend_prefix('', '/img/')
    ''
    """
    if not mask or not prefix:
        return mask
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
    # Standard library:
    import doctest
    doctest.testmod()
