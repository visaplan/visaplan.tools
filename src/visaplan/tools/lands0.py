# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
lands0 -- "lists and strings 0"

Die Funktionen dieses Moduls haben mit Strings und Listen zu tun;
ihre Namen, Signaturen etc. sind noch vorläufig
"""
# Python compatibility:
from __future__ import absolute_import

from six import string_types as six_string_types
from six.moves import range

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"

# Standard library:
from string import strip

try:
    # Standard library:
    from html import escape
except ImportError:
    # Standard library:
    from cgi import escape


__all__ = [
           'conflate',     # sort sequences, stripping out repetitions
           'nouns_first',  # a useful little key function
           # -------------- [ aus unitracc.tools.forms ... [
           'list_of_strings',
           'string_of_list',
           'as_new_list',
           'lines_to_list',
           # -------------- ] ... aus unitracc.tools.forms ]
           # --------------- [ aus unitracc.tools.misc ... [
           'makeListOrNone',
           'makeListOfStrings',
           'makeSet',          # verdaut auch None usw.
           'groupstring',      # wie tomcom-Adapter groupstring
           'join_stripped',
           'make_default_prefixer',
           # --------------- ] ... aus unitracc.tools.misc ]
           ]


def conflate(seq, joiner=u', ', subst=None, keyfunc=None, **kwargs):
    """
    Create a nicely formatted string built from the elements of a sequence
    in arbitrary order.

    We create a little test helper:
    >>> def f(seq, **kw):
    ...     defaults = {'joiner': ', '}
    ...     defaults.update(kw)
    ...     return conflate(seq, **defaults)
    >>> f(['Some', 'silly', 'Sequence'])
    'Sequence, Some, silly'
    >>> f(['Some', 'silly', 'Sequence'], keyfunc=str.lower)
    'Sequence, silly, Some'

    Now some more interesting example:
    >>> f(['Reparatur im Spachtelverfahren',
    ...    'Reparatur durch Injektion',
    ...    'Reparatur mittels Innenmanschetten',
    ...    'Reparatur mit Kurzliner',
    ...    'Reparatur mittels Hutprofil'],
    ...   keyfunc=nouns_first)                # doctest: +NORMALIZE_WHITESPACE
    'Reparatur mittels Hutprofil, Reparatur durch Injektion,
    Reparatur mittels Innenmanschetten, Reparatur mit Kurzliner,
    Reparatur im Spachtelverfahren'

    and, using a substitute:_
    >>> f(['Reparatur im Spachtelverfahren',
    ...    'Reparatur durch Injektion',
    ...    'Reparatur mittels Innenmanschetten',
    ...    'Reparatur mit Kurzliner',
    ...    'Reparatur mittels Hutprofil'],
    ...   subst='~',
    ...   keyfunc=nouns_first)                # doctest: +NORMALIZE_WHITESPACE
    'Reparatur mittels Hutprofil,
    ~          durch   Injektion,
    ~          mittels Innenmanschetten,
    ~          mit     Kurzliner,
    ~          im      Spachtelverfahren'

    (Spaces added to show the interesting part: the order is given by the 3rd
    words each, since those are upper-cased, as is often done in headlines,
    or in German texts for all nouns.)

    What if we need to wrap each topic in an HTML element?
    >>> f(['Reparatur', 'Baugrund'],
    ...   subst='~',
    ...   elem='a',
    ...   klass='label')                # doctest: +NORMALIZE_WHITESPACE
    '<a class="label">Baugrund,</a>
     <a class="label">Reparatur</a>'

    Currently, the "joiner" may contain two characters; if creating HTML,
    the 1st of these is appended as a "tail" to the element's contents,
    and the remainder (usually a blank) separates the elements.
    This is a pragmatic solution which frees you from the need to e.g. add
    those "tails" via CSS in an :after element.

    However, you can use two blanks as a joiner:
    >>> f(['Reparatur', 'Baugrund'],
    ...   subst='~',
    ...   elem='a',
    ...   joiner='  ',
    ...   klass='label')                # doctest: +NORMALIZE_WHITESPACE
    '<a class="label">Baugrund</a>
     <a class="label">Reparatur</a>'

    Since we can't think of a reason to append a blank to the element's
    contents, it is stripped down to an empty string, and the only effective
    joiner is the one separating the elements.

    This will yield "clean" elements which are still separated by blanks.

    Finally, some edge cases.
    If we have a substitution, repetitions are removed (since we iterate all
    values anyway):

    >>> f(['Baugrund', 'Reparatur', 'Baugrund'],
    ...   subst='~')
    'Baugrund, Reparatur'

    Without the substitution, this won't happen, following the GIGO principle:
    >>> f(['Baugrund', 'Reparatur', 'Baugrund'])
    'Baugrund, Baugrund, Reparatur'

    You could easily avoid this giving a set:
    >>> f(set(['Baugrund', 'Reparatur', 'Baugrund']))
    'Baugrund, Reparatur'

    Given an empty sequence, you'll always get an empty string:
    >>> f([])
    ''

    You might have reason to suppress sorting, e.g. for a hierarchy of
    categories, by specifying a non-None falsy keyfunc value:
    >>> f(['Inspection', 'Damage description'], keyfunc=0, joiner=' >> ')
    'Inspection >> Damage description'
    >>> f(['Renovation', 'Lining with pipes',
    ...    'Lining with discrete pipes',
    ...    ], keyfunc=0, subst='...', joiner=' >> ')
    'Renovation >> Lining with pipes >> ... with discrete pipes'

    Creating HTML code, we escape by default:
    >>> f(['Reparatur', 'Bau>grund'],
    ...   subst='<',
    ...   elem='a>"',
    ...   joiner='& ',
    ...   klass='la&bel')                # doctest: +NORMALIZE_WHITESPACE
    '<a&gt;&quot; class="la&amp;amp;bel">Bau&gt;grund&amp;</a&gt;&quot;>
    <a&gt;&quot; class="la&amp;amp;bel">Reparatur</a&gt;&quot;>'

    As you see, quoting happens in all parts, so for untrusted input, you
    shouldn't get harmful HTML code.

    If we don't create HTML, however, we don't do any quoting by default,
    so you are on your own:
    >>> f(['Reparatur', 'Bau>grund'],
    ...   elem=None,
    ...   joiner='& ')                   # doctest: +NORMALIZE_WHITESPACE
    'Bau>grund& Reparatur'

    You can explicitly request quoting:
    >>> f(['Reparatur', 'Bau>grund'],
    ...   quote=True,
    ...   joiner='& ')                   # doctest: +NORMALIZE_WHITESPACE
    'Bau&gt;grund&amp; Reparatur'

    """
    if keyfunc is None or keyfunc:
        liz = sorted(seq, key=keyfunc)
    else:
        liz = list(seq)
    if not liz:
        return joiner.join(liz)

    # HTML element wrapping:
    pop = kwargs.pop
    klass = pop('klass', None)
    elem = pop('elem', 'span' if klass else None)
    quote = pop('quote', elem is not None)
    if quote:
        if elem:
            elem =  escape(elem,  1)
        if klass:
            klass = escape(klass, 1)

    if elem:
        leadin = ['<', elem]
        if klass:
            klass = escape(klass, quote=1)
            leadin.extend([' class="', klass, '"'])
        leadin.append('>')
        leadin = ''.join(leadin)
        leadout = '</%(elem)s>' % locals()
        tail = joiner[:1].strip()
        if quote and tail:
            tail = escape(tail, quote=1)
        joiner = joiner[1:]
    if quote and joiner:
        joiner = escape(joiner, quote=1)

    # substitutions
    if subst is not None and liz[1:]:
        firstword = None
        res = []
        for chunk in liz:
            if chunk in res:
                continue
            sublist = chunk.split()
            if firstword is None:
                firstword = sublist[0]
                res.append(chunk)
                continue
            if sublist[0] == firstword:
                sublist[0] = subst
                res.append(' '.join(sublist))
            else:
                firstword = sublist[0]
                res.append(chunk)
    else:
        res = liz

    if quote:
        res = [escape(chunk, quote=1) for chunk in res]
    if elem:
        return joiner.join([
            leadin + chunk + tail + leadout
            for chunk in res[:-1]
            ] +
            [leadin + res[-1] + leadout])
    else:
        return joiner.join(res)


def nouns_first(s):
    """
    >>> nouns_first('Reparatur mittels Hutprofil')
    ('Reparatur', 'Hutprofil', 'mittels')
    """
    head = []
    tail = []
    for chunk in s.split():
        if chunk[0].isupper():
            head.append(chunk)
        else:
            tail.append(chunk)
    head.extend(tail)
    return tuple(head)


# ------------------------- [ aus unitracc.tools.forms ... [
def list_of_strings(val, splitchar=None, splitfunc=None):
    r"""
    Gib eine Liste zurück, ohne allerdings - wie es die eingebaute
    list-Funktion tun würde - einen String automatisch in eine Liste seiner
    Zeichen aufzusplitten.

    >>> a_list = list('abc')
    >>> a_list
    ['a', 'b', 'c']
    >>> list_of_strings('abc')
    ['abc']

    Im einfachsten Fall wird die Zeichenkette wortweise aufgesplittet:
    >>> list_of_strings(' eins  zwei ')
    ['eins', 'zwei']
    >>> list_of_strings('  ')
    []

    Wird ein "falscher" Wert (außer dem Vorgabewert None) als splitfunc
    übergeben, dann wird zumindest strip angewendet
    (was bei split impliziert ist):

    >>> list_of_strings(' eins  zwei ', splitfunc=False)
    ['eins  zwei']
    >>> list_of_strings('  ', splitfunc=False)
    []

    ... es sei denn, auch splitchar ist "falsch":
    >>> list_of_strings(' eins  zwei ', splitfunc=False, splitchar=False)
    [' eins  zwei ']
    >>> list_of_strings('  ', splitfunc=False, splitchar=False)
    ['  ']
    >>> list_of_strings('', splitfunc=False, splitchar=False)
    []

    Tupel werden zu Listen konvertiert, Sets dabei sortiert;
    None ergibt eine leere Liste;
    Listen werden direkt zurückgegeben:
    >>> a_tuple = tuple('abc')
    >>> list_of_strings(a_tuple)
    ['a', 'b', 'c']
    >>> list_of_strings(a_list) is a_list
    True
    >>> list_of_strings(None)
    []

    "Leere Zeilen" werden *nicht* ausgefiltert
    (hierfür ist besser --> lines_to_list zu verwenden):
    >>> leading_empty = '\neins\nzwei'
    >>> list_of_strings(leading_empty, '\n')
    ['', 'eins', 'zwei']
    """
    if val is None:
        return []
    elif isinstance(val, list):
        # aus Performanzgründen nur das erste Element prüfen:
        if val and not isinstance(val[0], six_string_types):
            raise ValueError('list_of_strings: list contains non-strings!'
                             ' [%r%s]' % (val[0],
                                          val[1:] and ', ...' or ''))
        return val
    elif isinstance(val, set):
        return list_of_strings(sorted(val))
    elif isinstance(val, six_string_types):
        pass
    else:
        return list_of_strings(list(val))

    if splitfunc is None:
        # splitchar=None is documented to use any whitespace:
        return val.split(splitchar)
    elif not splitfunc:
        if splitchar is None:
            val = val.strip()
        elif not splitchar:
            pass
        else:
            val = val.strip(splitchar)
        if val:
            return [val]
        else:
            return []
    elif splitchar is None:
        return splitfunc(val)
    else:
        raise ValueError('list_of_strings(%(val)r):'
                         ' *either* splitchar (%(splitchar)r)'
                         ' *or* splitfunc (%(splitfunc)r)!'
                         % locals())


def string_of_list(val, splitchar='\n', transform=strip):
    r"""
    Gib einen String zurück:
    - Wenn <val> ein String ist, unverändert;
    - wenn eine Liste oder ein Tupel, unter Verwendung von <splitchar>
      verkettet (Bezeichnung angelehnt an --> list_of_strings)

    Nützlich im Zusammenhang mit Formularen, bei denen Stringwerte benötigt
    werden, um Eingabeelemente vorzubelegen, deren Werte in Listen konvertiert
    werden (z. B. :lines-Suffix)

    >>> string_of_list(['a', 'b'])
    'a\nb'
    >>> string_of_list('a\nb')
    'a\nb'

    Wenn die Transformationsfunktion nicht None ist (Standardwert:
    string.strip), werden auch leere Zeilen ausgefiltert:

    >>> string_of_list(['a', '', 'b'])
    'a\nb'

    """
    if val is None:
        return ''
    elif isinstance(val, six_string_types):
        if transform is not None:
            return transform(val)
        return val
    elif transform is None:
        return splitchar.join(val)
    else:
        return splitchar.join([a
                               for a in [transform(line)
                                         for line in val]
                               if a])


def lines_to_list(s):
    r"""
    Konvertiere einen "mehrzeiligen" String in eine Liste

    >>> leading_empty = '\neins\nzwei'
    >>> lines_to_list(leading_empty)
    ['eins', 'zwei']

    >>> lines_to_list('')
    []
    """
    if isinstance(s, six_string_types):
        s = s.splitlines()
    return [_f for _f in [item.strip()
                         for item in s] if _f]


def as_new_list(val, splitfunc=None):
    """
    >>> as_new_list('eins,zwei')
    ['eins', 'zwei']
    >>> liz1 = as_new_list('eins')
    >>> liz1
    ['eins']
    >>> liz2 = as_new_list(liz1)
    >>> liz2 == liz1
    True
    >>> liz2 is liz1
    False
    """
    if val is None:
        return []
    if not isinstance(val, six_string_types):
        return list(val)
    if splitfunc is None:
        return [s.strip() for s in val.split(',')]
    return splitfunc(val)
# ------------------------- ] ... aus unitracc.tools.forms ]

# -------------------------- [ aus unitracc.tools.misc ... [
def makeListOrNone(val, default=None, ch=','):
    """
    Gib eine gefüllte Liste oder None zurück.

    >>> makeListOrNone('eins')
    ['eins']
    >>> makeListOrNone('eins,zwei')
    ['eins', 'zwei']
    >>> makeListOrNone('')
    >>> makeListOrNone(', ,')
    >>> makeListOrNone(None, ', ,')
    >>> makeListOrNone(None, 'drei')
    ['drei']
    >>> makeListOrNone(None, default=['null'])
    ['null']
    """
    if val is None:
        if default is None:
            return default
        else:
            return makeListOrNone(default)
    elif not val:
        return None
    elif isinstance(val, six_string_types):
        val = val.split(ch)
        tmp = [s.strip() for s in val]
        return [s for s in tmp
                if s] or None
    else:
        return list(val) or None


def makeListOfStrings(s, default=None):
    r"""
    für Transmogrifier: String ggf. mit splitlines aufsplitten
    und leere Strings weglassen

    >>> s = '\n  eins \n zwei drei \n \n'
    >>> makeListOfStrings(s)
    ['eins', 'zwei drei']
    >>> makeListOfStrings('  ', ['default'])
    ['default']
    """
    if isinstance(s, (list, tuple)):
        return list(s)
    res = []
    for chunk in s.splitlines():
        val = chunk.strip()
        if val:
            res.append(val)
    if default is not None and not res:
        return default
    return res


def makeSet(s, **kwargs):
    r"""
    Gib jedenfalls ein Set zurück (außer in dem entarteten Fall,
    daß als default explizit ein Nicht-Set übergeben wurde)

    >>> s = '\n  \n zwei drei \n \n'
    >>> makeSet(s)
    set(['zwei drei'])
    >>> makeSet('  ')
    set([])
    >>> makeSet(None)
    set([])
    >>> makeSet('  ', default=None)
    >>> makeSet(42)
    set([42])
    """
    try:
        default = kwargs.pop('default')
    except KeyError:
        has_default = False
    else:
        has_default = True
    if s is None:
        if has_default:
            return default
        return set()
    elif isinstance(s, set):
        pass
    elif isinstance(s, (list, tuple)):
        s = set(s)
    elif isinstance(s, six_string_types):
        tmp = set()
        for chunk in s.splitlines():
            val = chunk.strip()
            if val:
                tmp.add(val)
        s = tmp
    else:
        return set([s])
    if s:
        return s
    elif has_default:
        return default
    return set()


def groupstring(s, size=2, cumulate=False):
    """
    Wie TomCom-Adapter groupstring: Teile einen String in gleiche Häppchen
    einer Maximalgröße <size> auf

    >>> groupstring('abcdef')
    ['ab', 'cd', 'ef']
    >>> groupstring('abc')
    ['ab', 'c']

    Mit cumulate=True werden die Häppchen „aufsummiert“:

    >>> groupstring('abcdef', cumulate=True)
    ['ab', 'abcd', 'abcdef']
    >>> groupstring('abc', cumulate=True)
    ['ab', 'abc']
    """
    if cumulate:
        return [s[0:i + size]
                for i in range(0, len(s), size)
                ]
    else:
        return [s[i:i + size]
                for i in range(0, len(s), size)
                ]


def join_stripped(dic, keys, joiner=' ', strict=True):
    r"""
    Fügt diejenigen Werte aus dem übergebenen Dict zusammen, die einen
    (nach Anwendung der strip-Methode) nicht-leeren Stringwert haben;
    der Standard-"Joiner" ist ein Leerzeichen.

    >>> dic = {'text': ' ein  Text ', 'rest': ' (der  Rest) '}
    >>> KEYS = ['text', 'rest']
    >>> join_stripped(dic, KEYS)
    'ein  Text (der  Rest)'

    Der Joiner kommt nur zum Tragen, wenn mindestens zwei Schlüssel nicht-leere
    Werte haben:
    >>> join_stripped({'text': ' der Text ', 'rest': ' \t'}, KEYS, '\n')
    'der Text'

    Es wird davon ausgegangen, daß die Schlüssel existieren,
    und daß die Werte Strings sind (z. B. bei der Verarbeitung des
    groupdict-Ergebnisses eines RE-Match-Objekts).
    """
    res = []
    for k in keys:
        try:
            v = dic[k].strip()
            if v:
                res.append(v)
        except KeyError:
            if strict:
                raise
    return joiner.join(res)


def make_default_prefixer(default_prefix, other_prefixes=None):
    """
    >>> prefixed = make_default_prefixer('a-', ['b-'])
    >>> prefixed('X')
    'a-X'
    >>> prefixed('a-X')
    'a-X'
    >>> prefixed('b-X')
    'b-X'

    Anwendung für Migrationsschritte:
    >>> safe_context_id = make_default_prefixer('profile-', ['snapshot-'])
    >>> safe_context_id('Products.unitracc:default')
    'profile-Products.unitracc:default'

    Aus Performanzgründen wird ein multi_prefixer nur erzeugt,
    wenn es wirlich nötig ist:

    >>> prefixed.__name__
    'multi_prefixer'
    >>> make_default_prefixer('a-').__name__
    'simple_prefixer'
    >>> make_default_prefixer('a-', ['a-']).__name__
    'simple_prefixer'
    """

    def simple_prefixer(s):
        if s.startswith(default_prefix):
            return s
        return default_prefix + s

    if other_prefixes:
        a_p = [default_prefix]
        for p in other_prefixes:
            if p not in a_p:
                a_p.append(p)
        multi = bool(a_p[1:])
    else:
        multi = False

    def multi_prefixer(s):
        for p in a_p:
            if s.startswith(p):
                return s
        return default_prefix + s

    if multi:
        return multi_prefixer
    return simple_prefixer
# -------------------------- ] ... aus unitracc.tools.misc ]


if __name__ == '__main__':
    class MockRequest(dict):
        # kopiert ins mock-Modul
        def __init__(self, referer=None, **kwargs):
            self['HTTP_REFERER'] = referer
            self['ACTUAL_URL'] = kwargs.pop('actual_url', referer)
            self.form = kwargs

    # Standard library:
    import doctest
    doctest.testmod()
