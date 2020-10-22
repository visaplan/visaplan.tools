# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Dateisystem-Tools für Unitracc
"""
# Python compatibility:
from __future__ import absolute_import

from six import string_types as six_string_types
from six.moves import map

__author__ = "Tobias Herp <tobias.herp@visaplan.com>"
VERSION = (0,
           2,  # id_of, now --> visaplan.plone.tools.functions
           )
__version__ = '.'.join(map(str, VERSION))


# Standard library:
from glob import glob
from os import makedirs
from os.path import (
    abspath,
    dirname,
    exists,
    getmtime,
    isdir,
    isfile,
    split,
    splitext,
    )


# für Testbarkeit:
class Silent(object):
    def info(self, *args, **kwargs):
        pass
    debug = error = info

# import is expected to fail;
# no location for .log module yet:
try:
    # Local imports:
    from .log import getLogSupport
except (ImportError, ValueError):
    if 0 and __name__ != '__main__':
        raise
    logger = Silent()
    DEBUG = logger.debug
else:
    logger, debug_active, DEBUG = getLogSupport()

# ---------------------------------- [ Daten ... [
default_fs_mode = 0o770
default_makemissingdirs = True
default_gently = True
default_deletesiblings = False
default_spareextlist = ['.txt']
# ---------------------------------- ] ... Daten ]


def make_mtime_checker(logger=logger,
                       **kwargs):
    """
    Erzeugt eine Funktion, die die Änderungszeit (als simplen Unix-Timestamp,
    also numerisch) der übergebenen Datei zurückgibt, sofern diese existiert;
    andernfalls hängt das Verhalten von <gently> ab.

    Außerdem unterstützt werden folgende "Seiteneffekte":

    - Erzeugen des Verzeichnisses, sofern es fehlt
      (üblicherweise soll eine etwa noch fehlende Datei dort angelegt werden)
    - Löschen von "Schwesterdateien"
      (z. B., weil eine Datei abc123.png einen Vorgänger abc123.gif ersetzen
      könnte; Vorgabe: False), mit der Möglichkeit der selektiven "Verschonung"

    Optionen:

    logger -- wenn nicht übergeben, wird der lokale Logger des Moduls verwendet

    Die weitere müssen benannt übergeben werden:

    gently -- wenn True (Vorgabe), wird für fehlende Dateien None zurückgegeben
    makemissingdirs -- wenn True (Vorgabe), wird für fehlende Dateien
                       die Existenz des Verzeichnisses sichergestellt
    mode -- der numerische Dateisystem-Modus, üblicherweise als Oktalzahl
            angegeben
    deletesiblings -- Sollen "Schwesterdateien" der übergebenen Datei gelöscht
                      werden? (Vorgabe: False)
    spareextlist -- Liste von Erweiterungen zu verschonender "Schwesterdateien"

    verbose -- wenn 1 (Vorgabe), werden Löschvorgänge protokolliert;
               höhere Werte informieren auch über verschonte Dateien.
               Fehler werden generell protokolliert.
    """
    if not kwargs:
        gently = True
        mode = default_fs_mode
    else:
        if 'mode' in kwargs:
            mode = kwargs.pop('mode')
            gently = kwargs.pop('gently', bool(mode))
        else:
            mode = default_fs_mode
            gently = kwargs.pop('gently', None)
    makemissingdirs = kwargs.pop('makemissingdirs',
                                 default_makemissingdirs)
    if gently is None:
        if makemissingdirs:
            gently = True
        else:
            gently = default_gently
    deletesiblings = kwargs.pop('deletesiblings', default_deletesiblings)
    if deletesiblings:
        splitfunc = kwargs.pop('splitfunc', splitext)
        siblingsuffix = kwargs.pop('siblingsuffix', '.*')
        # zu verschonende Datei-Erweiterungen:
        spareextlist = kwargs.pop('spareextlist', default_spareextlist)
        spareext = set()
        if spareextlist:
            if isinstance(sparextlist, six_string_types):
                spareextlist = [spareextlist]
            for ext in spareextlist:
                if ext:
                    ext = normcase(ext)
                    if not ext.startwith('.'):
                        ext = '.'+ext
                    spareext.add(ext)
    verbose = kwargs.pop('verbose', 1)

    def get_mtime(filename):
        try:
            if isfile(filename):
                mt = getmtime(filename)
                if verbose >= 2:
                    logger.info('File %(filename)s found', locals())
            else:
                mt = None
                if verbose >= 2:
                    logger.info('File %(filename)s not yet found', locals())
        except OSError as ose:
            mt = None

        if makemissingdirs or deletesiblings:
            dn = dirname(filename)
            if dn:
                dirfound = isdir(dn)
            else:
                dirfound = None
        if makemissingdirs and dn and not dirfound:
            if verbose:
                logger.info('making dirs %(dn)r', locals())
            makedirs(dn, mode)
        if deletesiblings and (dirfound or not dn):
            mask, myext = splitfunc(filename)
            mask += siblingsuffix
            for fn in glob(mask):
                if fn == filename:
                    if verbose >= 3:
                        logger.info("Won't delete target file %(fn)r",
                                    locals())
                    continue
                stem, ext = splitfunc(fn)
                if normcase(ext) in spareext:
                    if verbose >= 2:
                        logger.info('File %(fn)r has spared extension %(ext)r',
                                    locals())
                    continue
                try:
                    remove(fn)
                except OSError as e:
                    logger.error('File %(fn)r not deleted (%(e)r)',
                                 locals())
                else:
                    if verbose:
                        logger.info('File %(fn)r deleted', locals())

        if mt is not None:
            return mt
        elif gently:
            return None
        else:
            raise ose

    return get_mtime


if __name__ == '__main__':  # currently no useful doctests
    # Standard library:
    import doctest
    doctest.testmod()
