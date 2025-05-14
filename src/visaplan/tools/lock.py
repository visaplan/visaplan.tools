# -*- coding: utf-8 -*- vim: set tw=78 cc=+1: ------------ [ skip docstring: [
"""
visaplan.tools.lock: Some sugar for zc.lockfile.LockFile

We depend on zc.lockfile in this module;
since you might not need it, we don't actually require that package in our metadata.

We add some sugar to the zc.lockfile.LockFile class, e.g. a context manager::

  form zc.lockfile import LockError
  from visaplan.tools.lock import ConvenientLock

  lfn = '/var/lock/perfectly-normal.lock'
  try:
      with ConvenientLock(lfn):
          # do what you need to do ...
  except LockError as e:
      # by default, we won't catch that error

When leaving the context, we try to delete the lock file by default;
specify autodelete=False to prevent this.
We'll ignore any OSError which may occur during deletion, however;
if verbose (requires a logger to be specified), this will be logged.

Further remarks:

- The property ``filename`` provides the name used internally to create the
  zc.lockfile.LockFile;
- The property ``lockfile`` (not to be confused with the former) provides
  that very LockFile object.
- There is an ``acquire`` method you may use to get the lock,
  although the usual way will be to simply `__enter__` the context;
- there is a companion ``release`` method
  which is normally called by the ``__exit__`` method.

"""  # -------------------------------------------------- ] module docstring ]
# reintegrated changes from visaplan.plone.tomoodle:
# - for Python 3.8+, use importlib.metadata
# - check_lockfile_options -> LockfileOptions,
#   including call to lockfile_kwargs
# - new property ConvenientLock.logger
# - range comments for top-level utility functions
# - "TOC entries" documented
# TODO:
# - remove _env option?
# - support alternative argument names, e.g. 'lockfile_name' instead of 'name'

# Python compatibility:
from __future__ import absolute_import, print_function

from sys import version_info
if version_info[:2] >= (3, 8):
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as pkg_version
else:
    from importlib_metadata import PackageNotFoundError
    from importlib_metadata import version as pkg_version

# Setup tools:
from packaging.version import parse as parse_version

# Standard library:
from collections import namedtuple
import logging
from os import unlink
from os import makedirs
from os.path import sep, normpath, isdir, abspath, join, dirname
from time import sleep

try:
    ZCLF_V = parse_version(pkg_version('zc.lockfile'))
except PackageNotFoundError:
    if __name__ == '__main__':
        ZCLF_V = parse_version('1.2.3.post4')
        print("Package zc.lockfile not found; some tests probably won't work!")
        class LockFile: pass
        class LockError(Exception): pass
    else:
        raise
else:
    # Zope:
    from zc.lockfile import LockError, LockFile

__all__ = [
    'ConvenientLock',  # our wrapper class, a context manager
    'check_lockfile_options',  # initialisation helper, returning a:
    'LockfileOptions',  # namedtuple for internal use
    'lockfile_kwargs',  # build keyword args for zc.lockfile.LockFile creation
    ]

HAVE_CUSTOMCONTENT = ZCLF_V >= parse_version('1.2.0')  # 1.2.1+ recommended!
DEFAULTS_KW = {
    'add_pid': True,
    'add_hostname': False,
    'content_template': None,
    'sep': ';',
    # for testability:
    '_zclf_v': None,  # inject a zc.lockfile version string
    '_env': None,     # inject an environment
    # see the respective lock module in visaplan.plone.tools:
    # 'add_worker': False,
    }


LockfileOptions = namedtuple('LockfileOptions',
                             ['name',
                              'mkdir',      # informational / for tests only
                              'tries',
                              'delay',
                              'autodelete',
                              'logger',
                              'verbose',
                              'zclf_kw',    # for zc.lockfile
                              'testonly'])

def check_lockfile_options(name=None, *,  # -------------- { skip docstring: [
        dest_dir=None,
        tries=1,
        delay=None,  # required for tries > 1
        autodelete=True,
        verbose=None,
        logger=None,  # required for verbose >= 1
        strict=False,
        doctest_only=False,
        **kwargs):
    """
    Testable options evaluation for ConvenientLock

    This includes creation of a directory, if necessary; for testablity, we
    inject a special keyword argument:
    >>> def clo(*args, doctest_only=True, **kwargs):
    ...     return check_lockfile_options(*args, doctest_only=doctest_only,
    ...                                   **kwargs)

    We don't need to specify anything:
    >>> clo()                                 # doctest: +NORMALIZE_WHITESPACE
    LockfileOptions(name='.LOCK', mkdir=False,
                    tries=1,
                    delay=None,
                    autodelete=True,
                    logger=None,
                    verbose=0,
                    zclf_kw={}, testonly=True)
    >>> clo('my.lock')                        # doctest: +NORMALIZE_WHITESPACE
    LockfileOptions(name='my.lock', mkdir=False,
                    tries=1,
                    delay=None,
                    autodelete=True,
                    logger=None,
                    verbose=0,
                    zclf_kw={}, testonly=True)
    >>> clo(dest_dir='some/dir')              # doctest: +NORMALIZE_WHITESPACE
    LockfileOptions(name='some/dir/.LOCK', mkdir=True,
                    tries=1,
                    delay=None,
                    autodelete=True,
                    logger=None,
                    verbose=0,
                    zclf_kw={},
                    testonly=True)
    >>> clo('your.lock', dest_dir='some/dir')
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    LockfileOptions(name='some/dir/your.lock', mkdir=True,
                    tries=1,
                    delay=None,
                    autodelete=True,
                    logger=None,
                    verbose=0,
                    zclf_kw={},
                    testonly=True)

    Unknown arguments are ignored:
    >>> clo('my.lock', tellme=42)             # doctest: +NORMALIZE_WHITESPACE
    LockfileOptions(name='my.lock',
                    mkdir=False,
                    tries=1,
                    delay=None,
                    autodelete=True,
                    logger=None,
                    verbose=0,
                    zclf_kw={},
                    testonly=True)

    ... unless we choose to be strict:
    >>> clo('my.lock', bogus=43, strict=True)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
      ...
    TypeError: Invalid argument: 'bogus' <class 'int'>

    Now for some special functionality.
    We might want to tell the zc.lockfile module to add_hostname information:
    >>> clo(add_hostname=True)                            # doctest: +ELLIPSIS
    LockfileOptions(... zclf_kw={'content_template': '{pid};{hostname}'}, ...)
    >>> clo(add_hostname=True, sep='|')                   # doctest: +ELLIPSIS
    LockfileOptions(... zclf_kw={'content_template': '{pid}|{hostname}'}, ...)

    If we have a preconstructed content_template, we'll refuse to build it
    again:
    >>> clo(content_template='{pid}|{hostname}', sep='|') # doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    TypeError: With content_template given, no other arguments are allowed!

    Other arguments are possible, of course:
    >>> clo(content_template='{pid}|{hostname}',
    ...     delay=0.5, tries=3, autodelete=False)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    LockfileOptions(name='.LOCK',
                    mkdir=False,
                    tries=3,
                    delay=0.5,
                    autodelete=False,
                    logger=None,
                    verbose=0,
                    zclf_kw={'content_template': '{pid}|{hostname}'},
                    testonly=True)

    NOTE: for pretty ancient zc.lockfile versions, the zclf_kw attribute might
    be always empty; see the lockfile_kwargs doctests below.

    There is currently no default logger:
    >>> clo(verbose=1)
    Traceback (most recent call last):
      ...
    TypeError: Can't be verbose with no logger given!

    For multiple tries, you need to specify a delay:

    >>> clo(tries=3)
    Traceback (most recent call last):
      ...
    TypeError: with tries > 1 (3), please specify a delay [seconds]!
    >>> clo(tries=3, delay='3.0')
    Traceback (most recent call last):
      ...
    ValueError: delay must be a number; found <class 'str'>
    >>> clo(tries=3, delay=-1)
    Traceback (most recent call last):
      ...
    ValueError: delay [seconds] > 0 expected; found -1!

    """  # -------------------------------- ] ... check_lockfile_options ... [
    if dest_dir is None:
        if name is None:
            name = '.LOCK'
            mkdir = False
        else:
            name = normpath(name)
            if doctest_only:
                mkdir = sep in name
            elif isdir(name):
                mkdir = False
                name = join(name, '.LOCK')
            elif sep in name:
                mkdir = kwargs.get('mkdir', True)
                dest_dir = dirname(name)
            else:
                mkdir = False
    else:
        if name is None:
            name = '.LOCK'
        name = normpath(join(dest_dir, name))
        mkdir = kwargs.get('mkdir', True)
    if mkdir:
        assert dest_dir, (f'with mkdir={mkdir}, '
                          f'we need a dest_dir! ({dest_dir!r})!')
        if not doctest_only and not isdir(dest_dir):
            makedirs(dest_dir)
    if not isinstance(tries, int):
        raise ValueError(f'tries must be an int; found {type(tries)}')
    elif tries < 1:
        raise ValueError(f'tries must be >= 1 ({tries!r})')
    elif tries > 1:
        if delay is None:
            raise TypeError(f'with tries > 1 ({tries}), please specify '
                            'a delay [seconds]!')
        if not isinstance(delay, (int, float)):
            raise ValueError(f'delay must be a number; found {type(delay)}')
        elif delay <= 0:
            raise ValueError(f'delay [seconds] > 0 expected; found {delay}!')
    else:
        delay = None

    if verbose is None:
        verbose = (1 if logger is not None
                   else 0)
    elif not isinstance(verbose, (bool, int)):
        raise TypeError(f'verbose must be a bool or int; found {type(verbose)}')
    if verbose and not logger:
        raise TypeError("Can't be verbose with no logger given!")

    lkw = {}
    for key, val in kwargs.items():
        if key in DEFAULTS_KW:
            lkw[key] = val
        elif strict:
            raise TypeError(f'Invalid argument: {key!r} {type(val)}')

    return LockfileOptions(name, mkdir,
                    tries, delay,
                    autodelete,
                    logger, verbose,
                    lockfile_kwargs(**lkw),
                    doctest_only)
    # ----------------------------------------- ] ... check_lockfile_options ]


def lockfile_kwargs(_zclf_v=None,  # --------------------- [ skip docstring: [
                    _env=None,
                    **kwargs):
    """
    Forge keyword arguments for zc.lockfile.LockFile;
    the first argument `name`, however, we expect to be specified positionally.

    This function is used internally by check_lockfile_options (above),
    which in turn is used by our ConvenientLock initialisation.

    Let's assume we have a recent zc.lockfile release,
    and we want the hostname to be included in the lockfile contents:

    >>> def lfkw_recent(**kw):
    ...     _zclf_v = parse_version('3.0.post1')
    ...     return lockfile_kwargs(_zclf_v, **kw)
    >>> lfkw_recent(add_hostname=1)
    {'content_template': '{pid};{hostname}'}

    If we have a pre-1.2.0 version, as pinned for Plone 4.3 versions by
    default, the content_template argument is not supported yet,
    so we'll get an empty dict:

    >>> def lfkw_ancient(**kw):
    ...     _zclf_v = parse_version('1.0.2')
    ...     return lockfile_kwargs(_zclf_v, **kw)
    >>> lfkw_ancient(add_hostname=1)
    {}

    In our Zope/Plone instances, we are sometimes interested in the "worker"
    (or part, in zc.buildout terms)
    which does certain things. We could look for the PID, of course,
    but the worker's name is much more "human readable";
    and since we just need to detect it once for each process ...

    If you'd like to have that worker's name automatically written into the
    lock file, you may use the respective module of the visaplan.plone.tools
    package instead.

    Now for some corner cases.

    Arguments for the ConvenientLock class are not accepted here:
    >>> lfkw_recent(autodelete=1)
    Traceback (most recent call last):
      ...
    TypeError: Unsupported arguments {'autodelete'}!

    If the content_template is readily specified, we don't accept additional
    arguments, to avoid possible ambiguities.
    To avoid surprises, we fail for errors even if the zc.lockfile version
    doesn't support customized ocntent yet anyway:

    >>> lfkw_ancient(add_hostname=1, content_template='{pid}')
    Traceback (most recent call last):
      ...
    TypeError: With content_template given, no other arguments are allowed!

    """  # --------------------------------------- ] ... lockfile_kwargs ... [
    pop = kwargs.pop
    if _zclf_v is None:
        _zclf_v = ZCLF_V
    have_customcontent = _zclf_v > parse_version('1.2.0')

    _ct = pop('content_template', None)
    if _ct is not None:
        if kwargs:
            raise TypeError('With content_template given, no other arguments '
                            'are allowed!')
        elif have_customcontent:
            return {'content_template': _ct}
        else:
            return {}
    sep = pop('sep', ';')  # separates not dirs but content_template entries!
    added = [key[4:] for key in DEFAULTS_KW.keys()
             if key.startswith('add_') and pop(key, DEFAULTS_KW[key])
             ]
    if kwargs:
        raise TypeError(f'Unsupported arguments {set(kwargs)}!')
    if added == ['pid'] or not have_customcontent:
        # this is the default:
        return {}
    res = [key.join('{}') for key in ['pid', 'hostname']
           if key in added]
    return {'content_template': sep.join(res)}
    # ------------------------------------------------ ] ... lockfile_kwargs ]


class ConvenientLock(object):
    """
    A convenience wrapper for zc.lockfile.LockFile
    """

    def __init__(self, name=None, **kwargs):
        self._opts = opts = check_lockfile_options(name, **kwargs)
        self.__logger = opts.logger
        self.__lockfile = None

    def __enter__(self):
        if not self.active:
            self.acquire()

    def acquire(self):
        i = 1
        opts = self._opts
        while True:
            try:
                self.__lockfile = LockFile(self.filename, **opts.zclf_kw)
            except LockError as e:
                verbose = opts.verbose
                if verbose:
                    msg = str(e)
                if i < opts.tries:
                    i += 1
                    delay = opts.delay
                    if verbose:
                        # (verified syntax:)
                        self.logger.warn('%s: sleep %f seconds, then retry ...',
                                         msg, delay)
                    sleep(delay)
                else:
                    if verbose:
                        self.logger.error(msg)
                    raise
            else:
                if opts.verbose >= 2:
                    self.logger.info('Acquired lock: %r', self)
                break

    def __repr__(self):
        return "<%s('%s'): %s>" % (
                self.__class__.__name__,
                self._opts.name,
                self.status,
                )

    @property
    def status(self):
        if self.active:
            return 'ACTIVE'
        elif self.__lockfile is None:
            return 'UNINITIALIZED'
        else:
            fp = self.__lockfile._fp
            if fp is None:
                return 'CLOSED'
            elif fp.closed:
                return 'closed'
            else:
                return '???'

    @property
    def lockfile(self):
        """
        This is the zc.lockfile.LockFile instance which we use internally
        """
        return self.__lockfile

    @property
    def filename(self):
        """
        This is the filename used to create the zc.lockfile.LockFile instance
        """
        return self._opts.name

    @property
    def logger(self):
        _lf = self.__logger
        if isinstance(_lf, str):
            _self.__logger = _lf = logging.getLogger(_lf)
        return _lf

    @property
    def active(self):
        _lf = self.__lockfile
        if _lf is None:
            return False
        _fp = _lf._fp
        if _fp is None:
            return False
        return not _fp.closed

    def release(self):
        if self.active:
            self.__lockfile.close()
        verbose = self._opts.verbose
        if self._opts.autodelete:
            filename = self._opts.name
            try:
                unlink(filename)
            except OSError as e:
                if verbose:
                    self.logger.warn("LockFile %(filename)r NOT deleted!",
                                     locals())
            else:
                if verbose >= 2:
                    self.logger.info('Lockfile %(filename)r deleted!',
                                     locals())
        elif verbose >= 2:
            self.logger.info('Lockfile %r left behind.', self._opts.name)
        if verbose >= 3:
            self.logger.info('Left context of %r', self)

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()


if __name__ == '__main__':
    # Standard library:
    import doctest
    doctest.testmod()
