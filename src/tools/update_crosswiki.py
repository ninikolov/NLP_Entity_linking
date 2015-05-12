__author__ = 'wolfv'

import pymysql
import pymysql.cursors

connection = pymysql.connect(host='localhost',
                             user='wolfv',
                             passwd='abcde',
                             db='mw',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

import sqlite3
import marshal
import sys
import math
cw_connection = sqlite3.connect("../../data/crosswikis-dict-preprocessed" + "-db.db")
cw_new_connection = sqlite3.connect("../../data/crosswikis-dict-preprocessed_new" + "-db.db")
try:
    cw_new_connection.execute('''CREATE TABLE entity_mapping (words TEXT, entities BLOB)''')
except:
    print("TABLE EX|IST")
cw_cursor = cw_connection.cursor()
cw_new_cursor = cw_new_connection.cursor()

cw_query = "SELECT * FROM entity_mapping"
cw_cursor.execute(cw_query)

mw_cursor = connection.cursor()
query = 'SELECT page.page_title, redirect.rd_title FROM page LEFT JOIN redirect ON redirect.rd_from = page.page_id WHERE page.page_title = %s'
i = 0
total_redirects = 0
total_entity_missing = 0
total_nothing = 0
for row in cw_cursor.fetchall():
    i += 1
    print("ROW: %i / 4567" % i)
    entities = marshal.loads(row[1])
    new_entities = []
    redirects = 0
    entity_missing = 0
    nothing = 0
    print("Number of entities: %i\n" % len(entities))
    total = len(entities)
    inc = total/20
    current = 0
    for e in entities:
        current += 1
        sys.stdout.write('\r')
        j = math.floor(current / inc)
        sys.stdout.write("[%-20s] %d%%" % ('='*j, 5*j))
        sys.stdout.flush()

        mw_cursor.execute(query, (e[0],))
        result = mw_cursor.fetchone()
        if not result:
            # print("NOT EXISTING ANYMORE", e)
            entity_missing += 1
        elif result["rd_title"]:
            redirects += 1
            new_entities.append((result["rd_title"].decode("utf-8"), e[1]))
        else:
            nothing += 1
            new_entities.append(e)
        if current > 1000:
            break

    print("\nRedirects", redirects, "Missing", entity_missing)
    total_redirects += redirects
    total_entity_missing += entity_missing
    total_nothing += nothing

    cw_new_cursor.execute('INSERT INTO entity_mapping VALUES(?, ?)', (row[0], marshal.dumps(new_entities)))
    cw_new_connection.commit()

    row = cw_cursor.fetchone()



print("\n\nRedirects, total: ", total_redirects)
print("\n\nEntity Missing, total: ", total_entity_missing)
print("\n\nCorrect, total: ", total_nothing)