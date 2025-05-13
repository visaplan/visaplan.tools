To Do
=====

Breaking changes, estimated for future releases:

- Signature change (e.g. name of first argument: ``form`` --> ``dic``) for
  ``dicts.update_dict``

  (estimated for release 2.0.0)

- Remove deprecated ``.http`` functions:

  - ``http_statustext``, because of questionable `func` option
  - ``make_url``

  (estimated for release 1.5.0)
 
Bugs to be fixed:

- The `.html.make_picture` function currently creates ``srcset`` attributes with
  width descriptors but no ``sizes`` attribute -- which is needed for the
  ``srcset`` to be honored!

Other things to do:

- In the .buildout module, use importlib-metadata_!
- Turn the information above in a nice table

.. _importlib-metadata: https://pypi.org/project/importlib-metadata/

