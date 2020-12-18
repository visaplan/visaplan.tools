# -*- coding: utf-8 -*- vim: et ts=8 sw=4 sts=4 si tw=79 cc=+1
"""\
Tools useful in buildout-built projects

For now, we support to check for whitelisted package versions
(e.g. for cases when you don't want to *require* a certain package,
but if you have it, you want to be sure to have a supported (whitelisted)
version.
"""
# Python compatibility:
from __future__ import absolute_import

# Standard library:
import sys
from os.path import normpath, sep

# Local imports:
from visaplan.tools.sequences import sequence_slide

# Logging / Debugging:
from logging import getLogger

__all__ = [
    'checkPathForPackage',
    # Constants:
    'FAIL', 'WARN', 'RETURN',
    # helper functions:
    'extract_package_and_version',
    'name_and_version_from_eggname',
    'check_illegal_choice',
    # exception classes (ValueError):
    'UnsupportedVersion',
    'PackageNotFound',
    'InvalidPathEntry',
    'PackageExtractionError',
    ]


# -------------------------- [ Constants for checkPathForPackage ... [
FAIL = 'FAIL'
WARN = 'WARN'
RETURN = 'RETURN'  # return True or False
## the first is the default:
# for missing packages, raise PackageNotFound by default:
VALUES_MISSING = (FAIL, RETURN)
# if found as a development package only, by default
# warn, and always return 'devel'
VALUES_NOVERSION = (WARN, RETURN)
VALUES_MISMATCHING = (FAIL, RETURN)
VALUES_INVALID = (FAIL, WARN)
# -------------------------- ] ... Constants for checkPathForPackage ]


# ------------------------------------------ [ exception classes ... [
class InstalledPackageError(ValueError):
    def __init__(self, **kwargs):
        self._msg = self.__doc__ % kwargs

    def __str__(self):
        return self._msg


class UnsupportedVersion(InstalledPackageError):
    """\
    Found unsupported %(package)s v%(version)s; whitelisted: %(whitelist)s

    The package maintainer should inspect the support for the currently
    whitelisted package versions and update this package to support
    version %(version)s of package %(package)s as well.
    """


class PackageNotFound(InstalledPackageError):
    """\
    Package %(package)s not found in sys.path

    Probably you need to add zcml:condition to check for this package
    before you import the calling module, e.g.:

    <configure
         xmlns="http://namespaces.zope.org/zope"
         xmlns:zcml="http://namespaces.zope.org/zcml">
      <include zcml:condition="installed %(package)s
               file="..."
    </configure>
    """


class InvalidPathEntry(InstalledPackageError):
    """\
    The path %(spec)r was not recognised as a development package or egg

    We support development package and egg specifications
    (like put into sys.path by buildout)
    under the following assumptions:
    - An egg path doesn't contain any subpath below the *-py*.egg directory
    - A development package path contains no subpath either,
      or a 'src' subdirectory

    Please tell us if these assumptions need to be refined.
    """


class PackageExtractionError(InvalidPathEntry):
    """\
    Path spec %(spec)r: error extracting package and version from %(chunk)r

    Egg names are expected to contain two or more dashes ('-').
    """
# ------------------------------------------ ] ... exception classes ]


# ------------------------------------------- [ helper functions ... [
def check_illegal_choice(value, name, choices):
    if value not in choices:
        raise TypeError('%(name)s value %(value)r not allowed; '
                        'choose from %(choices)s'
                        % locals())


def name_and_version_from_eggname(name):
    """
    Extract the package name and version from the given egg name.

    >>> f = name_and_version_from_eggname
    >>> f('plone.app.locales-4.3.7-py2.7.egg')
    ('plone.app.locales', '4.3.7')

    Package names might contain dashes:
    >>> f('fancy-package-1.2.3-py2.7.egg')
    ('fancy-package', '1.2.3')

    Version suffixes are possible but are expected not to contain dashes:
    >>> f('visaplan.tools-1.2.2.dev1-py2.7.egg')
    ('visaplan.tools', '1.2.2.dev1')
    """
    if sep in name:
        raise ValueError('no path allowed! (%(name)r)' % locals())
    parts = name.split('-')
    if not parts[2:]:
        raise ValueError('%(name)r: 2 or more "-" expected' % locals())
    return ('-'.join(parts[0:-2]),
            parts[-2])


def extract_package_and_version(spec, invalid=VALUES_INVALID[0], logger=None):
    """
    Extract package name and version from an egg specification

    >>> epav = extract_package_and_version
    >>> epav('/.../eggs/visaplan.tools-1.2.2-py2.7.egg')
    ('visaplan.tools', '1.2.2')
    >>> epav('/.../eggs/mismatching.pkg-1.1-py2.7.egg')
    ('mismatching.pkg', '1.1')

    Development packages (in a src directory) are found,
    and the version is None:
    >>> epav('/.../src/development.pkg/src')
    ('development.pkg', None)

    Note: the purpose is not to extract the information from any possible
    path below the package directory  but to consider real-life buildout-made
    sys.path entries only; thus, only the first one or (if '.../src') two path
    chunks are considered!

    It turned out to be necessary to support egg specs with subpaths.
    In such cases, if the first try fails, we try the direct child of 'eggs'
    as well:
    >>> epav('/opt/zope/common/eggs/Products.ATContentTypes-2.1.14'
    ...      '-py2.7.egg/Products/ATContentTypes/thirdparty')
    ('Products.ATContentTypes', '2.1.14')
    """
    chunks = normpath(spec).split(sep)
    check_illegal_choice(invalid, 'invalid', VALUES_INVALID)
    msg = 'path entry %(spec)r is too short'
    msg = 'Unexpected path entry %(spec)r'
    dbg = 'thirdparty' in spec or True and False

    for child, chunk, parent in sequence_slide(reversed(chunks)):
        # in src directories we expect development packages
        if parent == 'src':
            return (chunk, None)
        if child is None:
            if chunk == 'src':
                continue
            if parent == 'src':  # development package
                return (chunk, None)
            try:
                package, version = name_and_version_from_eggname(chunk)
            except ValueError:
                if parent != 'eggs':
                    if logger is None:
                        logger = getLogger('extract_package_and_version')
                    logger.warn('Invalid top chunk: %(chunk)r (%(spec)r', locals())
                    # next try with parent == 'eggs'
                    continue
                if invalid == FAIL:
                    raise PackageExtractionError(**locals())
                msg = 'Unexpected egg name %(chunk)r'
                break
            else:
                return (package, version)
        elif child == 'src' and parent == 'src':
            return (chunk, None)
        elif parent == 'eggs':
            try:
                package, version = name_and_version_from_eggname(chunk)
            except ValueError:
                if invalid == FAIL:
                    raise PackageExtractionError(**locals())
                if logger is None:
                    logger = getLogger('extract_package_and_version')
                logger.warn('Invalid chunk: %(chunk)r (%(spec)r', locals())
            else:
                return (package, version)
        elif not parent:
            msg = 'Unexpected path entry %(spec)r'
            break
    if invalid == FAIL:
        raise InvalidPathEntry(spec=spec)
    if logger is None:
        logger = getLogger('extract_package_and_version')
    logger.warn(msg, locals())
    return (None, False)
# ------------------------------------------- ] ... helper functions ]


# ---------------------------------------- [ checkPathForPackage ... [
def checkPathForPackage(package, whitelist, path=None,
        missing=VALUES_MISSING[0],
        noversion=VALUES_NOVERSION[0],
        mismatching=VALUES_MISMATCHING[0],
        invalid=VALUES_INVALID[0],
        logger=None,
        extract=extract_package_and_version):
    """
    Check the path entries for the given package;
    if found, and if the found version is in the whitelist,
    return True.
    Otherwise (by default) raise an exception.

    Let's say you don't *require* some.package (so you don't put it into your
    install_requires argument), but if you have it, you need to be sure you
    have a known-good version.

    In a Zope/Plone/ZCML-configured environment, you could have:

      <configure
           xmlns="http://namespaces.zope.org/zope"
           xmlns:zcml="http://namespaces.zope.org/zcml">
        <include zcml:condition="installed some.package"
                 package=".vcheck.some_package"/>
      </configure>

    If you know the versions '1.1' and '1.2' of some.package to be good,
    your vcheck/some_package.py module could look like this:

      from visaplan.tools.buildout import checkPathForPackage
      checkPathForPackage('some.package', '1.1, 1.2')

    If your setup contains some.package in one of the given versions, this
    won't do anything visible.

    If your setup happens to contain a non-whitelisted version of some.package,
    it will raise an UnsupportedVersion exception, and you are given the choice
    whether to extend the whitelist or add a version pinning.

    Arguments:
      package     the package name
      whitelist   a comma-separated string, or list, or tuple
      path        (for testing only)

      missing     action for not installed package,
                  or if develepent package found but disallowed
      noversion   by default (WARN), for development packages
                  a warning is logged; in any case, 'devel' is returned
      mismatching by default (FAIL), an exception is raised if a
                  non-whitelisted package version is found
      invalid     action for unexpected sys.path entries, by default: FAIL
      logger      anything which sports a "warn" method
      extract     a function which takes a (buildout-created) sys.path entry
                  and returns a (package, version) tuple
                  (see extract_package_and_version for the signature)

    >>> from visaplan.tools.mock import MockLogger
    >>> logger = MockLogger()
    >>> samplepath=['/.../eggs/visaplan.tools-1.2.2-py2.7.egg',
    ...             '/.../src/development.pkg/src',
    ...             '/.../eggs/mismatching.pkg-1.1-py2.7.egg',
    ...             ]
    >>> def cpfp(package, path=samplepath, **kwargs):
    ...     return checkPathForPackage(package,
    ...         '1.0, 1.2, 1.2.2',
    ...          path=path,
    ...          logger=logger,
    ...          **kwargs)

    Looking for a package which is present, version in whitelist:
    >>> cpfp('visaplan.tools')
    True

    Looking for a package which is present, but only as an development package,
    will return 'devel', which is "True" as well, but log a warning:
    >>> cpfp('development.pkg')
    'devel'
    >>> list(logger)[-1]
    ('WARN', 'Using development package for development.pkg')
    >>> cpfp('mismatching.pkg', mismatching=RETURN)
    False

    >>> logger_offset=len(logger)
    >>> samplepath.append('/opt/zope/common/eggs/Products.ATContentTypes-2.1.14'
    ...                   '-py2.7.egg/Products/ATContentTypes/thirdparty')
    >>> cpfp('Products.ATContentTypes', path=samplepath, mismatching=RETURN)
    False
    >>> logger[logger_offset:]
    [('WARN', "Invalid top chunk: 'thirdparty' ('/opt/zope/common/eggs/Products.ATContentTypes-2.1.14-py2.7.egg/Products/ATContentTypes/thirdparty'")]

    If a package cannot be found, all bogus path entries will be logged:
    >>> samplepath.append('/complete/nonsense')
    >>> cpfp('missing.package', path=samplepath, missing=RETURN)
    False
    >>> logger[-1:]
    [('WARN', 'Invalid entry: /complete/nonsense')]

    In our example above, there is no such message for Products.ATContentTypes
    because in the end the package and version had been found:
    >>> not [(lvl, txt)
    ...      for (lvl, txt) in logger
    ...      if txt.startswith('Invalid entry')
    ...      and 'ATContentTypes' in txt
    ...      ]
    True
    """
    if path is None:
        path = sys.path
    if not isinstance(whitelist, (list, tuple)):
        whitelist = [v.strip()
                     for v in whitelist.split(',')
                     ]
    check_illegal_choice(missing,     'missing',     VALUES_MISSING)
    check_illegal_choice(noversion,   'noversion',   VALUES_NOVERSION)
    check_illegal_choice(mismatching, 'mismatching', VALUES_MISMATCHING)
    bogus_paths = []
    for pa in path:
        try:
            p, version = extract(pa, invalid=invalid, logger=logger)
            if p == package:
                if version in whitelist:
                    return True
                if version is None:
                    if noversion == WARN:
                        if logger is None:
                            logger = getLogger('checkPathForPackage')
                        logger.warn('Using development package for %(package)s',
                                    locals())
                    return 'devel'
                elif mismatching == FAIL:
                    raise UnsupportedVersion(**locals())
                else:
                    return False
        except InvalidPathEntry as e:
            bogus_paths.append(pa)
    del p, v
    if bogus_paths:
        if logger is None:
            logger = getLogger('checkPathForPackage')
        logger.warn('Found %d invalid path entries:', len(bogus_paths))
        for pa in bogus_paths:
            logger.warn('Invalid entry: %(pa)s', locals())
    if missing == FAIL:
        raise PackageNotFound(**locals())
    return False
# ---------------------------------------- ] ... checkPathForPackage ]


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
