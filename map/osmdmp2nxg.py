import sys
import datetime
import argparse
import math
import pickle

import haversine
import networkx as nx

from pyproj import Proj
from shapely.geometry import LineString

VERBOSE = False

Road_Class = {'motorway':(1,90), 'trunk':(2,70), 'primary':(3,70), 'secondary':(4,50), 'tertiary':(5,50), 
        'motorway_link':(6,50), 'trunk_link':(7,50), 'primary_link':(8,50), 'secondary_link':(9,50), 'tertiary_link':(10,50), 
        'road':(11,50), 'unclassified':(12,50), 'residential':(13,40)}

def test_valid_road(tags):
    if 'highway' not in tags: 
        return False
    highway = str(tags['highway']).lower()
    if highway not in Road_Class:
        return False
    if __is_private(tags):
        return False
    return True

def __is_private(tags):
    if 'access' not in tags:
        return False
    v = str(tags['access']).lower()
    if v in ['private','no']:
        return True
    return False

def __is_one_way(tags):
    if 'oneway' not in tags:
        return 1 ### default is one way

    v = str(tags['oneway']).lower()
    if v in ['yes','true','1']: 
        return 1
    elif v in ['no','false','0']:
        return 0
    elif v in ['-1','reverse']:
        return -1

def __add_link(G, refs, road_osm_id, Nodes, highway):
    for i in xrange(len(refs)-1):
        n0 = Nodes[refs[i]]
        n1 = Nodes[refs[i+1]]
        
        ref_len = haversine.distance((n0['lat'],n0['lon']), (n1['lat'],n1['lon']))
        (rclass, speed) = Road_Class[highway]
        time = ref_len/(speed*1000/3600)
        
        id0 = n0['osm_id']
        id1 = n1['osm_id']
        
        ###G.add_node(id0, osm_id=id0, lon=n0['lon'], lat=n0['lat'])
        ###G.add_node(id1, osm_id=id1, lon=n1['lon'], lat=n1['lat'])
        G.add_edge(id0,id1,osm_id=road_osm_id,points=[id0,id1])
        #G.add_edge(id0,id1,road_class=rclass,length=ref_len,weight=time,osm_id=road_osm_id)
        
        if VERBOSE: print id0,id1,G[id0][id1]

def build_graph(nodes, ways, srid):
    print 'Building graph...'
    G = nx.DiGraph()
    g_nodes = {}
    g_roads = {}
    for wid in ways:
        way = ways[wid]
        osmid = way['osm_id']
        tags = way['tags']
        refs = way['refs']
        if not test_valid_road(tags): continue
        
        g_roads[osmid] = way
        for i in refs: g_nodes[i] = nodes[i]
        
        highway = str(tags['highway']).lower()
        oneway = __is_one_way(tags)
        
        if oneway==0:
            ### bi-directional way, add twice
            __add_link(G, refs, osmid, nodes, highway)
            __add_link(G, refs[::-1], osmid, nodes, highway)
        elif oneway==-1:
            __add_link(G, refs[::-1], osmid, nodes, highway)
        else:
            __add_link(G, refs, osmid, nodes, highway)
    
    print 'G={nodes=%s, links=%s} before trim.' % (len(G.nodes()),len(G.edges()))
    G.graph['Source'] = 'osm'
    __trim_graph(G, g_nodes, g_roads, srid)
    
    for (i, (u,v)) in enumerate(G.edges_iter()):
        G[u][v]['id'] = i
        #print u,v,G[u][v]
        
    return G

def __trim_graph(G, nodes, roads, srid):
    proj = Proj(init="epsg:%s"%srid)
    pts = {}
    for nd in nodes.itervalues():
        pts[nd['osm_id']] = proj(nd['lon'], nd['lat'])
        
    G.graph['Points'] = pts
    G.graph['SRID'] = srid
    merged = __merge_links(G)
    while merged>0:
        merged = __merge_links(G)
        #print 'G={nodes=%s, links=%s}' % (len(G.nodes()),len(G.edges()))
    
    k_name = 'name'.decode("utf-8")
    k_highway = 'highway'.decode("utf-8")
    for u,v in G.edges_iter():
        r = roads[G[u][v]['osm_id']]
        #print r['tags']
        
        G[u][v]['road_name'] = r['tags'][k_name].encode("ascii","ignore") if k_name in r['tags'] else 'Undefined'
        G[u][v]['road_type'] = r['tags'][k_highway].encode("ascii","ignore")
        (rclass, speed) = Road_Class[G[u][v]['road_type']]
        G[u][v]['road_class'] = rclass
        G[u][v]['speed'] = speed
        
        line = LineString([pts[ptid] for ptid in G[u][v]['points']])
        G[u][v]['length'] = line.length
        G[u][v]['weight'] = line.length/(speed*1000/3600)
        
        
    #print nx.shortest_path(G, source=231866308L, target=395050919L)

def __merge_links(G):
    in1 = [n for n,idg in G.in_degree_iter() if idg==1]
    out1 = [n for n,odg in G.out_degree_iter() if odg==1]
    d2s = set(in1) & set(out1)

    merged = 0
    for n in d2s:
        n1s = G.successors(n)
        n0s = G.predecessors(n)
        if len(n0s)!=1 or len(n1s)!=1: continue
        
        n1 = n1s[0]
        n0 = n0s[0]
        l0 = G[n0][n]
        l1 = G[n][n1]
        
        osmid0 = l0['osm_id']
        osmid1= l1['osm_id']
        if osmid0 != osmid1: continue
        
        zs = dict(osm_id=osmid0, points=l0['points'][0:-1]+l1['points'])
        if G.has_edge(n0,n): G.remove_edge(n0, n)
        if G.has_edge(n,n1): G.remove_edge(n, n1)
        if G.has_node(n): G.remove_node(n)
        if n0!=n1: G.add_edge(n0, n1, attr_dict=zs)
        merged += 1
        #print n0,n,l0,roads[osmid0]['tags']
        #print n,n1,l1,roads[osmid1]['tags']
        
    return merged
    
#def build_nodes_xy(nodes, epsg):
#    print 'Building node x,y with proj_srid=%s...'%epsg
#    proj = Proj(init="epsg:%s"%epsg)
#    for nid in nodes:
#        node = nodes[nid]
#        node['xy'] = proj(node['lon'],node['lat'])

def do_main(dmp_nodes, dmp_ways, srid, fn_out):
    with open(dmp_nodes, 'r') as fn, open(dmp_ways, 'r') as fw:
        print 'Reading from %s...'%dmp_nodes
        nodes = pickle.load(fn)
        print 'Reading from %s...'%dmp_ways
        ways = pickle.load(fw)
        
        G = build_graph(nodes, ways, srid)
        print 'G={nodes=%s, links=%s}' % (len(G.nodes()),len(G.edges()))
        
        print 'Writing graph to %s...'%fn_out
        nx.write_gpickle(G, fn_out)
        
        print 'Testing graph from %s...'%fn_out
        gg = nx.read_gpickle(fn_out)
        print 'G={nodes=%s, links=%s}' % (len(gg.nodes()),len(gg.edges()))
        
        #for i in gg.graph['Nodes']: print gg.graph['Nodes'][i]
        #for i in gg.graph['Roads']: print gg.graph['Roads'][i]
        #for n,d in gg.nodes_iter(data=True): 
        #    if 'tags' in d: print n,d
        #for u,v,d in gg.edges_iter(data=True): print u,v,d

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("nodes_osm_dmp", 
                        help="Nodes dump from OSM data file")
    parser.add_argument("ways_osm_dmp", 
                        help="Ways dump from OSM data file")
    parser.add_argument("srid", 
                        help="Spatial Reference System Identifier, http://en.wikipedia.org/wiki/SRID")
                        
    parser.add_argument("-o","--output", metavar='file',type=str,default='graph.osm.nxg', 
                        help="Output graph dume file for DiGraph of Networkx, default is [graph.osm.nxg]")
                        
    args = parser.parse_args()
    
    Start = datetime.datetime.now()
    do_main(args.nodes_osm_dmp,args.ways_osm_dmp,args.srid,args.output)
    print 'Done in %fs' %(datetime.datetime.now() - Start).total_seconds()
