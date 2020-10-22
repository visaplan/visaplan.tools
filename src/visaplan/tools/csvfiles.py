# -*- coding: utf-8 -*- äöü
"""
CSV-Unterstützung: Excel-kompatible CSV-Dateien erzeugen (Semikolon, UTF-8)

(initial extrahiert aus tan-Browser)
"""

# Python compatibility:
from __future__ import absolute_import

# Standard library:
# from csv import writer as writer_, excel, register_dialect
# from csv import register_dialect
import csv
from codecs import BOM_UTF8

# 3rd party:
from StringIO import StringIO  # hier importiert für Doctests

__all__ = ['ExcelSSV',  # Excel+ssv (semicolon-separated values)
           'csv_writer',
           'make_sequencer',
           ]

# ----------------------- [ aus Products.unitracc.tools.csvfiles ... [
class ExcelSSV(csv.excel):
    """
    "Semicolon separated values";
    der Standard-"Excel-Dialekt" des csv-Moduls verwendet Kommas
    """
    delimiter = ';'
csv.register_dialect('excel_ssv', ExcelSSV)


def csv_writer(csvfile, dialect='excel_ssv', **kwargs):
    r"""
    Wie csv.writer, aber mit unserem erprobten Dialekt.

    >>> io = StringIO()
    >>> wr = csv_writer(io)
    >>> fieldnames = 'eins zwei drei'.split()

    Der "Sequenzer" sorgt dafür, daß die angegebenen Felder von dicts in der gewünschten
    Reihenfolge weggeschrieben werden; nicht aufgeführte Felder werden ignoriert:

    >>> sq = make_sequencer(fieldnames)
    >>> wr.writerow(fieldnames)
    >>> dic1 = dict(eins=1, zwei=22, drei=222, boring='IGNORED')
    >>> wr.writerow(sq(dic1))
    >>> dic2 = dict(drei='extradrei', zwei=0.5, eins='\'')
    >>> wr.writerow(sq(dic2))

    Schreiben beendet; jetzt zurück auf los, und das Ergebnis lesen:

    >>> io.seek(0)
    >>> str(io.read())
    "eins;zwei;drei\r\n1;22;222\r\n';0.5;extradrei\r\n"

    """
    return csv.writer(csvfile, dialect, **kwargs)
# ----------------------- ] ... aus Products.unitracc.tools.csvfiles ]


# --------------------------- [ aus Products.unitracc.tools.misc ... [
def make_sequencer(keys, factory=None):
    """
    gib eine Funktion zurück, die die Werte jedes übergebenen Dictionarys in
    der angegebenen Reihenfolge zurückgibt, z. B. zum Schreiben von
    CSV-Dateien.

    >>> names = ['Ottos', 'Mops', 'hopst', 'fort']
    >>> dic = dict(zip(names, range(len(names), 0, -1)))
    >>> values = make_sequencer(names)
    >>> values(dic)
    [4, 3, 2, 1]
    >>> dic['Mops'] = 'Dackel'
    >>> values(dic)
    [4, 'Dackel', 2, 1]

    Das optionale Argument factory gibt eine Funktion an,
    die zur Transformation jedes einzelnen Werts verwendet wird;
    hier, um alle Strings in Unicode zu konvertieren:

    >>> from visaplan.tools.coding import make_safe_stringdecoder
    >>> uvalues = make_sequencer(names, make_safe_stringdecoder())
    >>> uvalues(dic)
    [4, u'Dackel', 2, 1]
    """

    def in_order_values(dic):
        res = []
        for key in keys:
            res.append(dic[key])
        return res

    def in_order_transformed_values(dic):
        res = []
        for key in keys:
            res.append(factory(dic[key]))
        return res
    if factory is None:
        return in_order_values
    else:
        return in_order_transformed_values
# --------------------------- ] ... aus Products.unitracc.tools.misc ]
