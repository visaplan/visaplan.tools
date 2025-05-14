To Do
=====

Breaking changes, estimated for future releases:

- Signature change (e.g. name of first argument: ``form`` --> ``dic``) for
  ``dicts.update_dict``

  (estimated for release 2.0.0)

- Remove deprecated ``.http`` functions:

  - ``http_statustext``, because of questionable `func` option
  - ``make_url``

  (estimated for releases 1.5.0 and 2.1.0)
 
- `.htmlohmy.make_picture` function:

  - Make it support ``<picture>`` elements with ``sizes`` attributes,
    which will require to parse the `sizes` value.

  - ``<img>`` elements should have ``width`` and ``height`` attributes!

Other things to do:

- In the .buildout module, use importlib-metadata_!
- Turn the information above in a nice table

.. _importlib-metadata: https://pypi.org/project/importlib-metadata/

