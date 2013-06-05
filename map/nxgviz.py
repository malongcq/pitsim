import sys
import datetime
import argparse
import ast

import networkx as nx

def do_draw(G, fn_nxg, w=32, h=18, dpi=80, links=[]):
    from matplotlib import pyplot as plt
    import numpy as np
    
    Start = datetime.datetime.now()
    plt.figure(figsize=(w,h),dpi=dpi)
    
    for (u,v,d) in G.edges_iter(data=True):
        xys = [G.graph['Points'][p] for p in d['points']]
        #xs = [x for x,y in xys]
        #ys = [y for x,y in xys]
        xs = np.array([x for x,y in xys])
        ys = np.array([y for x,y in xys])
        
        if links != None and d['id'] in links:
            plt.plot(xs, ys, 'r', linewidth=2)
        else:
            plt.plot(xs, ys, 'b', linewidth=1)
          
    plt.savefig('%s.png'%(fn_nxg))
    print 'Finished img in %fs' %(datetime.datetime.now() - Start).total_seconds()
    
    plt.show()

def do_draw2(G, width=800, height=600, links=[]):
    from Tkinter import *
    
    root = Tk()
    canvas = Canvas(root,width=800,height=600,scrollregion=(0,0,width,height))
    hbar = Scrollbar(canvas,orient=HORIZONTAL)
    hbar.pack(side=BOTTOM,fill=X)
    hbar.config(command=canvas.xview)
    vbar = Scrollbar(canvas,orient=VERTICAL)
    vbar.pack(side=RIGHT,fill=Y)
    vbar.config(command=canvas.yview)
    canvas.config(width=800,height=600)
    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
    canvas.pack(side=LEFT,expand=True,fill=BOTH)
    
    xx0,xx1,yy0,yy1 = 345000,390000,135000,165000
    w2w, h2h = width/float(xx1-xx0), height/float(yy1-yy0)
    
    for (u,v,d) in G.edges_iter(data=True):
        clr = 'red' if links != None and d['id'] in links else 'blue'
        
        xys = [((x-xx0)*w2w,(yy1-y)*h2h) for x,y in [G.graph['Points'][p] for p in d['points']]]
        x0,y0 = xys[0]
        for x1,y1 in xys[1:]:
            canvas.create_line(x0, y0, x1, y1, fill=clr)
            x0,y0 = x1,y1
            
    root.mainloop()

def do_draw3(G, bbox, links=[]):
    import pyglet

    xx0,xx1,yy0,yy1 = bbox
    
    window = pyglet.window.Window(resizable=True,width=800,height=600)
    pyglet.gl.glClearColor(1, 1, 1, 1)
    
    @window.event
    def on_draw():
        window.clear()
        w2w, h2h = window.width/float(xx1-xx0), window.height/float(yy1-yy0)

        pyglet.gl.glColor4f(0,0,1,1)
        #batch = pyglet.graphics.Batch()    
        for (u,v,d) in G.edges_iter(data=True):
            xys = [((x-xx0)*w2w,(y-yy0)*h2h) for x,y in [G.graph['Points'][p] for p in d['points']]]
            pyglet.graphics.draw(len(xys), pyglet.gl.GL_LINES,('v2f', sum(xys,())))
            
    pyglet.app.run()

def do_main(fn_nxg, w=32, h=18, dpi=80, links=[]):
    gg = nx.read_gpickle(fn_nxg)
    src = gg.graph['Source'] if 'Source' in gg.graph else ''
    print 'G={nodes=%d, links=%d, source=%s, srid=%s, points=%d}' % (len(gg.nodes()),len(gg.edges()),src,gg.graph['SRID'],len(gg.graph['Points']))

    l = nx.get_edge_attributes(gg,'points').values()
    ps = [item for sublist in l for item in sublist]
    xs = [gg.graph['Points'][p][0] for p in ps]
    ys = [gg.graph['Points'][p][1] for p in ps]
    
    import math
    xx0,xx1 = math.floor(min(xs)*0.99), math.ceil(max(xs)*1.01)
    yy0,yy1 = math.floor(min(ys)*0.99), math.ceil(max(ys)*1.01)
    print min(xs),max(xs),min(ys),max(ys)
    print xx0,xx1,yy0,yy1
    
    #do_draw(gg,fn_nxg,w,h,dpi,links)
    #do_draw2(gg,width=w*dpi,height=h*dpi,links=links)
    do_draw3(gg,(xx0,xx1,yy0,yy1),links=links)

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