.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

.. image:: https://travis-ci.org/visaplan/visaplan.tools.svg?branch=master
       :target: https://travis-ci.org/visaplan/visaplan.tools
.. image::
   https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
       :target: https://pycqa.github.io/isort/

==============
visaplan.tools
==============

This is a collection of utility modules for Python projects.

Features
--------

- ``buildout`` module, for buildout_-built projects:

  Function ``checkPathForPackage`` to check a given package against a versions whitelist.
  Useful if you like to constrain the versions of that package without actually requiring it.

- ``coding`` module:

  Factory functions to create ``safe_encode`` resp. ``safe_decode`` functions as needed

- ``classes`` module:

  Several simple but useful classes derived from Python dicts, e.g. ``Mirror`` and ``Proxy``

- ``dates`` module:

  - parse dates, supporting multiple formats

- ``debug`` module:

  - ``trace_this`` decorator

- ``dicts`` module:

  - several tools to work with standard dictionaries

- ``files`` module:

  - functions related to files; for now ``make_mtime_checker``

- ``html`` module:

  - ``HtmlEntityProxy`` - a dict which returns unicode characters when given a named HTML entity

- ``http`` module:

  - ``extract_hostname`` (using ``url.split`` and raising ``ValueError``)

- ``lands0`` module:

  - several tools to work with *lists and strings*

- ``minifuncs`` module:

  - very small functions, for some cases where functions are used as arguments

- ``profile`` module:

  - a ``StopWatch`` context manager and ``@profile`` decorator

- ``sequences`` module:

  - tools for sequences, e.g. ``inject_indexes``

- ``sql`` module:

  - functions for the generation of SQL statements, including
    `insert`, `update`, `delete` and `select`.

    The visaplan.zope.reldb_ package has a copy of this module which
    uses the SQLAlchemy_ placeholders convention (``:name``).

- ``times`` module:

  - functions related to date and/or time calculations


Documentation
-------------

The modules are documented by doctests.
Apart from this, we don't have real user documentation yet (sorry).


Installation
------------

Simply install visaplan.tools by using pip::

    pip install visaplan.tools

or by adding it to your buildout_::

    [buildout]
    ...
    eggs =
        visaplan.tools

and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/visaplan/visaplan.tools/issues
- Source Code: https://github.com/visaplan/visaplan.tools


Support
-------

If you are having issues, please let us know;
please use the `issue tracker`_ mentioned above.


License
-------

The project is licensed under the GNU General Public License v2 (GPLv2).

.. _buildout: https://pypi.org/project/zc.buildout
.. _`issue tracker`: https://github.com/visaplan/visaplan.tools/issues
.. _SQLAlchemy: https://www.sqlalchemy.org
.. _visaplan.zope.reldb: https://pypi.org/project/visaplan.zope.reldb

.. vim: tw=79 cc=+1 sw=4 sts=4 si et
