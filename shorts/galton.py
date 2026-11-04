import numpy as np, cairo, colorsys, sys, math
from rtu import *
DUR=26.0; NF=int(DUR*FPS)
N=10000; ROWS=24; DX=38; DY=24; CX=540
PY0=530; START_Y=470; BIN_TOP=1105; FLOOR=1660
GS=3.4; GR=1.5; PER=10           # grain spacing / radius / grains per layer
TDROP=0.12; TR=0.055; G=5200.0; V0=250.0
rng=np.random.default_rng(11)
# release times: slow start, exponential ramp, all released by T_REL
T_REL=20.0; B=0.27
u=(np.arange(N)+0.5)/N
t0=-1.0+np.log(1+u*(math.exp(B*T_REL)-1))/B
ch=rng.integers(0,2,(N,ROWS))
K=np.concatenate([np.zeros((N,1),int),np.cumsum(ch,1)],1)   # rights after each row; K[:,r] at peg row r
binn=K[:,ROWS]
counts=np.bincount(binn,minlength=ROWS+1)
slot=np.zeros(N,int); seen=np.zeros(ROWS+1,int)
for i in range(N): slot[i]=seen[binn[i]]; seen[binn[i]]+=1
def pegx(r,k): return CX+(k-r/2)*DX
def binx(k): return CX+(k-ROWS/2)*DX
y_exit=PY0+(ROWS-1)*DY+DY*0.6
gx=binx(binn)-(PER-1)/2*GS+(slot%PER)*GS+((slot//PER)%2)*GS*0.25
gy=FLOOR-GR-1-(slot//PER)*GS
d=gy-y_exit; tfall=(-V0+np.sqrt(V0**2+2*G*d))/G
t_exit=t0+TDROP+(ROWS-1)*TR+TR*0.6
t_land=t_exit+tfall
# colours by bin (centre cyan -> edge magenta)
def bincol(k):
    dd=abs(k-ROWS/2)/(ROWS/2)
    return colorsys.hsv_to_rgb(0.52+0.38*dd**0.8,0.75,1.0)
BC=[bincol(k) for k in range(ROWS+1)]
sigma=math.sqrt(ROWS)/2; mu=ROWS/2

bg=make_bg(CX,1000)
# static board layer
stat=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H); c=cairo.Context(stat)
c.set_source_rgba(0.45,0.52,0.8,0.55); c.set_line_width(3); c.set_line_cap(cairo.LINE_CAP_ROUND)
c.move_to(CX-170,START_Y-90); c.line_to(CX-16,START_Y+8); c.stroke()
c.move_to(CX+170,START_Y-90); c.line_to(CX+16,START_Y+8); c.stroke()
for r in range(ROWS):
    for k in range(r+1):
        c.set_source_rgba(0.45,0.52,0.85,0.6); c.arc(pegx(r,k),PY0+r*DY,2.6,0,6.2832); c.fill()
c.set_line_width(1.6)
for k in range(ROWS+2):
    x=binx(k)-DX/2; c.set_source_rgba(0.45,0.52,0.8,0.45); c.move_to(x,BIN_TOP); c.line_to(x,FLOOR); c.stroke()
c.set_line_width(2.5); c.move_to(binx(0)-DX/2,FLOOR+1.5); c.line_to(binx(ROWS)+DX/2,FLOOR+1.5); c.stroke()
STAT=np.ndarray((H,W,4),np.uint8,stat.get_data())[...,[2,1,0]].astype(np.float32)
ORDER=np.argsort(t_land)
land=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H); LST={'t':-1.0}
def landed_upto(t):
    ctx=cairo.Context(land)
    if t<LST['t']:
        ctx.set_operator(cairo.OPERATOR_CLEAR); ctx.paint(); LST['t']=-1.0
    ctx=cairo.Context(land)
    tl=t_land[ORDER]; a=np.searchsorted(tl,LST['t'],'right'); b=np.searchsorted(tl,t,'right')
    for i in ORDER[a:b]:
        col=BC[binn[i]]; ctx.set_source_rgba(col[0],col[1],col[2],1.0); ctx.arc(gx[i],gy[i],GR+0.2,0,6.2832); ctx.fill()
    LST['t']=t
    return np.ndarray((H,W,4),np.uint8,land.get_data())[...,[2,1,0]].astype(np.float32)
mov=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
def moving(t):
    ctx=cairo.Context(mov); ctx.set_operator(cairo.OPERATOR_CLEAR); ctx.paint(); ctx.set_operator(cairo.OPERATOR_ADD)
    act=np.where((t0<=t)&(t_land>t))[0]
    if len(act):
        tt=t-t0[act]
        x=np.full(len(act),float(CX)); y=np.zeros(len(act))
        # drop
        m=tt<TDROP; s=tt[m]/TDROP; y[m]=START_Y+(PY0-6-START_Y)*s*s
        # pegs
        m2=(~m)&(t<t_exit[act]); s=(tt[m2]-TDROP)/TR; r=np.floor(s).astype(int); fr=s-r
        ii=act[m2]; r1=np.minimum(r+1,ROWS)
        xa=pegx(r,K[ii,r]); xb=np.where(r+1<ROWS,pegx(r1,K[ii,r1]),pegx(r1,K[ii,r1]))
        x[m2]=xa+(xb-xa)*np.sin(fr*np.pi/2)
        y[m2]=PY0+r*DY-7+DY*fr*fr-10*np.sin(np.pi*np.minimum(fr*1.4,1))*(1-fr)
        # bin fall
        m3=t>=t_exit[act]; ii=act[m3]; tf=t-t_exit[ii]
        x[m3]=gx[ii]; y[m3]=np.minimum(y_exit+V0*tf+0.5*G*tf*tf,gy[ii])
        ctx.set_source_rgba(0.75,0.97,1.0,1.0)
        for xi,yi in zip(x,y): ctx.arc(xi,yi,3.4,0,6.2832); ctx.new_sub_path()
        ctx.fill()
    return np.ndarray((H,W,4),np.uint8,mov.get_data())[...,[2,1,0]].astype(np.float32)
curve=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
def curve_layer(p):
    ctx=cairo.Context(curve); ctx.set_operator(cairo.OPERATOR_CLEAR); ctx.paint(); ctx.set_operator(cairo.OPERATOR_OVER)
    if p<=0: return None
    xs=np.linspace(-0.5,ROWS+0.5,400); xs=xs[:max(2,int(len(xs)*p))]
    h=N*np.exp(-(xs-mu)**2/(2*sigma**2))/(math.sqrt(2*math.pi)*sigma)/PER*GS
    ctx.set_line_width(5); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(1.0,0.86,0.45,1.0)
    for j,(xv,hv) in enumerate(zip(xs,h)):
        X=binx(0)+xv*DX; Y=FLOOR-hv-6
        (ctx.move_to if j==0 else ctx.line_to)(X,Y)
    ctx.stroke()
    return np.ndarray((H,W,4),np.uint8,curve.get_data())[...,[2,1,0]].astype(np.float32)
T=[(0.0,5.6,text_layer([("10,000 balls.",FB,96,180,WHITE),("Every bounce is a 50/50 coin flip.",FM,50,305,SOFT)])),
   (6.0,11.6,text_layer([("No ball knows",FB,80,190,WHITE),("where it will land…",FB,80,290,WHITE)])),
   (12.0,20.4,text_layer([("…yet together they",FB,78,190,WHITE),("build the same shape.",FB,78,288,WHITE)])),
   (20.8,DUR-1+0.05,text_layer([("The bell curve.",FB,96,180,(255,220,130,255)),("Randomness with a shape you can predict.",FM,44,305,SOFT)]))]
HND=handle(1700)
def compose(f):
    t=f/FPS
    lay=STAT+landed_upto(t)
    mv=moving(t); lay=lay+mv
    cv=curve_layer((t-21.0)/1.2)
    if cv is not None: lay=lay+cv
    x=bg+lay+bloom(lay)*0.6
    img=tonemap(x)
    for a,b,L in T: img=over(img,L,env(t,a,b,hold_end=(b>=DUR-1)))
    img=over(img,HND,1.0)
    return img
C={}
def final(f):
    if 'f0' not in C:
        C['bgt']=tonemap(bg+STAT+bloom(STAT)*0.6); C['bgt']=over(C['bgt'],HND,1.0)
    t=f/FPS
    if t>DUR-1:
        if 'f0' not in C:
            C['f0']=compose(0)
        img=compose(f)
        img=loop_fade(img,C['f0'],C['bgt'],(t-(DUR-1))/1.0)
    else: img=compose(f)
    return np.clip(img,0,255).astype(np.uint8)
if __name__=='__main__':
    print('max bin',counts.max(),'top y',gy.min(),'last land',t_land.max())
    run(final,NF,'galton',sys.argv[1:])
