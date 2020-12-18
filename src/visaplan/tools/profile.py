# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Mini-Profiler als Kontextmanager

Verwendung:
    with StopWatch(Beschreibungstext) as stopwatch:
        ...
        stopwatch.lap(Text)
        ...
        stopwatch.lap(Text)
        ...

Es wird beim Betreten des Kontexts, beim Verlassen und (optional, wenn
zugewiesen mit "as") bei jedem Aufruf der lap-Methode ein Text ausgegeben bzw.
protokolliert.

Die Stoppuhr kann mit dem Argument enable (Standardwert True) vom aktivierten
Debugging abhängig gemacht werden; in diesem Fall erfolgen keinerlei Ausgaben.
Am performantesten ist aber natürlich, nicht mehr gebrauchte Stopwatch-Kontexte
wieder zu entfernen.

Diesem Zweck dient der Meta-Dekorator "profile", der mit einem Boolean-Argument
verwendet wird:

    @profile(debug_active)
    def eine_funktion(arg):
        ...

Wenn debug_active logisch True ist, wird die Funktion "eine_funktion" stets in
einem StopWatch-Kontext ausgeführt; andernfalls wird sie (ohne weitere
Performanz-Einbußen) unverändert zurückgegeben.  In diesem Fall sind natürlich
keine weiteren stopwatch.lap-Aufrufe möglich.

Siehe auch .cfg.get_debug_active, .log.getLogSupport
"""
# Python compatibility:
from __future__ import absolute_import, print_function

# Standard library:
from functools import wraps
from time import time

# Local imports:
from visaplan.tools.classes import Proxy

# Daten:
#                      Label   Text
#                           Sekunden
LAP_MASK = 'StopWatch (%s): %f %s'
DEFAULT_LOGGER_METHOD = 'info'

def prefixed_mask(spaces):
    return ' ' * spaces + LAP_MASK

PREFIXED_MASK = Proxy(prefixed_mask)
NESTING_DEPTH = 0
NESTING_DELTA = 2


class StopWatch(object):
    def __init__(self, txt, enable=True, **kwargs):
        """
        txt - Bezeichnung des Mini-Profilers, z. B. ein Methodenname

        Schlüsselwortoptionen: optional eine aus ...

        method - eine Methode eines Loggers, z.B. logger.info
        logger - ein Logger; die Methode info wird verwendet.

        Wenn keins dieser Argumente angegeben wird, wird zur Standardausgabe
        geschrieben.
        """
        self._disabled = not enable
        if self._disabled:
            self.method = self.do_nothing
            return
        mapping = kwargs.pop('mapping', None)
        if mapping is None:
            if '%' in txt:
                raise ValueError('%% im Text ist nicht erlaubt! (%r)'
                                 % (txt,
                                    ))
            self.txt = txt
        else:
            self.txt = txt % mapping
        logger = kwargs.pop('logger', None)
        method = kwargs.pop('method', None)
        if logger is None:
            if method is None:
                self.method = self._to_stdout
            else:
                self.method = method
        else:
            if method is None:
                method = DEFAULT_LOGGER_METHOD
            self.method = getattr(logger, method)

    def __enter__(self):
        if self._disabled:
            return self
        global NESTING_DEPTH
        self._nesting = NESTING_DEPTH
        start = self._start = time()
        self._last = [start]

        self.method('%sStopWatch (%s): START [  %f [',
                    ' ' * self._nesting,
                    self.txt, start)
        NESTING_DEPTH += NESTING_DELTA
        return self

    def _to_stdout(self, txt, *args):
        """
        Mini-Logger-Methode
        """
        print(txt % args)

    def __repr__(self):
        return '<%s.%s(%r)>' % (
            self.__module__,
            self.__class__.__name__,
            self.txt,
            )

    def lap(self, txt, delta=None):
        if self._disabled:
            return
        now = time()
        if delta is None:
            delta = now - self._last[-1]
        self._last.append(now)
        self.method(PREFIXED_MASK[self._nesting],
                    self.txt, delta, txt)

    def do_nothing(self, *args):
        return

    def __exit__(self, exc_type, exc_value, traceback):
        if self._disabled:
            return
        global NESTING_DEPTH
        NESTING_DEPTH -= NESTING_DELTA
        now = time()
        if self._last[1:]:
            delta = now - self._last[-1]
            if delta:
                self.lap('(last delta)')
        self.lap('(overall time)', now - self._start)
        self.method('%sStopWatch (%s):   END  ] %f  ]',
                    ' ' * self._nesting,
                    self.txt, now)

def profile(active, logger=None):
    """
    Meta-Dekorator: Wenn <active> True ist, gib eine Funktion zurück, die die
    übergebene Funktion in einen StopWatch-Kontext packt;
    andernfalls wird die dekorierte Funktion direkt zurückgegeben.
    """
    def dummy(func):
        return func
    def decorate_with_stopwatch(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with StopWatch(func.__name__, logger=logger):
                return func(*args, **kwargs)
        return wrapper
    if active:
        return decorate_with_stopwatch
    return dummy
