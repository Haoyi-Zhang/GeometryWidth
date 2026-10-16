"""Vector drawing primitives; copied into each independent project generator."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)

def slack(out):
    from fractions import Fraction as F
    # A rational width-four realization of the identity shown in the diagram.
    b=((F(3,5),0,0,F(4,5)),(0,1,0,0))
    z=((F(5,3),0,0),(0,1,0),(0,0,1),(0,0,0))
    product=lambda a,b:tuple(tuple(sum(x*y for x,y in zip(row,col))
                             for col in zip(*b)) for row in a)
    assert product(b,tuple(zip(*b)))==((1,0),(0,1))
    assert product(b,z)==((1,0,0),(0,1,0))
    d=Drawing((-1.9,-2.15,9.85,1.0))
    d.box('z',0,0,3.25,1.15,
          r'$Z=[(S^{-1/2}X)^T\;\;0]^T$'+'\nrank-three codes')
    d.box('b',4.35,0,4.05,1.15,
          r'$B_i=[A_iS^{1/2}\;\;L_i]$'+'\nrow-orthonormal decoder')
    d.box('y',8.5,0,2.25,1.15,'$Y_i=A_iX$\nexact view')
    d.edge('z','b','e','w');d.edge('b','y','e','w')
    d.text(4,-1.28,r'$L_iL_i^T=I_2-A_iSA_i^T\succeq 0$')
    d.text(4,-1.78,r'$\mathrm{rank}(L_iL_i^T)\leq q-3$')
    d.save(out,'slack')


def generate(out):
    out.mkdir(parents=True,exist_ok=True);slack(out)


def main():
    import tempfile
    p=argparse.ArgumentParser(description='Direct Python calibration-slack diagram.')
    p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    if a.check:
        with tempfile.TemporaryDirectory() as t:
            x,y=Path(t)/'a',Path(t)/'b';generate(x);generate(y)
            assert (x/'slack.pdf').read_bytes()==(y/'slack.pdf').read_bytes()
        print('Calibration and exact reprojection identities and fresh redraw passed.')
    else:generate(a.output_dir)
if __name__=='__main__':main()

