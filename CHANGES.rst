Changelog
=========


1.3 (unreleased)
----------------

- Breaking changes:

  - Signature change (e.g. name of first argument: ``form`` --> ``dic``) for
    ``dicts.update_dict``.


1.2.6 (unreleased)
------------------

Improvements:

- Travis CI integration added.
- Test discovery configuration for nose2 (used on Travis) and nose.

Bugfixes:

- Fixed doctests for

  - ``.dicts.update_dict``
  - ``.dicts.make_key_injector``

- Removed now-obsolete ...tests/test_doctests.py file which caused ``nosetests`` to fail.

New Features:

- ``.times.make_defaulttime_calculator``: new keyword-only option ``utc=False``,
  to make the doctests work with Travis.

[tobiasherp]


1.2.5 (2019-10-16)
------------------

- New class ``classes.AliasDict``

- Added some doctests.

[tobiasherp]


1.2.4 (2019-05-09)
------------------

- New function ``dicts.update_dict`` (from v1.2.3) "published" in ``__all__`` list.
  We are not happy with the signature of this function, though, so it will likely change
  in a future release.

- New function ``classes.connected_dicts`` which creates two connected
  dictionaries with ``dic1[key] = val`` <--> ``dict2[val] = key``

- ``log_or_trace`` will print a useful info, containing the ``trace_key``,
  before calling ``set_trace()``

[tobiasherp]


1.2.3 (2019-01-30)
------------------

- new function ``update_dict`` in ``dicts`` module
  (which takes a ``deletions`` list argument)

- ``buildout.extract_package_and_version`` supports egg specs with
  subpaths as well (child of an ``/eggs/`` directory)

- ``buildout.checkPathForPackage`` logs the invalid package entries
  if the package in question could not be found

- ``lands0.groupstring`` supports ``cumulate`` option (default: False)
  [tobiasherp]


1.2.2 (2018-11-08)
------------------

- new module ``buildout`` for use in buildout-built projects:
  use the ``checkPathForPackage`` function to check an installed package
  against a versions whitelist
  [tobiasherp]


1.2.1 (2018-09-17)
------------------

- new module ``dates``:

  - ``make_date_parser`` factory to create a ``parse_date`` function
    which understands multiple date formats

  - ``make_date_formatter`` factory to create a function which formats date,
    given as a ``datetime`` object or a tuple of ``int``

- new module ``profile``:

  - ``StopWatch`` context manager and ``@profile`` decorator

- new module ``mock``:

  - a few small classes for use in doctests

  - the same module as ``visaplan.plone.tools.mock``

- module ``debug``:

  - new decorators ``trace_this``, ``log_result``

  - new function ``print_indented``

  - new factory function ``make_sleeper``

- module ``dicts``:

  - new function ``make_key_injector``

- module ``minifuncs``:

  - new function ``translate_dummy``

- module ``sequences``:

  - new function ``nocomment_split``

  - new function ``columns``
    [tobiasherp]

- module ``lands0``:

  - new function ``join_stripped``

- License changed to GPLv2


1.2 (2018-07-11)
----------------

- breaking changes:

  - ``classes``: Proxy is now a factory rather than a class

- modules ``debug``, ``dicts``, ``lands0``, ``minifuncs``
  [tobiasherp]


1.1 (2018-06-12)
----------------

- modules ``sequences``, ``times``, ``files``
- Minor Bugfixes
  [tobiasherp]


1.0 (2018-06-11)
----------------

- Initial release, including modules ``classes``, ``html``, ``http`` and ``coding``
  [tobiasherp]
