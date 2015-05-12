__author__ = 'wolfv'

import sqlite3
import marshal
cw_new_connection = sqlite3.connect("../../data/crosswikis-dict-preprocessed_new" + "-db.db")

cw_cursor = cw_new_connection.cursor()
cw_query = "SELECT * FROM entity_mapping"
cw_cursor.execute(cw_query)

fp = open("../../data/crosswiki-corrected-entities", "w+")
for row in cw_cursor.fetchall():
    entities = marshal.loads(row[1])
    q = row[0]

    for e in entities:
        fp.write("{}\t{} {}\n".format(q, e[0], e[1]))

fp.close()