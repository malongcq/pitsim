import argparse
import sys
import os
import datetime
import multiprocessing

import networkx as nx 
from pyproj import Proj
from shapely.geometry import LineString
from shapely.geometry import Point
from rtree import index as RTIndex

import gpslog
import triproute as tr

VERBOSE = False
RADIUS = 80
THRESHOLD = 0.5
TRIPLEAP = 240

Road_Network_G = None
Road_Network_Index = None
Road_Network_Links = None

def find_trip_path(f,trip_lnks,tp_no,gps_num):
    route_path = tr.find_path(trip_lnks, Road_Network_G, TRIPLEAP)
    
    set_rt = set()
    for (rt,stg,start,end,time_dur,length,p0,p1,path) in route_path:
        if VERBOSE: print 'DATA',tp_no,stg,path[0],path[-1],time_dur,length,len(path),'nodes'
        data = (tp_no,gps_num,rt,stg,path[0],p0,path[-1],p1,str(start),str(end),time_dur,length,len(path),path)
        f.write('\"%d\",\"%d\",\"%d\",\"%d\",\"%d\",\"%d\",\"%d\",\"%d\",\"%s\",\"%s\",\"%d\",\"%f\",\"%d\",\"%s\"\n'%data)
        
        set_rt.add(rt)
    return len(set_rt)

def get_nearby_links(xy, r=RADIUS):
    L = Road_Network_Links
    G = Road_Network_G
    rtx = Road_Network_Index
    
    pt0 = Point(xy)
    links = set(Road_Network_Index.intersection(pt0.buffer(r).bounds))
    lnz = []
    for lnk in links:
        (u,v) = L[lnk]
        ll = LineString([G.graph['Points'][p] for p in G[u][v]['points']])
        ll_dis = pt0.distance(ll)
        if ll_dis > r: continue # skip too far away link
        
        pt_dis = [(p,pt0.distance(Point(G.graph['Points'][p]))) for p in G[u][v]['points']]
        pt1 = sorted(pt_dis, key=lambda s: s[1])[0]
        lnz.append((u,v,pt1[0]))
        
    ### for ln in lnz: print 'GPS=%s,(i,j,p)=%s'%(xy,ln)
    return lnz

def trips_map_match(f, trips_log, proj):
    t0 = datetime.datetime.now()
    match_cnt = 0
    for i, ts in enumerate(trips_log):
        print '%s: Trip #%d, %d GPS points captured...' % (f.name,i,len(ts))
        trip_lnks = []
        for ii,t in enumerate(ts):
            timestamp = t[0]
            xy = proj(t[1],t[2])
            lnz = get_nearby_links(xy)
            if VERBOSE: print '%d GPS point %s ---> Map links %d:%s' %(ii,xy,len(lnz),list(lnz))
            
            ### skip any non-matched GPS points
            if len(lnz)>0: trip_lnks.append((timestamp, lnz))

        if len(trip_lnks)<2 or float(len(trip_lnks))/len(ts) < THRESHOLD:
            print '%s: not enough links map-matched, skipped'%f.name
            continue        
        
        cnt_path = find_trip_path(f,trip_lnks,i,len(ts))
        print '%s: %d path found.' % (f.name,cnt_path)
        match_cnt += 1 if cnt_path>0 else 0
    print '%s map-match(%d/%d) done in %ds'%(f.name,match_cnt,len(trips_log),(datetime.datetime.now() - t0).total_seconds())
    return match_cnt
    
def __vehicle_map_match(vid, table, proj):
    trips_log = gpslog.get_trips_gps_log(table, vid)
    
    fn = os.path.join(table,vid.strip()) + '.csv'
    with open(fn, 'w') as f:
        f.write('TRIP_NUM,GPS_NUM,ROUTE_NUM,STAGE_NUM,ORG_LINK,ORG_PT,DST_LINK,DST_PT,START_TIME,END_TIME,TIME_s,LENGTH_m,PATH_NUM,PATH_LINKs\n')
        trips_map_match(f,trips_log,proj)
        
def do_vehicle_map_match(args):
    (vid, table, proj) = args
    __vehicle_map_match(vid, table, proj)
    
def build_rtree_index(G):
    rt_index = RTIndex.Index()
    for (u,v,d) in G.edges_iter(data=True):
        ln = LineString([G.graph['Points'][p] for p in d['points']])
        bb = ln.bounds
        rt_index.insert(d['id'],bb)
    return rt_index

def do_main(fn_nxg, table, concurrency = 2, test=True, epsg=None):
    if concurrency > multiprocessing.cpu_count()*0.8:
        concurrency = multiprocessing.cpu_count()*0.8
        print '!!!Too many concurrent tasks requested, reset concurreny=%d!!!'%concurrency
    
    if concurrency < 1: concurrency = 1
    
    if not os.path.exists(table):
        os.makedirs(table)
    
    print 'Reading graph from %s...'%fn_nxg
    nxg = nx.read_gpickle(fn_nxg)
    src = nxg.graph['Source'] if 'Source' in nxg.graph else ''
    if epsg is None: 
        epsg = nxg.graph['SRID']
    print 'G={nodes=%d, links=%d, source=%s, srid=%s, points=%d}' % (len(nxg.nodes()),len(nxg.edges()),src,
            nxg.graph['SRID'],len(nxg.graph['Points']))
    
    print 'Set SRID to %s'%epsg
    proj = Proj(init="epsg:%s"%epsg)
    
    print 'Building RTree index...'
    rtidx = build_rtree_index(nxg)
    
    global Road_Network_G 
    Road_Network_G = nxg
    
    global Road_Network_Index 
    Road_Network_Index = rtidx
    
    global Road_Network_Links
    Road_Network_Links = {}
    links = nx.get_edge_attributes(nxg,'id')
    for l in links: 
        Road_Network_Links[links[l]] = l
        #print nxg[l[0]][l[1]]
    
    pool = multiprocessing.Pool(processes=concurrency)
    
    print 'Loading all vehicle id...'
    vehicles = gpslog.get_all_vehicle_id(table)
    for i in xrange(0,len(vehicles),concurrency):
        pending = []
        for j in xrange(concurrency):
            if i+j<len(vehicles):
                vid = vehicles[i+j]
                pending.append((vid, table, proj))
        if VERBOSE: print pending
        
        if concurrency==1:
            do_vehicle_map_match(pending[0])
        else:
            pool.map(do_vehicle_map_match, pending)
        if test: break
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("nxg", help="Networkx graph binary file for road network")
    parser.add_argument("gps", help="GPS log table name")
    parser.add_argument("--srid", help="Overide SRID of map, Spatial Reference System Identifier, http://en.wikipedia.org/wiki/SRID")
    parser.add_argument("-t","--test", action="store_true",help="Test run, only process one iteration")
    parser.add_argument("-v","--verbose", action="store_true",help="Verbose output")
    parser.add_argument("-r","--radius", metavar='N',type=int,default=80,help="Radius of the circle of GPS point in meter, default N=80")
    parser.add_argument("-p","--tripleap", metavar='N',type=int,default=240,help="Max. GPS time interval in seconds within same trip, default N=300")
    parser.add_argument("-d","--threshold", metavar='N',type=float,default=0.5,help="Threshold of valid matched GPS points for single trip, default N=0.5")
    parser.add_argument("-c","--concurrency", metavar='N',type=int,default=1,help="# of concurrent processes, default N=1")
    args = parser.parse_args()
    
    VERBOSE = args.verbose
    RADIUS = args.radius
    THRESHOLD = args.threshold
    TRIPLEAP = args.tripleap
    
    Start = datetime.datetime.now()
    do_main(args.nxg, args.gps, concurrency=args.concurrency, test=args.test, epsg=args.srid)
    print 'Done in %ds' % (datetime.datetime.now() - Start).total_seconds()