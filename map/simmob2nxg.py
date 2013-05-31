import sys
import datetime
import argparse

import psycopg2
import networkx as nx
from shapely.geometry import LineString

DSN = """dbname=SimMobility_DB user=postgres password=5M_S1mM0bility host=172.25.184.11"""

def __build_graph(srid):
    try:
        conn = psycopg2.connect(DSN)
        curs = conn.cursor()
        
        G = nx.DiGraph()
        
        rgis = {}
        curs.execute("SELECT * from get_section_polyline_sg()")
        for ptid,r in enumerate(curs.fetchall()): 
            rid = r[0]
            if rid not in rgis: rgis[rid] = []
            rgis[rid].append((ptid,r[1],r[2]))
        ###print rgis
        
        pts = {}
        for rid in rgis:
            for ptid,x,y in rgis[rid]:
                pts[ptid] = (x,y)
        ###print pts,len(pts)
        
        G.graph['Points'] = pts
        G.graph['SRID'] = srid
        G.graph['Source'] = 'simmob'
        
        link_id = 0
        curs.execute("SELECT * from get_section_sg()")
        for r in curs.fetchall():
            ptlst = [ptid for ptid,x,y in rgis[r[0]]]
            ###print ptlst, [pts[p] for p in ptlst]
            G.add_edge(ptlst[0],ptlst[-1],id=link_id,points=ptlst,road_name=r[1],length=r[7],lane=r[2],speed=r[3],capacity=r[4])
            link_id += 1
        print link_id,'links after add section,',
        ###print [desc[0] for desc in curs.description]
        
        curs.execute("SELECT * from get_lane_connector_sg()")
        miss_turning = 0
        dup_turning = 0
        for r in curs.fetchall(): 
            from_sec = r[1]
            to_sec = r[2]
            if from_sec not in rgis or to_sec not in rgis: 
                miss_turning += 1
                continue
            
            pts1 = [ptid for ptid,x,y in rgis[from_sec]]
            pts2 = [ptid for ptid,x,y in rgis[to_sec]]
            
            if G.has_edge(pts1[-1],pts2[0]): 
                dup_turning += 1
                continue
                   
            G.add_edge(pts1[-1],pts2[0],id=link_id,points=[pts1[-1],pts2[0]],turning=True)
            link_id += 1
        print '%d links after add turnings(miss=%d,duplicate=%d).' % (link_id,miss_turning,dup_turning)
        ###print [desc[0] for desc in curs.description]
        
        return G
    finally:
        conn.close()

def __trim_graph(G):
    '''deprecated, only merged turnings'''
    in1 = [n for n,idg in G.in_degree_iter() if idg==1]
    out1 = [n for n,odg in G.out_degree_iter() if odg==1]
    d2s = set(in1) & set(out1)
    
    for n in d2s:
        n1s = G.successors(n)
        n0s = G.predecessors(n)
        assert len(n0s)==1 and len(n1s)==1
        n1 = n1s[0]
        n0 = n0s[0]
        l0 = G[n0][n]
        l1 = G[n][n1]
        
        if 'road_name' in l0 and 'turning' in l1:
            zs = dict(l0.items())
        elif 'road_name' in l1 and 'turning' in l0:
            zs = dict(l1.items())
        else:
            #print n0,n,l0
            #print n,n1,l1
            continue 
    
        zs['points'] = l0['points'][0:-1]+l1['points']
        G.remove_edge(n0, n)
        G.remove_edge(n, n1)
        G.remove_node(n)
        G.add_edge(n0, n1, attr_dict=zs)
        
    #print nx.shortest_path(G, source=56992, target=57004)

def __trim_graph2(G):
    merged = __merge_links(G)
    while merged>0:
        merged = __merge_links(G)
        ###print 'G={nodes=%s, links=%s}' % (len(G.nodes()),len(G.edges()))
    
    pts = G.graph['Points']
    for u,v in G.edges_iter():
        line = LineString([pts[ptid] for ptid in G[u][v]['points']])
        G[u][v]['length'] = line.length
        
        speed = G[u][v]['speed'] if 'speed' in G[u][v] else 50
        G[u][v]['weight'] = line.length/(speed*1000/3600)
        ###print G[u][v]
        
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
        
        if 'road_name' in l0 and 'road_name' in l1:
            if l0['road_name'] != l1['road_name'] : continue
            if l0['lane'] != l1['lane'] : continue
            if l0['capacity'] != l1['capacity'] : continue
            if l0['speed'] != l1['speed'] : continue
        
        if 'road_name' in l0 and 'road_name' not in l1:
            zs = dict(l0.items())
        elif 'road_name' in l1 and 'road_name' not in l0:
            zs = dict(l1.items())
        else:
            zs = dict(l0.items())
        
        zs['points'] = l0['points'][0:-1]+l1['points']
        if G.has_edge(n0,n): G.remove_edge(n0, n)
        if G.has_edge(n,n1): G.remove_edge(n, n1)
        if G.has_node(n): G.remove_node(n)
        if n0!=n1: G.add_edge(n0, n1, attr_dict=zs)
        merged += 1
        
    return merged

def do_main(fn_out):
    g = __build_graph(32648)
    print 'G={nodes=%s, links=%s} before trim' % (len(g.nodes()),len(g.edges()))
    __trim_graph2(g)
    print 'G={nodes=%s, links=%s}' % (len(g.nodes()),len(g.edges()))
    
    print 'Writing graph to %s...'%fn_out
    nx.write_gpickle(g, fn_out)
    
    print 'Testing graph from %s...'%fn_out
    gg = nx.read_gpickle(fn_out)
    print 'G={nodes=%d, links=%d, points=%d}' % (len(gg.nodes()),len(gg.edges()),len(gg.graph['Points']))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o","--output", metavar='file',type=str,default='graph.simmob.nxg', 
        help="Output graph dume file for DiGraph of Networkx, default is [graph.simmob.nxg]")

    args = parser.parse_args()
    
    Start = datetime.datetime.now()
    do_main(args.output)
    print 'Done in %fs' %(datetime.datetime.now() - Start).total_seconds()