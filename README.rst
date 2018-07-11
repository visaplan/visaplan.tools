.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

==============
visaplan.tools
==============

This is a collection of utility modules for Python projects.

Features
--------

- "classes" module:

  Several classes derived from Python dicts, e.g. Mirror and Proxy.

- "html" module:

  - HtmlEntityProxy - a dict which returns unicode characters when given a named HTML entity

- "http" module:

  - extract_hostname (using url.split and raising ValueError)

- "coding" module:

  Factory functions to create safe_encode resp. safe_decode functions as needed


Documentation
-------------

The modules are documented by doctests.
Full documentation for end users can be found in the "docs" folder.


Installation
------------

Simply install visaplan.tools by using pip::

    pip install visaplan.tools

or by adding it to your buildout::

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
please use the issue tracker mentioned above.


License
-------

The project is licensed under the Apache Software License.
