# -*- coding: utf-8 -*-
# export.py
# Exports results as ODS for spreadsheet view

import sys
sys.path.append("../lib/odswriter/")

from odswriter import writer as ods_writer
from collections import OrderedDict


class Export():
    def __init__(self):
        # data: List of OrderedDict of Dict
        self.data = list()

    def append_row(self, row):
        assert type(row), OrderedDict
        self.data.append(row)

    def export(self, filename="export", filetype="ods"):
        print("Exporting: ... ")
        with ods_writer(open(filename + "." + filetype,"wb")) as odsfile:
            for row in self.data:
                odsfile.writerow(row)
