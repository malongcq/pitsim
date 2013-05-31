#!/usr/bin/env python

import os
import atexit

FILE_PERSON = 'sim_result_person.log'
FILE_TRIP_START = 'sim_result_trip0.log'
FILE_TRIP_END = 'sim_result_trip1.log'
FILE_NETWORK = 'sim_result_network.log'

def __check_log_file(filename):
  if os.access(filename, os.F_OK): 
    exit('%s is exist!'%(filename))

__check_log_file(FILE_PERSON)
__check_log_file(FILE_TRIP_START)
__check_log_file(FILE_TRIP_END)
__check_log_file(FILE_NETWORK)

__log_person = open(FILE_PERSON, 'w')
print 'person log set to', __log_person.name

__log_trip_start = open(FILE_TRIP_START, 'w')
print 'trip_start log set to', __log_trip_start.name

__log_trip_end = open(FILE_TRIP_END, 'w')
print 'trip_end log set to', __log_trip_end.name

__log_network = open(FILE_NETWORK, 'w')
print 'network log set to', __log_network.name

def __close_log_files():
  __log_person.close()
  __log_trip_start.close()
  __log_trip_end.close()
  __log_network.close()

atexit.register(__close_log_files)

def __log_line(f, line):
  f.write(','.join([str(x) for x in line]))
  f.write('\n')

def person_log(pid, time, link, trip):
  path = trip['path']
  mod = trip['mod']
  p0 = path[0]
  if(len(path)==1): p1 = p0
  else: p1 = path[-2]

  line = (pid,time,link,p0,p1,mod)
  __log_line(__log_person, line)

def network_log(network, time):
  for l in network:
    link = network[l]
    qlen = len(link['queue'])
    if qlen==0: continue
    line = (time,link['id'],link['speed'],qlen)
    __log_line(__log_network, line)

def trip_end_log(end_trips):
  for line in end_trips:
    __log_line(__log_trip_end, line)

def trip_start_log(line):
  __log_line(__log_trip_start, line)

if __name__ == '__main__':
  pass
