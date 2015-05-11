# -*- coding: utf-8 -*-

"""
Baseline code
"""

import marshal

import sqlite3

db_conn = sqlite3.connect('../../data/crosswikis-dict-preprocessed_new-db.db')

def main():
    term = 'bbt'
    c = db_conn.cursor()
    for i in range(3, 0, -1):  # Try combinations with up to 3 words
        c.execute("select * from entity_mapping where words = ?", (term,))
        res = c.fetchone()
        entities = [(d[0], d[1]) for d in marshal.loads(res[1])]
        print(entities)


if __name__ == "__main__":
    main()
