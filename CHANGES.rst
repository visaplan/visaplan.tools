Changelog
=========


1.5.0 (estimated)
-----------------

Breaking changes:

- Remove deprecated ``.http`` functions:

  - ``http_statustext``, because of questionable `func` option
  - ``make_url``


1.3.13 (2024-03-21)
-------------------

New Features:

- New function .http.qad_hostname (for valid absolute URLs only)

Improvements:

- Improved .words.head to avoid implicit string decoding

Miscellaneous:

- We make clear that our .words.head function doesn't handle HTML markup correctly
  (but unescapes entities only, if requested).
  Use the similar function from visaplan.kitchen.extract instead.

[tobiasherp]


1.3.12 (2023-05-02)
-------------------

Improvements:

- .buildout.checkPathForPackage:

  - Changed the default for `invalid` (path entries) to `WARN`,
    because we got wrong exceptions for not-found packages.

  - Since we require importlib-metadata_ now,
    .buildout.checkPathForPackage doesn't
    scan the `sys.path` for the given package anymore
    (unless given as `path` or requested by `use_importlib=False`)
    but tries importlib_metadata.version().

Requirements:

- importlib_metadata_

[tobiasherp]


1.3.11 (2023-03-21)
-------------------

- New functions in .minifuncs module:

  - NoneOrFloat
  - NoneOrDecimal

[tobiasherp]


1.3.10 (2023-03-08)
-------------------

New Features:

- new module .minicurr to map some popular currency specs to their respective 
  `ISO 4217`_ codes
- new function .minifuncs.is_nonempty_string

[tobiasherp]


1.3.9 (2022-11-21)
------------------

Bugfixes:

- .html.make_picture didn't support the `sizes` option.
  We do so now for img[srcset] (not yet for picture elements)

Improvements:

- .html.make_picture:

  - `img_style` option

[tobiasherp]


1.3.8 (2022-09-20)
------------------

Improvements:

- .html.make_picture:

  - `rel` option (implies ``<a>`` element and the need for `href`)
  - `outer_class` option (used for the outmost element;
    with `img_class` and without an ``<a>``, implies a ``<div>``
  - improved internal `need_picture` criterion

[tobiasherp]


1.3.7 (2021-10-27)
------------------

New Features:

- ``.html`` module:

  - new function `from_plain_text`
  - new character generator `entity_aware`

- ``.words`` module:

  - New options for `head`:

    - `detect_entities` (using ``.html.entity_aware``)
    - `max_fuzz`
    - `return_tuple`

[tobiasherp]


1.3.6 (2021-10-06)
------------------

New Features:

- ``.words`` module, providing a ``head`` function

[tobiasherp]


1.3.5.post2 (2021-10-01)
------------------------

Corrected changes list.
[tobiasherp]


1.3.5 (2021-09-07)
------------------

New Features:

- `.html.make_picture` function to create an ``<img>`` element,
  wrapped in a ``<picture>`` and / or ``<a>`` element as needed
  (currently limited to one ``<source>``
  and not yet supporting ``sizes`` attributes)

- `.lands0` module:

  - new function `conflate` to join strings,
    with a simple remove-equal-leading-words facility;
    allows non-default or suppressed sorting
  - key function `nouns_first`, e.g. for use with `conflate`

[tobiasherp]


1.3.4.post2 (2021-10-01)
------------------------

Corrected changes list.
[tobiasherp]


1.3.4 (2021-03-24)
------------------

New Features:

- new function ``minifuncs.extract_float``

[tobiasherp]


1.3.3.post2 (2021-10-01)
------------------------

Corrected changes list.
[tobiasherp]


1.3.3 (2021-01-12)
------------------

Miscellaneous:

- The following ``.http`` functions are deprecated:

  - ``http_statustext``, because of questionable `func` option
  - ``make_url``, because it doesn't satisfy the promise suggested by the name.

  With zope.deprecation_ installed, there will be a deprecation warning
  issued on first use.

[tobiasherp]


1.3.2 (2021-01-05)
------------------

Bugfixes:

- ``.sql.subdict_ne`` had failed with `TypeError` exceptions
  if the checked form data contained list values.

[tobiasherp]


1.3.1 (2020-12-16)
------------------

Breaking changes:

- ``.lands0.list_of_strings`` now *does* split strings by default:

  - like for the `str.split` method (which is used internally),
    a `None` split character
    causes the argument to be split using any whitespace

  - to suppress splitting, you may now specify `splitfunc=False`
    which will imply the value to be *stripped*, at least ...

  - ... unless `splitchar=False` is given as well.

Bugfixes:

- ``.lands0.list_of_strings`` didn't split strings by default ...
  
  (You didn't *rely* on this bug, did you?!)

New Features:

- New class `.dicts.ChangesCollector`;
  allows to collect additions *to* and deletions *from* lists (see doctests).
  If collections-extended_ is installed, the `setlist` class is used,
  an "ordered set".

Improvements:

- ``.sequences.nonempty_lines`` now takes a function argument, default: ``string.strip``

New Features:

- new module ``sql`` which helps generating SQL statements; it doesn't try, however,
  to provide any kind of object relational mapping.

  The following function return a statement string with placeholders and a values dictionary:

  - `insert`
  - `update`
  - `delete`
  - `select`

  (a modified copy of the `utils` module from visaplan.plone.sqlwrapper_ v1.0.2),
  with the following unfinished functions removed:

  - `make_grouping_wrapper` (including the helper `_groupable_spectup`)
  - `make_join` (in [v1_3_x]@34490)

  Instead, we have new functions:

  - `subdict_ne` - create a subdict of non-empty values.
    This is a replacement for the `extract_dict` function which (sadly) expects -
    other than the `.dicts.subdict` function - the `fields` argument first.

    It is generated by the `.sql.make_dict_extractor` factory function
    which allows for a few keyword options, e.g. to specify the values considered empty.
  
- new function ``lands0.make_default_prefixer``

[tobiasherp]


1.3.0 (2020-06-12)
------------------

New Features:

- new module ``batches``, containing a `batch_tuples` function which generates (sublist, txt) tuples
- new class ``classes.StackOfDicts``
- new function ``minifuncs.check_kwargs``
- new function ``debug.has_strings``
- new function ``debug.make_debugfile_writer`` (not yet sufficiently generalized)

Requirements:

- six_ module, for Python_ 3 compatibility

[tobiasherp]


1.2.6 (2020-01-08)
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

  - ``StopWatch`` `context manager`_ and ``@profile`` decorator

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

.. _collections-extended: https://pypi.org/project/collections-extended
.. _`context manager`: https://peps.python.org/pep-0343/
.. _importlib_metadata: https://pypi.org/project/importlib-metadata/
.. _`ISO 4217`: https://www.iso.org/iso-4217-currency-codes.html
.. _Python: https://www.python.org
.. _six: https://pypi.org/project/six
.. _visaplan.plone.sqlwrapper: https://pypi.org/project/visaplan.plone.sqlwrapper
.. _zope.deprecation: https://pypi.org/project/zope.deprecation
