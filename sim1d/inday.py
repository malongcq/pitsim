#!/usr/bin/env python

"""
Within-Day module
generate route for each trip
by Ma Long
"""

import psycopg2
import atexit

conn = psycopg2.connect('dbname=fmdb user=postgres')
curs = conn.cursor()
#print 'connect db'

def __close_db():
  #print 'disconnect db'
  curs.close()
  conn.close()

atexit.register(__close_db)

sql_get_path = '''SELECT * FROM shortest_path('SELECT gid AS id, inode::int4 AS source, \
  jnode::int4 as target, length::double precision AS cost \
  FROM ntu_sg_map',%(from)s, %(to)s, false, false)'''

def __get_path_pgrouting(node0, node1):
  path = []
  curs.execute(sql_get_path % {'from':node0, 'to':node1})
  for r in curs:
    path.append(r[1])
  return path

def set_path(trip):
  path = __get_path_pgrouting(trip['from_node'], trip['to_node'])
  trip['path'] = path
  return len(path)

def choose_trip(pending_trips):
  return pending_trips.pop(0)

if __name__ == '__main__':
  pass
