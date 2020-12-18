# -*- coding: utf-8 -*- äöü vim: sw=4 sts=4 si et textwidth=72 cc=+8
"""
visaplan.tools.debug - Helferlein für Entwicklung und Debugging

Autor: Tobias Herp
"""
# Python compatibility:
from __future__ import absolute_import, print_function

from six import string_types as six_string_types
from six import text_type as six_text_type
from six.moves import map

# Local imports:
from visaplan.tools.minifuncs import check_kwargs

# ACHTUNG - Importe aus dem unitracc-Produkt stets incl. des
# Products-Kontexts vornehmen, also
#   "from Products.unitracc.tools.ModulXY import ..."
# anstelle von
#   "from unitracc.tools.ModulXY import ..." --
# ansonsten können Probleme mit dem Pickle-Storage etc. auftreten!

__all__ = [
           # ----------------------- [ aus unitracc.tools.debug2 ... [
           'pp',
           'log_or_trace',  # Universalwerkzeug; siehe auch trace_this
           # ----------------------- ] ... aus unitracc.tools.debug2 ]
           'pretty_callstack',
           # ------------------------ [ aus unitracc.tools.debug ... [
           'trace_this',    # ... für einfache Fälle
           'arginfo',
           'pretty_funcname',
           'asciibox',        # Ausgabe
           'asciibox_lines',  # ... dieser Liste
           'print_indented',  # Ausgabe mit Einrückung
           'make_sleeper',    # Ausgabe entschleunigen, mit Logging
           # Metadekoratoren (Dekorator-Erzeuger):
           'log_result',
           # ------------------------ ] ... aus unitracc.tools.debug ]
           'has_strings',     # mit formatierter Ausgabe
           # make_debugfile_writer  (requires some more love; see below)
           ]

# Standard library:
from collections import defaultdict
from functools import wraps
from pprint import pformat, pprint
from time import sleep
from traceback import extract_stack

try:
    # Logging / Debugging:
    from visaplan.plone.tools.log import getLogSupport
except ImportError:
    getLogSupport = None
try:
    # Local imports:
    from visaplan.tools.minifuncs import gimme_False
except ImportError:
    gimme_False = lambda: False

# ------------------------------------------------------ [ Daten ... [
_TRACE_SWITCH = defaultdict(gimme_False)
# ------------------------------------------------------ ] ... Daten ]


# ---------------------------------- [ aus unitracc.tools.debug2 ... [
# ------------------------------------------ [ log_or_trace ... [
class log_or_trace(object):
    """
    Meta-Dekorator für Funktionen: Gib einen Dekorator zurück, der die
    übergebene Funktion <func> dekoriert oder auch unverändert zurückgibt.

    Empfohlene Verwendung:

      from visaplan.plone.tools.log import getLogSupport
      logger, debug_active, DEBUG = getLogSupport()
      lot_kwargs = {'logger': logger,
                    'debug_level': debug_active,
                    # ggf. weitere Optionen ...
                    }
      ...
      @log_or_trace(**lot_kwargs)
      def ...

    Um einzelne Funktionen bzw. Methoden besonders zu behandeln, kann die
    Funktion "updated" verwendet werden:

      from visaplan.tools.dicts import updated
      ...
      @log_or_trace(**updated(lot_kwargs, trace=1))
      def ...

    Um einfach eine einzelne Funktion zu debuggen, bietet sich
    alternativ die Funktion --> trace_this an.
    """

    def __init__(self, debug_level, **kwargs):
        """
        Wenn ein "wahrer" debug_level übergeben wird, wird ein Dekorator
        zurückgegeben, der die übergebene Funktion mit Logging und/oder set_trace
        einrahmt; ist debug_level False, werden alle weiteren Argumente ignoriert,
        und der zurückgegebene "Dekorator" gibt einfach nur sein Argument
        unverändert zurück.

        Schlüsselwort-Argumente:
        - log -- Protokollierung einschalten?
        - logger -- wenn ein Logger übergeben wird, wird log=True impliziert
                    (wenn nicht ein expliziter Wert angegeben wurde)
        - trace -- Einzelschrittausführung einschalten?
        - trace_key -- Schlüsselwert zum ein- und ausschalten der
                       Einzelschrittausführung
        """
        assert debug_level >= 0
        self.debug_level = debug_level
        self.log = kwargs.get('log')
        self.logger = kwargs.get('logger')
        self.trace = kwargs.get('trace')
        self.trace_key = kwargs.get('trace_key')
        self.kwargs = kwargs

    def __call__(self, func):
        if not self.debug_level:
            return func
        log = self.log
        if (log is not None and not log
            and not self.trace
            and not self.trace_key
            ):
            return func

        pretty_name = pretty_funcname(func)
        trace = self.trace
        trace_key = self.trace_key
        if trace and trace_key is None:
            trace_key = pretty_name
        elif trace_key and trace is None:
            trace = True
        if trace_key:
            INFO_MASK = '\n'.join(('',
                        '*** switched_tracer for %(inner1)r',
                        '*** trace_key is "%(trace_key)s"',
                        ">>> pprint(dict(globals()['_TRACE_SWITCH']))",
                        ">>> globals()['_TRACE_SWITCH'][%(trace_key)r] = False",
                        ''
                        ))
            def trace_on(key=trace_key):
                globals()['_TRACE_SWITCH'][key] = True

            def trace_off(key=trace_key):
                globals()['_TRACE_SWITCH'][key] = False
            globals()['_TRACE_SWITCH'][trace_key] = trace
            # Logging / Debugging:
            from pdb import set_trace

            inner1 = func

            @wraps(func)
            def switched_tracer(*args, **kw):
                if globals()['_TRACE_SWITCH'][trace_key]:
                    print(INFO_MASK % locals())
                    set_trace()  # trace_on|off()
                res = inner1(*args, **kw)
                return res  # ... switched_tracer

            func = switched_tracer

        # nun das Logging:
        logger = self.logger
        kwargs = self.kwargs
        verbose = kwargs.get('verbose', True)
        log_args = kwargs.get('log_args')
        if log_args is None:
            log_args = verbose
        log_result = kwargs.get('log_result')
        result_formatter = kwargs.get('result_formatter', pformat)
        if log_result is None:
            log_result = verbose
        if log is None and logger is not None:
            log = True
        elif logger is None:
            if log is None:
                # wenn verbose (Vorgabe), sind beide True:
                log = log_args or log_result or False
        if log and (logger is None):
            if getLogSupport is None:
                raise TypeError('log=%(log)r, but no logger given!'
                                % locals())
            logger, _da, _dbg = getLogSupport(fn=__file__)

        if log:
            if verbose and trace_key:
                logger.info('%s: trace_(on|off)(key=%r), Startwert: %s',
                       pretty_name, trace_key, trace)

            inner2 = func

            @wraps(func)
            def logging_wrapper(*args, **kw):
                if log_args:
                    logger.info('%s(%s) ...', pretty_name, arginfo(*args, **kw))
                else:
                    logger.info('%s(...) ...', pretty_name)
                res = inner2(*args, **kw)
                if (res is None) or not log_result:
                    logger.info('%s(...).', pretty_name)
                elif result_formatter is not None:
                    logger.info('%s(...) -->\n%s', pretty_name,
                                result_formatter(res))
                else:
                    logger.info('%s(...) --> %r', pretty_name, res)
                return res

            func = logging_wrapper

        return func
# ------------------------------------------ ] ... log_or_trace ]


def pp(*args, **kwargs):
    """
    Gib die übergebenen Argumente mit pprint aus - nach einer Information über
    die aufrufende Stelle im Code.

    Es besteht oft das Bedürfnis, während der Entwicklung Werte zur Konsole
    auszugeben.  Im Ergebnis stehen dann viele Ausgaben, bei denen hinterher
    nicht ersichtlich ist, in welchem Modul sie erzeugt werden.
    Das erschwert das Aufräumen zuweilen erheblich.

    Der Fokus liegt hier weniger auf Schönheit als auf Einfachheit:
    Die Funktion ist einfach zu benutzen und gibt die benötigten Informationen
    aus; die Informationen über den Aufruf stehen jeweils in der ersten Zeile.
    """

    raw_info = extract_stack(limit=2)
    filename, lineno, funcname = raw_info[0][:3]
    if filename.endswith('.pyc'):
        filename = filename[:-1]
    if funcname:
        prefix = '%(filename)s[%(funcname)s]: %(lineno)d'
    else:
        prefix = '%(filename)s: %(lineno)d'
    tup = (prefix % locals(),
           ) + args + tuple(kwargs.items())
    pprint(tup)
# ---------------------------------- ] ... aus unitracc.tools.debug2 ]


def pretty_callstack(limit=3, revert=True, verbose=True):
    """
    Ermittle die letzten <limit> aufrufenden Funktionen
    """
    raw_info = extract_stack(limit=limit+1)
    res = []
    for tup in raw_info[:-1]:
        filename, lineno, funcname = tup[:3]
        if filename.endswith('.pyc'):
            filename = filename[:-1]
        res.append((funcname
            and '%(filename)s[%(funcname)s]: %(lineno)d'
            or  '%(filename)s: %(lineno)d'
            ) % locals())
    if verbose:
        hint = ('The last %d calling functions, innermost %s:'
                ) % (len(res),
                     revert and 'FIRST' or 'last',
                     )
    if revert:
        res.reverse()
    if verbose:
        res.insert(0, hint)
    return res


# ----------------------------------- [ aus unitracc.tools.debug ... [
def trace_this(func):
    """
    Dekoratorfunktion für Entwicklung/Debugging:
    - Information über das Betreten der Funktion und die Argumente
    - anschließend pdb.set_trace()

    Um das Debugging vom Entwicklungsmodus abhängig zu machen etc.,
    kann stattdessen der mit Argumenten zu verwendende Dekorator -->
    log_or_trace verwendet werden.
    """
    NAME = func.__name__
    AFTERDARK = '... %s -->' % NAME
    LABEL = NAME + '('
    # Standard library:
    from pprint import pprint

    @wraps(func)
    def inner(*args, **kwargs):
        label = [LABEL] + list(args)
        print(asciibox(label, kwargs=kwargs))
        # Logging / Debugging:
        import pdb
        pdb.set_trace()  # --------- # @trace_this (sichtbarer Hinweis):
        res = func(*args, **kwargs)  # [s]tep into
        # TODO: - trace automatisch wieder zurücksetzen
        #       - evtl. Ergebnisausgabe weiter aufhübschen
        print(AFTERDARK)
        pprint(res)
        return res

    return inner


def arginfo(*args, **kwargs):
    """
    Stringdarstellung der übergebenen Argumente

    >>> arginfo('eins', zwei=3)
    "'eins', zwei=3"
    """
    liz = [repr(a) for a in args]
    liz.extend(['%s=%r' % tup
                for tup in kwargs.items()
                ])
    return ', '.join(liz)


def pretty_funcname(fo):
    """
    Gib einen nützlicheren Funktionsnamen als "__call__" etc. zurück

    fo -- ein Funktionsobjekt

    Bietet noch etwas Verbesserungspotential ...
    """
    if fo.__name__ != '__call__':
        # evtl. noch Modulinformationen hinzufügen
        return fo.__name__
    liz = fo.__module__.split('.')
    if 'unitracc' not in liz:
        return fo.__module__
    if liz[-1] not in ('browser', 'adapter'):
        return fo.__module__
    if liz[-1] == 'browser':
        return 'unitracc@@%s' % liz[-2]
    if liz[-1] == 'adapter':
        return 'unitracc->%s' % liz[-2]
    return fo.__module__


def log_result(logger=None, logfunc=None):
    """
    Gib eine Dekorator-Funktion zurück, die den Aufruf einer Funktion
    und ihr Ergebnis einzeilig protokolliert
    (z. B. für cachekey-Funktionen);
    für einfache Funktionen, deren innere Logik weniger spannend ist als
    das Faktum ihres Aufrufs.

    Verwendung z. B.:

      from visaplan.tools.debug import log_result
      ...
      @log_result(logger=logger)
      def cachekey(...):
         ...
    """
    if logfunc is None:
        if logger is None:
            logger = debug_logger
        logfunc = logger.info
    elif isinstance(logfunc, str):
        if logger is None:
            logger = debug_logger
        logfunc = getattr(logger, logfunc)
    elif logger is not None:
        debug_logger.warning('logfunc given (%(logfunc)r), '
                             'ignoring logger (%(logger)r)',
                             locals())

    def decorate(func):
        MASK = '%s(...) --> %%(res)s' % (func.__name__,)

        @wraps(func)
        def inner(*args, **kwargs):
            res = func(*args, **kwargs)
            logfunc(MASK, locals())
            return res
        return inner

    return decorate


# ---------------------------- [ asciibox + Hilfsfunktionen ... [
def gen_prefix(prefix, *args, **kwargs):
    """
    Hilfsfunktion für asciibox_lines:
    Ab dem zweiten Argument (aus args oder kwargs) wird das Präfix durch
    einen Leerstring gleicher Länge ersetzt.

    >>> list(gen_prefix('func(', 'eins', 'zwei'))
    ["func('eins'", "     'zwei'"]
    """
    first = True
    if not args and not kwargs:
        yield prefix
        return
    for a in args:
        yield '%(prefix)s%(a)r' % locals()
        if first:
            prefix = ' ' * len(prefix)
            first = False
    for k, v in kwargs.items():
        yield '%(prefix)s%(k)s=%(v)r' % locals()
        if first:
            prefix = ' ' * len(prefix)
            first = False


def gen_suffix(seq, ch=',', lastch=')'):
    """
    Hilfsfunktion für asciibox_lines:
    Füge jedem Element der übergebenen Sequenz <seq> das Suffix <ch>
    hinzu - bis auf das letzte, das <lastch> bekommt.

    >>> list(gen_suffix(['eins', 'zwei']))
    ['eins,', 'zwei)']
    """
    prev = None
    first = True
    for item in seq:
        if first:
            first = False
        else:
            yield prev + ch
        prev = item
    if not first:
        yield item + lastch


# ----------------------------------- [ asciibox_lines ... [
def asciibox_lines(label, ch, width, kwargs):
    """
    Arbeitspferd für -> asciibox; testbar.

    Das wichtigste Argument ist <label>.
    Ein einzelner String wird zentriert:
    >>> asciibox_lines('A', '*', 7, {})
    ['*******', '*     *', '*  A  *', '*     *', '*******']

    Die ersten und letzten beiden Teile sind vergleichsweise
    uninteressant, weswegen wir sie für die weiteren Tests ignorieren.

    Für Funktionsaufrufe mit unbenannten Argumenten: "foo" ist der Name
    der Funktion; "foo(" als erstes Element einer Sequenz <label> löst
    diese Interpretation aus:

    >>> asciibox_lines(['foo(', 'ein string', 123], '*', 25, {})[2:-2]
    ["*   foo('ein string',   *", '*       123)            *']

    >>> asciibox_lines(['foo(', 'foo'], '*', 20, {'bar': 'baz'})[2:-2]
    ["*  foo('foo',      *", "*      bar='baz')  *"]

    >>> asciibox_lines(['foo('], '*', 18, {'bar': 'baz'})[2:-2]
    ["* foo(bar='baz') *"]

    """
    asti = ch * width
    wid_ = width - 2
    empt = (' ' * wid_).join((ch, ch))
    liz = [asti, empt]
    if isinstance(label, six_string_types):
        assert not kwargs
        ham_ = label.strip().center(wid_).join((ch, ch))
        liz.append(ham_)
    else:
        autopar = label[0].endswith('(')
        if autopar:
            raw = list(gen_suffix(gen_prefix(label[0],
                                             *tuple(label[1:]),
                                             **kwargs)))
        else:
            assert not kwargs
            raw = list(map(str, label))
        maxl = max(list(map(len, raw)))
        filled = ['%-*s' % (maxl, s)
                  for s in raw]
        liz.extend([s.center(wid_).join((ch, ch))
                    for s in filled])
    liz.extend([empt, asti])
    return liz
# ----------------------------------- ] ... asciibox_lines ]


def join_lines(liz):
    return '\n'.join(liz)


def raw_result(res):
    return res


def asciibox(label, ch='*', width=79, kwargs={}, finish=join_lines):
    """
    Gib eine umrandete Box zurück

    label -- ein String oder eine Sequenz.
             Wenn das erste Element einer (Nicht-String-) Sequenz mit einer
             öffnenden Klammer endet, wird angenommen, daß es sich um
             einen Funktionsaufruf mit Argumenten handelt

    >x> asciibox(['foo(', 'ein string', 123], width=25)
 '''*************************
    *                       *
    *   foo('ein string',   *
    *       123)            *
    *                       *
    *************************'''

    (siehe Doctests zu asciibox_lines)
    """
    return finish(asciibox_lines(label, ch, width, kwargs))
# ---------------------------- ] ... asciibox + Hilfsfunktionen ]


def print_indented(txt, indent=0):
    r"""
    Zur eingerückten Ausgabe (vom pprint-Modul nicht unterstützt!)

    >>> print_indented('''\
    ... a
    ...   b
    ... ''', 2)
      a
        b

    """
    if isinstance(txt, six_text_type):
        prefix = u' ' * indent
    else:
        prefix = ' ' * indent
    try:
        for line in txt.splitlines():
            try:
                print(prefix + line.rstrip())
            except UnicodeEncodeError as e:
                print('*** Hoppla! %s (%r)' % (e, line.rstrip()))
    except UnicodeEncodeError as e:
        print('!!! %s' % (e, ))


def make_sleeper(logger, default=2, method='info'):
    """
    Erzeuge eine Funktion, die eine bestimmte Zeit schläft (z.B., um die
    Ausgaben des psql-Loggings besser zeitlich zuordnen zu können),
    und darüber natürlich Auskunft gibt.

    Um nach Verwendung das Aufräumen zu unterstützen, muß ein Logger
    übergeben werden, aus dessen Ausgabe üblicherweise das aufrufende
    Modul hervorgeht.
    """
    logfunc = getattr(logger, method)

    def sleepfunc(secs=default):
        logfunc('Sleeping %f seconds ...', secs)
        sleep(secs)
        logfunc('... done sleeping %f seconds.', secs)
    return sleepfunc
# ----------------------------------- ] ... aus unitracc.tools.debug ]


def _needle_tuples(haystack, needles, found, before, after):
    """
    Little helper function for has_strings; see below.

    This list is filled in-place:
    >>> found = []

    The haystack is searched for the given needles; before and after
    specify the amount of context.
    >>> haystack = 'Some haystack  which contains needles'
    >>> needles = ['  ', 'needle']

    This little helper returns nothing ...
    >>> _needle_tuples(haystack, needles, found, before=5, after=10)

    ... since the calling function will find the list filled:
    >>> found
    [(8, 13, 25, '  '), (25, 30, 46, 'needle')]
    """
    for needle in needles:
        start = 0
        needle_len = len(needle)
        found_at = haystack.find(needle, start)
        while found_at >= 0:
            found.append((max(found_at-before, 0),
                          found_at,
                          found_at+needle_len+after,
                          needle,
                          ))
            start = found_at + needle_len
            found_at = haystack.find(needle, start)


def has_strings(haystack, *needles, **kwargs):
    r"""
    Search the given text <haystack> for the given "needles"; if found anything,
    print an information (unless some other function was specified)
    and return True.

    >>> txt = 'Vitaler Nebel mit Sinn ist im Leben relativ'
    >>> liz = []
    >>> has_strings(txt, 'Nebel', 'r', before=3, after=5, head=10,
    ...             func=liz.append)
    True
    >>> liz
    ["'Vitaler Ne'...", '        v', " 6: 'aler Nebe'", " 8: 'er Nebel mit '", "36: 'en relati'"]

    This function is designed to be used in the pdb b(reak) feature:
    the optional 2nd argument is an expression which -- if evaluating to
    True -- will trigger the break; therefore, the `has_strings`
    function will either print nothing and return False, or print the
    interesting information and return True.
    """
    pop = kwargs.pop
    before = max(pop('before', 20), 0)
    after = max(pop('after', 20), 0)
    head = max(pop('head', 76), 0)
    label = pop('label', None)
    func = pop('func', print)
    other = pop('other', None)
    if isinstance(other, six_string_types):
        other = [other]

    check_kwargs(kwargs)  # raises TypeError if necessary

    found = []
    # The "needles" are our criterion to tell whether the result is interesting:
    _needle_tuples(haystack, needles, found, before=before, after=after)
    if not found:
        return False

    # If it is interesting, we might want to know more:
    if other:
        _needle_tuples(haystack, other, found, before=before, after=after)

    found.sort()
    found_max = found[-1][1]
    max_len = len(str(found_max))
    if label:
        func(label)
    shortened = haystack[:head]
    if haystack[head:]:
        func(repr(shortened)+'...')
    else:
        func(repr(shortened))
    prev_offset = None
    if isinstance(haystack, six_text_type):
        zugabe = 5  # 'u' prefix
    else:
        zugabe = 4
    for tup in found:
        start, found_at, end, needle = tup
        offset = found_at - start
        if offset and offset != prev_offset:
            func('%+*s' % (offset + max_len + zugabe, 'v'))
            prev_offset = offset
        func('%*d: %r' % (max_len, found_at, haystack[start:end]))
    return True


def make_debugfile_writer(dirname, **kwargs):
    """
    Debugging helper: write a file, taking the raw ajax-nav dictionary
    (not jsonified)

    NOTE: For this function to be generally useful, it requires some
          more love.  It was written for the returned function to take a
          dictionary with "content" (HTML text) and "@title" keys.
    """
    cnt = {'files': 0}
    pop = kwargs.pop
    datemask = pop('datemask', '%a-%H%M%S')
    dirseg = strftime(datemask)
    fulldir = path_join(dirname, dirseg)
    makedirs(fulldir)
    print('Creating files in directory %(fulldir)s'
          % locals())
    width = pop('width', 4)
    num_mask = '%%0%dd' % int(width)

    def write_file(dic):
        text = dic.get('content')
        if not text:
            print('*** No text!')
            return
        number = cnt['files'] + 1
        cnt['files'] = number
        title = dic.get('@title')
        name = num_mask % number
        if title:
            name += '--' + title
        name += '.html'
        full_name = path_join(fulldir, name)
        with open(full_name, 'wb') as f:
            f.write(text)
        print('*** %(full_name)s written' % locals())

    return write_file


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()

    def a():
        print('Funktion a ...')
        print('\n'.join(pretty_callstack()))
        print('... Funktion a')

    def b():
        print('Funktion b ...')
        a()
        print('... Funktion b')

    def c():
        print('Funktion c ...')
        b()
        print('\n'.join(pretty_callstack()))
        print('... Funktion c')

    c()
