import sys
import datetime
import argparse

import networkx as nx
import matplotlib.pyplot as plt

def do_main(fn_nxg, w=32, h=18):
    gg = nx.read_gpickle(fn_nxg)
    src = gg.graph['Source'] if 'Source' in gg.graph else ''
    print 'G={nodes=%d, links=%d, source=%s, srid=%s, points=%d}' % (len(gg.nodes()),len(gg.edges()),src,gg.graph['SRID'],len(gg.graph['Points']))
    
    plt.figure(figsize=(w,h))
    pts = nx.get_edge_attributes(gg,'points')
    for eg in pts:
        xys = [gg.graph['Points'][p] for p in pts[eg]]
        xs = [x for x,y in xys]
        ys = [y for x,y in xys]
        plt.plot(xs, ys)
    plt.savefig('%s.png'%(fn_nxg))
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("nxg", help="NetworkX graph dump file")                  
    args = parser.parse_args()
    
    Start = datetime.datetime.now()
    do_main(args.nxg)
    print 'Done in %fs' %(datetime.datetime.now() - Start).total_seconds()