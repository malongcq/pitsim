#!/usr/bin/env python
"""
Pre-Day module
generate persons and trips by HITS2008 survey
by Ma Long
"""

import psycopg2
###from pg8000 import DBAPI
from copy import deepcopy
from random import randint

LIMIT = 10
USE_HITS_TRIP_FACTOR = False
SCALE = 1

sql_get_persons = "select person_id,age1,age2,gender,employment,\
  car_license_ownership,motorcycle_license_ownership,vanbuslicense_ownership,\
  environment_friendly from hits2008_person"

sql_get_trips = "select person_id,lpad(start_time::text,4,'0'),org_mtz,dst_mtz,\
  trip_mode,r.TripFactorsStgFinal \
  from hits2008_trip t, hits2008_raw r \
  where t.t_id=r.msno_main and trip_mode is not null \
  order by t.person_id,t.start_time"

__hits_persons = {}

def __init_hits_persons():
  try:
    conn = psycopg2.connect('dbname=fmdb user=postgres')
    ###conn = DBAPI.connect(database='fmdb',user='postgres',host='localhost')
    curs = conn.cursor()
    curs.execute(sql_get_persons)
    for r in curs.fetchall():
      __hits_persons[r[0]] = {'id':r[0],'pending_trip':[],'age1':r[1],'age2':r[2],'gender':r[3],'emp':r[4]}
      __hits_persons[r[0]]['trips'] = {}
      __hits_persons[r[0]]['own_car_lic'] = r[5]
      __hits_persons[r[0]]['own_motor_lic'] = r[6]
      __hits_persons[r[0]]['own_vanbus_lic'] = r[7]
      __hits_persons[r[0]]['env_friend'] = r[8]
    print "%s HITS persons loaded" % len(__hits_persons)

    curs.execute(sql_get_trips)
    cnt = 0
    for r in curs.fetchall():
      cnt+=1
      __hits_persons[r[0]]['trips'][r[1]] = {'start':r[1],'org':r[2],'dst':r[3],'mode':r[4]}
      __hits_persons[r[0]]['trips'][r[1]]['tf'] = r[5]
    print "%s HITS trips loaded" % cnt
  finally:
    conn.close();

persons = {}

def __gen_new_time(t):
  new_mins = 60*int(int(t)/100) + int(t)%100 + randint(-10,10)
  if new_mins<0: new_mins += 10
  new_h = int(new_mins/60)
  new_m = new_mins%60
  new_t = '%02d%02d'%(new_h,new_m)
  return new_t

def __gen_new_person(psn, idx):
  new_psn = deepcopy(psn)
  new_psn['id'] = '%s_p%s' % (new_psn['id'],idx)
  t_oldnew = {}
  
  for t in new_psn['trips']:
    new_t = __gen_new_time(t)
    #print t,new_t
    t_oldnew[t] = new_t
  
  for t_old in t_oldnew:
    new_psn['trips'][t_oldnew[t_old]] = new_psn['trips'].pop(t_old)
  
  return new_psn

def __clone_person(psn, scale):
  for i in xrange(scale):
    new_psn = __gen_new_person(psn, i)
    persons[new_psn['id']] = new_psn  

def __get_clone_factor_hits_trip_factor(psn):
  f = 0
  for t in psn['trips']:
    if psn['trips'][t]['tf'] is not None:
      f += psn['trips'][t]['tf']
  f = f / len(psn['trips'])
  if f<=0: f = 1
  return f

def __get_clone_factor(psn):
  if USE_HITS_TRIP_FACTOR:
    return __get_clone_factor_hits_trip_factor(psn)

  return SCALE

def __init_sims_persons():
  person_trips_cnt = 0
  for p in __hits_persons:
    if LIMIT>0 and person_trips_cnt>=LIMIT: break

    psn = __hits_persons[p]
    if len(psn['trips'])==0: continue
    person_trips_cnt += 1

    f = __get_clone_factor(psn)
    __clone_person(psn, f)

  print '%s perons derived from %s persons has trips' % (len(persons),person_trips_cnt)

#import time
#start_time = time.time()
print 'init. from HITS...'
__init_hits_persons()
print 'init. pre-day trips...'
__init_sims_persons()
#print time.time() - start_time, "seconds"

if __name__ == '__main__':
  pass
  ###print persons
  ###print trips

