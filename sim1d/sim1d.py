#!/usr/bin/env python

"""
Simulation controller
main entry point for simulator
by Ma Long
"""

SCHEDULE_TRIP_ONLY = True

import simlog

import datetime
import sys
import os

import road
import preday
import inday
import supply
import event

Tick = 60
Start = datetime.datetime.now()

DEBUG = False

persons = preday.persons
network = road.network

def schedule_trip(time, person, org, dst, mod):
  nds = road.odmtz2node(org,dst)
  if nds is None: return

  node0 = nds[0]
  node1 = nds[1]
  print "%s schedule trip at %s from %s[node=%s] to %s[node=%s] by %s" % (person['id'],time,org,node0,dst,node1,mod)
  simlog.trip_start_log((person['id'],time,org,node0,dst,node1,mod))

  trip = {'start':time,'from_node':node0,'to_node':node1,'mod':mod}
  if inday.set_path(trip):
    person['pending_trip'].append(trip)
  else:
    print 'Skip trip, no path found from node=%s to node=%s' % (node0, node1)
  #print trip['path']
  #print '%s has %s pending trips' % (person['id'], len(person['pending_trip']))

def on_trip(time, person):
  person['current_trip']['duration'] += Tick
  trip = person['current_trip']
  link = supply.move_in_tick(Tick, person, network)
  simlog.person_log(person['id'],time,link,trip)

def start_trip(time, person, trip):
  person['current_trip'] = trip
  person['current_trip']['duration'] = 0
  person['current_trip']['distance'] = 0.0
  person['current_trip']['path_idx'] = 0
  #print person['id'],'start trip',person['current_trip']
  link = trip['path'][0]
  network[link]['queue'].append(person['id'])
  simlog.person_log(person['id'],time,link,trip)

def next_person(time, person):
  if time in person['trips']: 
    org = person['trips'][time]['org']
    dst = person['trips'][time]['dst']
    mod = person['trips'][time]['mode']
    schedule_trip(time,person,org,dst,mod)

  if SCHEDULE_TRIP_ONLY: return

  if 'current_trip' in person:
    on_trip(time, person)
  elif len(person['pending_trip'])>0:
    trip = inday.choose_trip(person['pending_trip'])
    start_trip(time, person, trip)

def next_step(time):
  for p in persons:
    if len(persons[p]['trips'])==0: continue
    next_person(time, persons[p])

  #next_person(persons['529944AR6-1'])
  #next_person(persons['760111AR2-1'])

def do_sim():
  for i in xrange(0,24*Tick):
    time_hr = i / 60
    time_mi = i % 60
    time = "%02d%02d" % (time_hr, time_mi)

    event.apply_event(time,persons,network)
    next_step(time)
    supply.update_road_speed(network)
    simlog.network_log(network, time)
    print '%s passed...'%time

  print 'Done in %fs' %(datetime.datetime.now() - Start).total_seconds()
  simlog.trip_end_log(supply.End_Trips)
  print len(supply.End_Trips),'end trips'

if __name__ == '__main__':
  do_sim()
