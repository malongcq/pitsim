import networkx as nx
from shapely.geometry import LineString

def find_path(trip_lnks, G, trip_leap):
    possible_path = __simple2_find_path(trip_lnks, G, trip_leap)
    return possible_path
        
def __simple2_find_path(trip_lnks, G, trip_leap):
    path_find_g = __simple2_build_g(trip_lnks, G, trip_leap)
    if path_find_g==None:
        return []
    
    possible_path = []
    (time0, ln0) = trip_lnks[0]
    (time1, ln1) = trip_lnks[-1]
    r = 0
    for (u0,v0,p0) in ln0:
        for (u1,v1,p1) in ln1:
            if p0==p1: continue
            result = __simple_path_find_nodes(path_find_g,p0,p1)
            if result==None: 
                ###print "cannot find path between %s to %s"%(u0,v1)
                continue
            
            (cost, pathz) = result
            p0 = pathz[0]
            r = r + 1
            for s,p1 in enumerate(pathz[1:]):
                eg = path_find_g[p0][p1]
                #### print 'r=%d,s=%d,p0=%d,p1=%d'%(r,s,p0,p1)
                ### for (n0,n1) in eg['path']: print '\t',G[n0][n1]['id'],G[n0][n1]['points']
                links = [G[n0][n1]['id'] for (n0,n1) in eg['path']]
                
                possible_path.append((r,s,eg['start'],eg['end'],eg['time'],eg['weight'],p0,p1,links))
                p0 = p1
    
    return possible_path
    
def __simple2_build_g(trip_lnks, G, trip_leap):
    path_find_g = nx.DiGraph()
    (time0, ln0) = trip_lnks[0]
    for (time1,ln1) in trip_lnks[1:]:
        time_dur = (time1-time0).total_seconds()
        ### filter by time duration
        if time_dur<=0: continue
        if time_dur>trip_leap: 
            print 'Time between 2 GPS points >%d, skipped whole trip!!!'%trip_leap
            return None

        resultset = []
        for (u0,v0,p0) in ln0:
            for (u1,v1,p1) in ln1:
                idx0 = G[u0][v0]['points'].index(p0)
                ptx0 = [G.graph['Points'][p] for p in G[u0][v0]['points'][idx0:]]
                
                idx1 = G[u1][v1]['points'].index(p1)
                ptx1 = [G.graph['Points'][p] for p in G[u1][v1]['points'][:idx1]]
                
                #print ptx0,ptx1
                len0 = LineString(ptx0).length if len(ptx0)>1 else 0
                len1 = LineString(ptx1).length if len(ptx1)>1 else 0
                
                if u0==u1 and v0==v1:
                    ### same link
                    len_total = len0+len1-LineString([G.graph['Points'][p] for p in G[u0][v0]['points']]).length
                    if len_total<0:
                        continue
                        # TODO
                        #print u0,v0,p0,G[u0][v0]['points']
                        #print u1,v1,p1,G[u1][v1]['points']
                        #print len0,len1,LineString([G.graph['Points'][p] for p in G[u0][v0]['points']]).length
                    path_total = [u0,v0]
                elif v0==u1:
                    ### connected link
                    len_total = len0+len1
                    path_total = [u0,v0,v1]
                else:
                    ### diff. link
                    conns = __simple_path_find_nodes(G,v0,u1)
                    if conns==None: continue
                    len_total = len0 + conns[0] + len1
                    path_total = [u0] + conns[1] + [v1]
                
                ### if >70m/s means >250kmh, not reliable for normal vehicle
                if time_dur>0 and len_total/time_dur>70: continue
                
                edgs = __get_link_path(G,path_total)
                resultset.append((p0,p1,len_total,edgs))
                    
        ### no path found between 2 points, then skip dst. point
        if len(resultset)==0: continue
        
        for (p0,p1,length,nodes) in resultset:
            path_find_g.add_edge(p0,p1,weight=length,path=nodes,time=time_dur,start=time0,end=time1)
        
        ### move to next point
        (time0, ln0) = (time1, ln1)
        
    return path_find_g
    
def __get_link_path(G, path):
    p0 = path[0]
    edgs = []
    for p1 in path[1:]:
        assert G.has_edge(p0,p1)
        edgs.append((p0,p1))
        p0 = p1
    return edgs 
    
def __simple_find_path(trip_pts, G):
    """
    1. build a mini-graph to connect each GPS point mapped node set
       for each pair of node set, look for path between node, add edge to mini-graph with weight=length if path found 
    2. looking for shortest path between first and last node set on mini-graph
    ps. mini-graph is an abstract subset of real road network
    """
    path_find_g = __simple_build_g(trip_pts, G)
    
    possible_path = []
    (time0, pts0) = trip_pts[0]
    (time1, pts1) = trip_pts[-1]
    r = 0
    for p0 in pts0:
        for p1 in pts1:
            if p0==p1: continue
            result = __simple_path_find_nodes(path_find_g,p0,p1)
            if result==None: continue
            
            cost = result[0]
            pathz = result[1]
            pt0 = pathz[0]
            r = r + 1
            for s,pt1 in enumerate(pathz[1:]):
                eg = path_find_g[pt0][pt1]
                possible_path.append((r,s,eg['start'],eg['end'],eg['time'],eg['weight'],eg['path']))
                pt0 = pt1
    
    return possible_path
    
def __simple_build_g(trip_pts, G):
    path_find_g = nx.DiGraph()
    (time0, pts0) = trip_pts[0]
    for (time1,pts1) in trip_pts[1:]:
        time_dur = (time1-time0).total_seconds()
        ### filter by time duration
        if time_dur<=0: continue

        resultset = []
        for p0 in pts0:
            for p1 in pts1:
                if p0==p1: continue
                result = __simple_path_find_nodes(G,p0,p1)
                if result==None: continue
                ### if >70m/s means >250kmh, not reliable for normal vehicle
                if time_dur>0 and result[0]/time_dur>70: continue
                resultset.append((p0,p1,result[0],result[1]))
        ### no path found between 2 points, then skip dst. point
        if len(resultset)==0: continue
        
        for (p0,p1,length,nodes) in resultset:
            path_find_g.add_edge(p0,p1,weight=length,path=nodes,time=time_dur,start=time0,end=time1)
        
        ### move to next point
        (time0, pts0) = (time1, pts1)
        
    return path_find_g
    
def __simple_path_find_nodes(graph, n0, n1, attr_cost='weight'):
    try:
        result = nx.bidirectional_dijkstra(graph,n0,n1,weight=attr_cost)
    except:
        result = None
    return result