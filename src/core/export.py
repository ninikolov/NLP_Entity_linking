# -*- coding: utf-8 -*-
# export.py
# Exports results as ODS for spreadsheet view

import sys
sys.path.append("../lib/odswriter/")

from odswriter import writer as ods_writer
from collections import OrderedDict
import pickle


class Export():
    def __init__(self):
        # data: List of OrderedDict of Dict
        self.data = []
        self.new_diff_data = []
        self.row_count = 0
        try:
            self.old_diff_data = pickle.load(open("../data/diff.pickle", "rb+"))
        except:
            print("No old diff loaded ... ")
            self.old_diff_data = None

    def append_row(self, row):
        assert type(row), OrderedDict
        self.data.append(row)

    def save_new_diff(self):
        pickle.dump(self.new_diff_data, open("../data/diff.pickle", "wb+"))

    def diff(self):
        last_row = self.data[-1]
        self.new_diff_data.append(last_row)
        print(self.old_diff_data)
        if self.old_diff_data:
            old_row = self.old_diff_data[self.row_count]
            for od in old_row:
                old_row[od]["bg"] = ""
            self.data.append(old_row)
        self.row_count += 1

    def export(self, filename="export", filetype="ods"):
        print("Exporting: ... ")
        with ods_writer(open(filename + "." + filetype,"wb")) as odsfile:
            for row in self.data:
                odsfile.writerow(row)
        self.save_new_diff()