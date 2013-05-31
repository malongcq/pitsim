#!/usr/bin/env python

"""
Supply simulator module
move agent on road network in trip
by Ma Long
"""
End_Trips = []

def update_road_speed(network):
  for s in network:
    set_link_speed2(network[s])

def set_link_speed2(link):
  vmax = link['speed_limit'] * 1.05
  n = len(link['queue'])
  alpha = 0.1

  if n > 1:
    link['speed'] = vmax * ((1.0 / n)**alpha)
  else:
    link['speed'] = vmax

def set_link_speed_dynamit(link):
  k0 = 0.01
  kjam = 0.5
  alpha = 3.75
  beta = 0.56

  k = len(link['queue'])/link['len']
  kmin = k0
  vmax = link['speed_limit']

  if k-kmin>kjam: print 'c=%s,n=%s,l=%s,k=%s' % (link['capacity'],len(link['queue']),link['len'],k)

  if k > k0:
    link['speed'] = vmax * (1 - ((k-kmin)/kjam)**beta)**alpha
  else: 
    link['speed'] = vmax

def get_current_path_idx(trip, network):
  path_len = 0
  path_i = 0
  for i in xrange(len(trip['path'])):
    link = trip['path'][path_i]
    if link==-1: break    

    path_len += network[link]['len']
    if path_len>trip['distance']: break
    else: path_i = i

  return path_i

def get_distance_sec(link, network):
  #print network[link]
  return network[link]['speed']

def end_current_trip(person):
  log = []
  log.append(person['id'])
  log.append(person['current_trip']['start'])
  log.append(person['current_trip']['distance'])
  log.append(person['current_trip']['duration'])
  log.append(person['current_trip']['distance'] / person['current_trip']['duration'])
  End_Trips.append(log)
  ###print person['id'],'end current trip',person['current_trip']
  del person['current_trip']

def travel_link(person, network, link0, link1):
  if link0==link1: return False

  pid = person['id']
  network[link0]['queue'].remove(pid)
  #print 'prev_link:',network[link0]

  if link1 == -1:
    end_current_trip(person)
    ###del person['current_trip']
    return True

  network[link1]['queue'].append(pid)
  #print 'curr_link',network[link1]
  
  return False

def move_in_tick(tick, person, network):
  cur_trip = person['current_trip']
  #print 'move_in_tick',cur_trip['path']
  
  link = cur_trip['path'][cur_trip['path_idx']]
  for sec in xrange(tick):
    prev_link = link
    sec_len = get_distance_sec(link,network)
    cur_trip['distance'] += sec_len
    cur_trip['path_idx'] = get_current_path_idx(cur_trip, network)
    link = cur_trip['path'][cur_trip['path_idx']]

    #print prev_link,link,'dis =',cur_trip['distance'] 
    if travel_link(person,network,prev_link,link): break

  return link

if __name__ == '__main__':
  pass
