# -*- coding: utf-8 -*- äöü vim: sw=4 sts=4 si et textwidth=72 cc=+8
"""
visaplan.tools.debug - Helferlein für Entwicklung und Debugging

Autor: Tobias Herp
"""
# ACHTUNG - Importe aus dem unitracc-Produkt stets incl. des
# Products-Kontexts vornehmen, also
#   "from Products.unitracc.tools.ModulXY import ..."
# anstelle von
#   "from unitracc.tools.ModulXY import ..." --
# ansonsten können Probleme mit dem Pickle-Storage etc. auftreten!

__all__ = [
           # ----------------------- [ aus unitracc.tools.debug2 ... [
           'pp',
           'log_or_trace',
           # ----------------------- ] ... aus unitracc.tools.debug2 ]
           # ------------------------ [ aus unitracc.tools.debug ... [
           'arginfo',
           'pretty_funcname',
           # ------------------------ ] ... aus unitracc.tools.debug ]
           ]


# Standardmodule:
from functools import wraps
from pprint import pformat, pprint
from traceback import extract_stack
from collections import defaultdict

try:
    from visaplan.plone.tools.log import getLogSupport
except ImportError:
    getLogSupport = None
from visaplan.tools.minifuncs import gimme_False

# ------------------------------------------------------ [ Daten ... [
_TRACE_SWITCH = defaultdict(gimme_False)
# ------------------------------------------------------ ] ... Daten ]


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
            def trace_on(key=trace_key):
                globals()['_TRACE_SWITCH'][key] = True

            def trace_off(key=trace_key):
                globals()['_TRACE_SWITCH'][key] = False
            globals()['_TRACE_SWITCH'][trace_key] = trace
            from pdb import set_trace

            inner1 = func

            @wraps(func)
            def switched_tracer(*args, **kw):
                if globals()['_TRACE_SWITCH'][trace_key]:
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

# ----------------------------------- [ aus unitracc.tools.debug ... [
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
# ----------------------------------- ] ... aus unitracc.tools.debug ]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
