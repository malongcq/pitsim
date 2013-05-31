import sys
import datetime
import argparse
import pickle

def __write_tags(f, osmid, data, src):
    if 'tags' not in data: return
    
    tags = data['tags']
    for key, value in tags.iteritems():
        try:
            s_k = str(key)
            s_v = str(value)
            f.write('\"%d\",\"%d\",\"%s\",\"%s\"\n'%(osmid,src,s_k,s_v))
        except:
            continue
    
def do_main(dmp_nodes, dmp_ways, dmp_relations, csv_nodes, csv_ways, csv_relations, csv_tags):
    with open(dmp_nodes, 'rb') as f, open(csv_nodes, 'wb') as fn, open(csv_tags, 'a') as ft:
        ft.write('osm_id,source,key,value\n')
        
        fn.write('osm_id,lat,lon\n')
        print 'Reading from %s...'%dmp_nodes
        nodes = pickle.load(f)
        for osmid in nodes:
            node = nodes[osmid]
            __write_tags(ft,osmid,node,0)
            fn.write('%d,%f,%f\n'%(osmid,node['lat'],node['lon']))
    
    with open(dmp_ways, 'rb') as f, open(csv_ways, 'wb') as fw, open(csv_tags, 'a') as ft:
        fw.write('osm_id,idx,ref_id\n')
        print 'Reading from %s...'%dmp_ways
        ways = pickle.load(f)
        for osmid in ways:
            way = ways[osmid]
            __write_tags(ft,osmid,way,1)
            refs = way['refs']
            for i,r in enumerate(refs):
                fw.write('%d,%d,%d\n'%(osmid,i,r))
            
    with open(dmp_relations, 'rb') as f, open(csv_relations, 'wb') as fr, open(csv_tags, 'a') as ft:
        fr.write('osm_id,idx,member_id,member_type,member_role\n')
        print 'Reading from %s...'%dmp_relations
        relations = pickle.load(f)
        for osmid in relations:
            relation = relations[osmid]
            __write_tags(ft,osmid,relation,2)
            members = relation['members']
            for i,(m_id,m_type,m_role) in enumerate(members):
                fr.write('%d,%d,%d,%s,%s\n'%(osmid,i,m_id,m_type,m_role))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("nodes_osm_dmp", help="Nodes dump from OSM data file")
    parser.add_argument("ways_osm_dmp", help="Ways dump from OSM data file")
    parser.add_argument("relations_osm_dmp", help="Relations dump from OSM data file")
    
    parser.add_argument("-n","--csv_file_nodes", metavar='file',type=str,default='osm.nodes.csv', 
        help="CSV file for osm nodes, default is [osm.nodes.csv]")
                        
    parser.add_argument("-w","--csv_file_ways", metavar='file',type=str,default='osm.ways.csv', 
        help="CSV file for osm ways, default is [osm.ways.csv]")
                        
    parser.add_argument("-r","--csv_file_relations", metavar='file',type=str,default='osm.relations.csv', 
        help="CSV file for osm relations, default is [osm.relations.csv]")
        
    parser.add_argument("-t","--csv_file_tags", metavar='file',type=str,default='osm.tags.csv', 
        help="CSV file for osm tags, default is [osm.tags.csv]")
    
    parser.add_argument("-p","--prefix", metavar='str',type=str,default='', 
        help="prefix for csv file")
                        
    args = parser.parse_args()
    f1 = args.prefix + args.csv_file_nodes
    f2 = args.prefix + args.csv_file_ways
    f3 = args.prefix + args.csv_file_relations
    f4 = args.prefix + args.csv_file_tags
    
    Start = datetime.datetime.now()
    do_main(args.nodes_osm_dmp,args.ways_osm_dmp,args.relations_osm_dmp,f1,f2,f3,f4)
    
    print 'Done in %fs' %(datetime.datetime.now() - Start).total_seconds()