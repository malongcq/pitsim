import sys
import datetime
import argparse
import ast

import networkx as nx
import matplotlib.pyplot as plt

def do_main(fn_nxg, w=32, h=18, dpi=80, links=[]):
    gg = nx.read_gpickle(fn_nxg)
    src = gg.graph['Source'] if 'Source' in gg.graph else ''
    print 'G={nodes=%d, links=%d, source=%s, srid=%s, points=%d}' % (len(gg.nodes()),len(gg.edges()),src,gg.graph['SRID'],len(gg.graph['Points']))
    
    plt.figure(figsize=(w,h),dpi=dpi)
    
    for (u,v,d) in gg.edges_iter(data=True):
        xys = [gg.graph['Points'][p] for p in d['points']]
        xs = [x for x,y in xys]
        ys = [y for x,y in xys]
        
        if links != None and d['id'] in links:
            plt.plot(xs, ys, 'r', linewidth=2)
        else:
            plt.plot(xs, ys, 'b', linewidth=1)
          
    plt.savefig('%s.png'%(fn_nxg))
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("nxg", help="NetworkX graph dump file")
    
    parser.add_argument("--width", metavar='N', type=int, default=32, help="image width in inch, default=32")
    parser.add_argument("--height", metavar='N', type=int, default=18, help="image height in inch, default=18")
    parser.add_argument("--dpi", metavar='N', type=int, default=80, help="image dpi, default=80")
    parser.add_argument('--links', metavar='L', type=int, nargs='*', help='Highlight an list of link ID')
    parser.add_argument('--links2', metavar='Ls', help='Highlight an list of link ID in \"[L,...]\"')
    args = parser.parse_args()
    
    lks = []
    if args.links != None: lks += args.links
    if args.links2 != None: lks += [int(l) for l in ast.literal_eval(args.links2)]
    
    Start = datetime.datetime.now()
    do_main(args.nxg, w=args.width, h=args.height, dpi=args.dpi, links=lks)
    print 'Done in %fs' %(datetime.datetime.now() - Start).total_seconds()