import sys
import datetime
import argparse
import pickle

from imposm.parser import OSMParser

Nodes = {}
Ways = {}
Relations = {}

def callback_coords(coords):
    for osm_id, lon, lat in coords:
        if osm_id not in Nodes: 
            Nodes[osm_id] = {'osm_id':osm_id, 'lat':float(lat), 'lon':float(lon)}
    
def callback_nodes(nodes):
    for osm_id, tags, (lon, lat) in nodes:
        if osm_id not in Nodes: 
            Nodes[osm_id] = {'osm_id':osm_id, 'lat':float(lat), 'lon':float(lon)}
        Nodes[osm_id]['tags'] = tags

def callback_ways(ways):
    for osm_id, tags, refs in ways:
        Ways[osm_id] = {'osm_id':osm_id, 'tags':tags, 'refs':refs}
    
def callback_relations(relations):
    for osm_id, tags, members in relations:
        Relations[osm_id] = {'osm_id':osm_id, 'tags':tags, 'members':members}

def osmdump(osm_src, fn_node, fn_way, fn_relation,concurrency=2,prefix=''):
    osmp = OSMParser(concurrency=concurrency, 
                coords_callback=callback_coords, 
                nodes_callback=callback_nodes, 
                ways_callback=callback_ways, 
                relations_callback=callback_relations)
                
    print 'parsing %s...'%(osm_src)
    osmp.parse(osm_src)
    
    pfn_node = prefix+fn_node
    pfn_way = prefix+fn_way
    pfn_relation = prefix+fn_relation
    with open(pfn_node,'w') as fn, open(pfn_way,'w') as fw, open(pfn_relation,'w') as fr:
        print 'writing nodes to %s...'%(pfn_node)
        pickle.dump(Nodes, fn)
        print 'writing ways to %s...'%(pfn_way)
        pickle.dump(Ways, fw)
        print 'writing relations to %s...'%(pfn_relation)
        pickle.dump(Relations, fr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("osm", 
                        help="OSM file in *.osm or *.osm.pbf")
    parser.add_argument("-fn","--file_nodes", metavar='file',type=str,default='nodes.osm.dmp', 
                        help="Dump file for osm nodes, default is [nodes.osm.dmp]")
    parser.add_argument("-fw","--file_ways", metavar='file',type=str,default='ways.osm.dmp', 
                        help="Dump file for osm ways, default is [ways.osm.dmp]")
    parser.add_argument("-fr","--file_relations", metavar='file',type=str,default='relations.osm.dmp', 
                        help="Dump file for osm relations, default is [relations.osm.dmp]")
    parser.add_argument("-p","--prefix", metavar='str',type=str,default='', 
                        help="prefix for dump file")
    parser.add_argument("-c","--concurrency", metavar='N',type=int,default=1,
                        help="# of concurrent processes, default N=1")
    #parser.add_argument("--test", action="store_true",help="Test run, only process one iteration")
    args = parser.parse_args()
    
    Start = datetime.datetime.now()
    osmdump(args.osm,args.file_nodes,args.file_ways,args.file_relations,args.concurrency,args.prefix)
    print 'Done in %fs' %(datetime.datetime.now() - Start).total_seconds()