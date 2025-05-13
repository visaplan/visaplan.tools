.. NOTE: Dont delete trailing blanks here;
   not in the table, in particular!

Compatibility
=============

======== ========= ==========================
Versions Python    Using packages *(cumulative)*
======== ========= ==========================
2.0+     3.6+      *(not yet released)*
 
                   drop Python 2 support;
                   don't require ``six`` anymore
-------- --------- --------------------------
1.4+     2.7,      + `setuptools v36.2+ <https://setuptools.pypa.io/en/latest/history.html#v36-2-0>`_
         **3.6+**  + ``[lock]`` extra:
 
                     + zc.lockfile_
                     + packaging_
-------- --------- --------------------------
1.3.12+  2.7       + `importlib_metadata <https://pypi.org/project/importlib-metadata/>`_
-------- --------- --------------------------
1.3+     2.7       + `six <https://pypi.org/project/six>`_
-------- --------- --------------------------
1+       2.7       + `setuptools <https://pypi.org/project/setuptools>`_
======== ========= ==========================

.. _packaging: https://pypi.org/project/packaging/
.. _zc.lockfile: https://pypi.org/project/zc.lockfile
