#!/usr/bin/env python

"""
Road network module
provide GIS-based road network for simulation
by Ma Long
"""

import psycopg2
import random

vdf2spd = {12:80,11:90,21:70,31:50,41:50,42:60,43:70,44:50,45:60,46:70,51:50,52:60,53:70,61:30}
def get_vdf2speed(vdf):
  spd = 50
  if vdf in vdf2spd: spd = vdf2spd[vdf]
  return spd * 1000 / 3600

network = {}
sql_getnetwork = '''select gid,inode,jnode,st_length(the_geom,true),type,modes,lanes,vdf from ntu_sg_map'''

### initialize road network
def init_network(curs):
  curs.execute(sql_getnetwork)
  for r in curs:
    network[r[0]] = {'id':r[0],'src':r[1], 'tgt':r[2], 'len':r[3], 'type':r[4], 'modes':r[5]}
    network[r[0]]['lanes'] = r[6]
    network[r[0]]['speed'] = get_vdf2speed(r[7])
    network[r[0]]['speed_limit'] = get_vdf2speed(r[7])
    network[r[0]]['capacity'] = r[3]*r[6]/5
    network[r[0]]['queue'] = []
  print '%s links loaded' % len(network)

mtz2links = {}
sql_getmtz2links = '''select z.mtz_1092::text, m.gid from ntu_sg_map m, lta_zone_gis z \
  where ST_Intersects(st_transform(m.the_geom,3414),z.the_geom) \
  group by z.mtz_1092, m.gid order by z.mtz_1092, m.gid'''

### initialize mapping table from zone to links
def init_mtz2links(curs):
  curs.execute(sql_getmtz2links)
  for r in curs:
    if r[0] in mtz2links: mtz2links[r[0]].append(r[1])
    else: mtz2links[r[0]] = [r[1]]
  print '%s mtz loaded' % len(mtz2links)

def odmtz2node(mtz0, mtz1):
  link0 = mtz2link(mtz0)
  link1 = mtz2link(mtz1)
  if link0 is None or link1 is None: return None

  nds = ((link0['src'],link1['src']),(link0['src'],link1['tgt']),(link0['tgt'],link1['src']),(link0['tgt'],link1['tgt']))

  for (node0, node1) in nds:
    if node0 != node1: return (node0, node1)
  
  print 'ERROR: can\'t find OD %s[link=%s] to %s[link=%s]' % (mtz0,link0,mtz1,link1)
  return None

def mtz2link(mtz):
  if mtz not in mtz2links: return None

  lnks = mtz2links[mtz]
  lnk = lnks[random.randint(0,len(lnks)-1)]

  if lnk in network: return network[lnk]
  else: return None

try:
  conn = psycopg2.connect('dbname=fmdb user=postgres')
  curs = conn.cursor()
  init_network(curs)
  init_mtz2links(curs)
finally:
  curs.close()
  conn.close()

if __name__ == '__main__':
  #print network
  #print mtz2links
  pass
