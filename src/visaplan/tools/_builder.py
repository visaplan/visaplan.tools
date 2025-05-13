# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79 cc=+1
r"""
visaplan.tools._builder: simple text-to-HTML conversions

Currently we have one exposed function here: `from_plain_text`.

All we support is

- paragraphs
- unordered lists (not nested)
- hard linebreaks

Let's use this as an example:

>>> plain = '''
... All we support is
...
... - paragraphs
... - unordered lists (not nested)
... - hard linebreaks
...
... Let's use this as an example:
... '''

But first we'll create a little test helper function:

>>> from visaplan.tools.htmlohmy import _prefixed
>>> def fpt(txt):
...     return _prefixed(from_plain_text(txt, joiner=u' '))
>>> fpt(plain)       # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    u'<p> All we support is
     <ul> <li> paragraphs
          <li> unordered lists (not nested)
          <li> hard linebreaks
     </ul>
     <p> Let...s use this as an example:'

Things demonstrated here:

- We create quite minimalistic HTML; a paragraph is automatically terminated if
  a block element is found (i.e., '<p> some text <ul>...</ul> more text </p>'
  yields a '<p>some text</p>' paragraph, an unordered list, some unframed text,
  and an orphaned closing '</p>' tag.
  Thus, closing '</p>' elements are optional, so we don't bother to create
  them.
- In contrast, <p> elements *can* occur in list items; so we simply terminate
  a list when a new paragraph starts.

Now, into the details.

>>> fpt(u'  ')
u''
>>> fpt(u'A two-line\nparagraph')
u'<p> A two-line <br> paragraph'
>>> fpt(u'A paragraph\n  \nand a 2nd one')     # doctest: +NORMALIZE_WHITESPACE
u'<p> A paragraph
 <p> and a 2nd one'
>>> fpt('\nImmer Ärger mit\n* Harry  \n* Sally')           # doctest: +ELLIPSIS
u'<p> Immer ...rger mit <ul> <li> Harry <li> Sally'
>>> fpt('''
... empty first
... and last lines
... + are skipped
... ''')
u'<p> empty first <br> and last lines <ul> <li> are skipped'

>>> fpt('''Trailing
... + whitespace  \t
... + is stripped   \t
... ''')
u'<p> Trailing <ul> <li> whitespace <li> is stripped'

HTML special characters are escaped:
>>> fpt('S & P')
u'<p> S &amp; P'
>>> fpt('- S & P\n- visaplan\n- clever & smart')
u'<ul> <li> S &amp; P <li> visaplan <li> clever &amp; smart'

>>> plain = u'''
... * foo
... * bar
... And now for something completely different ...'''
>>> fpt(plain)                                 # doctest: +NORMALIZE_WHITESPACE
    u'<ul> <li> foo <li> bar </ul>
     <p> And now for something completely different ...'

"""

# Python compatibility:
from __future__ import absolute_import

from six import string_types as six_string_types
from six import text_type as six_text_type
from six import unichr

from sys import version_info
if version_info[0] <= 2:
    from six.moves.html_entities import name2codepoint
else:
    from html.entities import name2codepoint

# Standard library:
from string import whitespace

# Local imports:
from visaplan.tools.coding import safe_decode
from visaplan.tools.sequences import sequence_slide

__all__ = [
    'from_plain_text',  # build HTML from [* ]lines
    ]


# as long as we have this in a separate module,
# we'd rather not use the HtmlEntityProxy:
BULLET_CHARS = set([unichr(name2codepoint['bull']),
                    ] + list(u'*-+'))

try:
    # Standard library:
    from html import escape as html_escape
except ImportError:
    # Standard library:
    from cgi import escape as cgi_escape
    def html_escape(s):
        return cgi_escape(s, quote=1)


class LineInfo(object):
    r"""
    >>> print(sorted(BULLET_CHARS))  # doctest: +FAIL_FAST
    ['*', '+', '-', '•']

    >>> LineInfo(u'An ordinary paragraph.')
    <LineInfo('An ordinar...')>

    >>> LineInfo(u'* A list item.')
    <LineInfo(bullet='*'; 'A list ite...')>
    >>> LineInfo(u'+ A list item.')
    <LineInfo(bullet='+'; 'A list ite...')>
    >>> LineInfo(u'- A list item.')
    <LineInfo(bullet='-'; 'A list ite...')>
    >>> LineInfo(u'*Not considered a list item.')
    <LineInfo('*Not consi...')>
    >>> LineInfo(u'  * An indented list item.')
    <LineInfo(bullet='*'; prefix='  '; 'An indente...')>
    >>> LineInfo(u'  *  Another indented list item.')
    <LineInfo(bullet='*'; prefix='  '; 'Another in...')>
    >>> LineInfo(u'  ')  # empty line
    <LineInfo(empty)>

    """
    def __init__(self, s):
        assert isinstance(s, six_text_type)

        s = s.rstrip()
        self.bullet = bullet = None
        pref = []
        i = 0
        for ch in s:
            if ch in BULLET_CHARS:
                bullet = ch
            elif ch in whitespace:
                if bullet is None:
                    pref.append(ch)
                else:
                    self.bullet = bullet
                    break
            else:
                break
            i += 1
        self.prefix = (u''.join(pref) if pref
                       else None)
        offset = 0
        if pref:
            self.prefix = u''.join(pref)
            offset += len(pref)
        else:
            self.prefix = None
        if self.bullet:
            offset += 2
        self.text = s[offset:].lstrip()
        self.empty = not self.text

    def __repr__(self):
        liz = [u'<', self.__class__.__name__, u'(']

        tail = []
        def add(more):
            if tail:
                tail.append(u'; ')
            tail.extend(more)

        if self.bullet is not None:
            add([u'bullet=', u'\'', self.bullet, u'\''])
        if self.prefix is not None:
            add([u'prefix=', u'\'', self.prefix, u'\''])
        if self.empty:
            add([u'empty'])
        else:
            txt = self.text[:10]
            if self.text[10:]:
                txt += u'...'
            if u'\'' in txt:
                add(u["\"", txt, u"\""])
            else:
                add([u'\'', txt, u'\''])
        tail.append(u')>')
        liz.extend(tail)
        return u''.join(liz)


def from_plain_text(txt, joiner=u'', decode=None):
    r"""
    Convert a simple text to HTML

    As already mentioned, all we support is

    - paragraphs
    - unordered lists
    - hard linebreaks.

    We don't try to be as complete as reStructuredText or Markdown;
    there is no headlines support or other fancy stuff.

    For our tests, we use a little helper function:
    >>> from visaplan.tools.htmlohmy import _prefixed
    >>> def fpt(txt):
    ...     return _prefixed(from_plain_text(txt, joiner=u' '))
    >>> fpt(u'  ')
    u''
    >>> fpt(u'A two-line\nparagraph')
    u'<p> A two-line <br> paragraph'
    >>> fpt(u'A paragraph\n\nand a 2nd one')  # doctest: +NORMALIZE_WHITESPACE
    u'<p> A paragraph
     <p> and a 2nd one'
    >>> fpt('\nImmer Ärger mit\n* Harry  \n* Sally')      # doctest: +ELLIPSIS
    u'<p> Immer ...rger mit <ul> <li> Harry <li> Sally'
    >>> fpt('''
    ... empty first
    ... and last lines
    ... + are skipped
    ... ''')
    u'<p> empty first <br> and last lines <ul> <li> are skipped'

    >>> fpt('''Trailing
    ... + whitespace  \t
    ... + is stripped   \t
    ... ''')
    u'<p> Trailing <ul> <li> whitespace <li> is stripped'

    HTML special characters are escaped:
    >>> fpt('S & P')
    u'<p> S &amp; P'
    >>> fpt('- S & P\n- visaplan\n- clever & smart')
    u'<ul> <li> S &amp; P <li> visaplan <li> clever &amp; smart'

    Now for some special cases.

    Currently, we silently accept different bullet characters in a row:
    >>> fpt('- dashed list item,\n+ and one with a plus sign')
    u'<ul> <li> dashed list item, <li> and one with a plus sign'

    Currently we don't support nested lists; the amount of leading whitespace
    is ignored:
    >>> fpt('''
    ... * main list topic
    ...   + sublist topic
    ...     - innermost topic
    ... ''')
    u'<ul> <li> main list topic <li> sublist topic <li> innermost topic'

    Corner cases (strange input):

    Bullet points are recognised only if followed by text:
    >>> fpt('  *')
    u'<p> *'
    >>> fpt('  * ')
    u'<p> *'
    >>> fpt('  * A')
    u'<ul> <li> A'

    Leading whitespace is ignored, unless we are in a list; in this case, the
    current list item is continued:

    >>> fpt('''
    ... - first item
    ...   continued after a line break
    ... - second item
    ...
    ...   After an empty line, we have a new paragraph.
    ...   ''')                                # doctest: +NORMALIZE_WHITESPACE
    u'<ul> <li> first item
               <br> continued after a line break
          <li> second item
    </ul>
     <p> After an empty line, we have a new paragraph.'

    """
    if decode is None:
        decode = safe_decode
    if isinstance(txt, bytes):
        txt = decode(txt)
    res = []
    seq = (LineInfo(line) for line in txt.splitlines())
    in_list = False
    for prev_o, o, next_o in sequence_slide(seq):
        if o.empty:
            if in_list:
                res.append(u'</ul>')
                in_list = 0
            continue
        if o.bullet:
            if not in_list:
                res.append(u'<ul>')
                in_list = 1
            res.extend([u'<li>', html_escape(o.text)])
        elif in_list and o.prefix:
            res.extend([u'<br>', html_escape(o.text)])
        else:
            if in_list:
                res.append(u'</ul>')
            if in_list or prev_o is None or prev_o.empty:
                res.append(u'<p>')
                in_list = 0
            else:
                res.append(u'<br>')
            res.append(html_escape(o.text))
    return joiner.join(res)


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
