Changelog
=========

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
