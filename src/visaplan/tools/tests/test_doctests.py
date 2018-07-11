# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=72 cc=+8
import doctest
import visaplan.tools.classes
import visaplan.tools.coding
import visaplan.tools.html

def load_tests(loader, tests, ignore):
    # https://docs.python.org/2/library/unittest.html#load-tests-protocol
    for mod in (
            visaplan.tools.classes,
            visaplan.tools.coding,
            visaplan.tools.html,
            ):
        tests.addTests(doctest.DocTestSuite(mod))
    return tests
