#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79

# Python compatibility:
from __future__ import absolute_import

from six.moves.urllib.parse import urlsplit, urlunsplit

import pkg_resources

try:
    pkg_resources.get_distribution('zope.deprecation')
except pkg_resources.DistributionNotFound:
    if __name__ != '__main__':
        raise
    HAS_ZOPEDEPRECATION = False
    print('*** zope.deprecation not installed!')
else:
    HAS_ZOPEDEPRECATION = True
    from zope.deprecation import deprecated
    deprecated(
        'http_statustext',
        'The optional func argument is pretty fishy; '
        'with modern Python versions the function shouldn\'t be necessary '
        'anyway.'
        '\nWill be removed in release 1.5.0.')
    deprecated(
        'make_url',
        'The function doesn\'t satisfy the promise suggested by the name;'
        '\nwill be removed in release 1.5.0.')

try:
    # Python compatibility:
    from six.moves.http_client import responses as http_responses
except ImportError:
    # Mapping status codes to official W3C names
    http_responses = {
        100: 'Continue',
        101: 'Switching Protocols',

        200: 'OK',
        201: 'Created',
        202: 'Accepted',
        203: 'Non-Authoritative Information',
        204: 'No Content',
        205: 'Reset Content',
        206: 'Partial Content',

        300: 'Multiple Choices',
        301: 'Moved Permanently',
        302: 'Found',
        303: 'See Other',
        304: 'Not Modified',
        305: 'Use Proxy',
        306: '(Unused)',
        307: 'Temporary Redirect',

        400: 'Bad Request',
        401: 'Unauthorized',
        402: 'Payment Required',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        407: 'Proxy Authentication Required',
        408: 'Request Timeout',
        409: 'Conflict',
        410: 'Gone',
        411: 'Length Required',
        412: 'Precondition Failed',
        413: 'Request Entity Too Large',
        414: 'Request-URI Too Long',
        415: 'Unsupported Media Type',
        416: 'Requested Range Not Satisfiable',
        417: 'Expectation Failed',

        500: 'Internal Server Error',
        501: 'Not Implemented',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
        505: 'HTTP Version Not Supported',
    }

__all__ = [
    'extract_hostname',  # forgiving hostname extractor for invalid URLs
    # deprecated:
    'http_statustext',  # accepts a questionable func option
    'make_url',  # amend the 'http:' scheme if none is contained
    ]


def http_statustext(code, func=None):
    """
    code -- der numerische Statuscode (eine ganze Zahl)
    func -- Fehlerbehandlungsfunktion. Wenn None (die Vorgabe), wird im
            Fehlerfall ein KeyError geworfen
    """
    try:
        return http_responses[code]
    except KeyError:
        if func is None:
            raise
        func('Unbekannter HTTP-Statuscode: %r', code)
        return 'Unknown HTTP status %r' % (code, )


def make_url(s):
    """
    Ergänze http://, wenn kein Protokollschema angegeben

    >>> make_url('www.unitracc.de')
    'http://www.unitracc.de'
    >>> make_url('//www.unitracc.de')
    'http://www.unitracc.de'
    >>> make_url('http://www.unitracc.de')
    'http://www.unitracc.de'
    >>> make_url('https://www.unitracc.de')
    'https://www.unitracc.de'
    """
    # in diesem Fall schlägt urlsplit den nackten Hostnamen
    # der Pfadkomponente zu (und läßt den Hostnamen leer):
    if '/' not in s and ':' not in s:
        return 'http://' + s
    info = urlsplit(s)
    liz = list(info)
    if info.netloc and not info.scheme:
        liz[0] = 'http'
        return urlunsplit(liz)
    # Wenn das Ergebnis jetzt noch ungültig ist,
    # wird es eben beim Test auffallen ...
    return s


def extract_hostname(url):
    """
    Extrahiere den Hostnamen, z. B. für die Ermittlung des Subportals.
    urlsplit liefert manchmal ein suboptimales Ergebnis:

    >>> url='http://aqwa-academy.net:/Pfad/zur/Datei'
    >>> urlsplit(url).netloc
    'aqwa-academy.net:'
    >>> extract_hostname(url)
    'aqwa-academy.net'

    Das klappt auch für nicht-verhunzte URLs:

    >>> extract_hostname('http://unitracc.de/akademie')
    'unitracc.de'

    Hostnamen ohne Protokoll:
    >>> extract_hostname('betonquali.de')
    'betonquali.de'

    Wenn kein Hostname enthalten ist, knallt's:
    >>> extract_hostname('/akademie')
    Traceback (most recent call last):
        ...
    ValueError: '/akademie' doesn't contain a hostname
    """
    try:
        return url.split(':')[1].split('/')[2]
    except IndexError:
        # kein : enthalten:
        hostname =  url.split('/')[0]
        if hostname:
            return hostname
        raise ValueError('%(url)r doesn\'t contain a hostname'
                         % locals())


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
