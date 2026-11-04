import numpy as np, cairo, math, sys
from rtu import *
from brach_phys import *
DUR=26.0; NF=int(DUR*FPS); T0=4.6
KEYS=['line','cyc','dive']; LAB={'line':'A','cyc':'B','dive':'C'}
NAME={'line':'Straight line','cyc':'Cycloid','dive':'Deep dive'}
COLR={'line':(0.35,0.85,1.0),'cyc':(1.0,0.82,0.35),'dive':(1.0,0.42,0.78)}
FIN={k:TR[k][2][-1] for k in KEYS}
ORDER=sorted(KEYS,key=lambda k:FIN[k])
def pos(k,t):
    x,y,tt=TR[k]
    if t<=0: return x[0],y[0]
    return float(np.interp(t,tt,x)),float(np.interp(t,tt,y))
bg=make_bg(540,1000,seed=12)
surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
def track(c,k,alpha,reveal=1.0,width=6):
    x,y,_=TR[k]; n=max(2,int(len(x)*reveal))
    r,g,b=COLR[k]; c.set_source_rgba(r,g,b,alpha); c.set_line_width(width)
    c.move_to(x[0],y[0])
    for i in range(1,n,8): c.line_to(x[i],y[i])
    c.line_to(x[n-1],y[n-1]); c.stroke()
def ball(c,k,px,py,a=1.0):
    r,g,b=COLR[k]
    c.set_source_rgba(r,g,b,a); c.arc(px,py-14,13,0,6.2832); c.fill()
    c.set_source_rgba(1,1,1,0.8*a); c.arc(px-4,py-18,4,0,6.2832); c.fill()
def label(c,txt,x,y,size,rgb,a=1.0,bold=True,anchor='c'):
    c.select_font_face('Inter',cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size); e=c.text_extents(txt)
    ox={'c':-e.x_advance/2,'l':0,'r':-e.x_advance}[anchor]
    c.move_to(x+ox,y); c.set_source_rgba(*rgb,a); c.show_text(txt)
def draw(t):
    c=cairo.Context(surf); c.set_operator(cairo.OPERATOR_CLEAR); c.paint(); c.set_operator(cairo.OPERATOR_OVER)
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    wheel=t>=13.4
    dimk=smooth((t-12.6)/0.8)
    for k in KEYS:
        a=0.9 if (k=='cyc' or not wheel) else 0.9-0.65*dimk
        if k!='cyc': a=0.9-0.65*dimk
        track(c,k,a,reveal=smooth(t/1.2))
    # start / finish markers
    c.set_source_rgba(0.85,0.9,1,0.9); c.arc(AX,AY,7,0,6.2832); c.fill(); c.arc(BX,BY,7,0,6.2832); c.fill()
    label(c,'START',AX+10,AY-40,30,(0.75,0.82,1.0),0.9*(1-dimk))
    label(c,'FINISH',BX-10,BY+56,30,(0.75,0.82,1.0),0.9*(1-dimk))
    # track letters
    if t<12.6:
        la=smooth(t/1.0)
        for k,(fx) in (('line',0.5),('cyc',0.5),('dive',0.5)):
            x,y,_=TR[k]; i=int(len(x)*{'line':0.42,'cyc':0.62,'dive':0.42}[k])
            off={'line':(-38,-10),'cyc':(10,58),'dive':(0,64)}[k]
            label(c,LAB[k],x[i]+off[0],y[i]+off[1],46,COLR[k],la)
    # balls
    if not wheel:
        for k in KEYS: ball(c,k,*pos(k,(t-T0)),a=1.0)
    # countdown
    for i,n in enumerate(('3','2','1')):
        ts=1.6+i*1.0
        if ts<=t<ts+1.0:
            u=(t-ts); label(c,n,540,1580,170+40*(1-u),(1,1,1),1-smooth((u-0.6)/0.4))
    if T0<=t<T0+0.8: label(c,'GO!',540,1580,150,(1,1,1),1-smooth((t-T0-0.4)/0.4))
    # results rows
    if t>=T0+0.3 and t<13.4:
        ra=1-smooth((t-12.6)/0.8)
        for j,k in enumerate(KEYS):
            y0=1390+j*78
            done=(t-T0)>=FIN[k]
            name=(LAB[k]+'  '+NAME[k]) if t>=10.0 else LAB[k]
            label(c,name,190,y0,44,COLR[k],ra,anchor='l')
            if done:
                rank=ORDER.index(k)+1
                label(c,f"{FIN[k]:.2f} s",760,y0,44,(1,1,1),ra,anchor='r')
                label(c,['1st','2nd','3rd'][rank-1],890,y0,44,(1,0.86,0.45) if rank==1 else (0.7,0.75,0.9),ra,anchor='r')
            else:
                tm=max(0,t-T0); label(c,f"{tm:.2f} s",760,y0,44,(0.7,0.75,0.9),ra*0.7,anchor='r')
    # rolling wheel
    if wheel:
        u=smooth((t-13.9)/6.0); th=math.pi*u
        ccx=AX+R*th; ccy=AY+R
        wa=smooth((t-13.4)/0.5)*(1-smooth((t-24.0)/0.8))
        c.set_source_rgba(0.75,0.82,1.0,0.5*wa); c.set_line_width(2)
        c.move_to(AX-60,AY); c.line_to(BX+60,AY); c.stroke()            # ceiling
        c.set_source_rgba(0.75,0.82,1.0,0.85*wa); c.set_line_width(3); c.arc(ccx,ccy,R,0,6.2832); c.stroke()
        for sp in range(6):
            a=th+sp*math.pi/3; c.move_to(ccx,ccy); c.line_to(ccx-R*math.sin(a),ccy-R*math.cos(a))
        c.set_line_width(1.2); c.stroke()
        px,py=ccx-R*math.sin(th),ccy-R*math.cos(th)
        # traced cycloid in white over the gold track
        tt=np.linspace(0,th,200); c.set_source_rgba(1,1,1,0.95*wa); c.set_line_width(5)
        c.move_to(AX,AY)
        for v in tt: c.line_to(AX+R*(v-math.sin(v)),AY+R*(1-math.cos(v)))
        c.stroke()
        c.set_source_rgba(1,1,1,wa); c.arc(px,py,11,0,6.2832); c.fill()
        ball(c,'cyc',BX,BY,a=wa*0.0)
    a=np.ndarray((H,W,4),np.uint8,surf.get_data()).astype(np.float32)
    return a[...,[2,1,0]],a[...,3:4]/255
T=[(0.0,4.4,text_layer([("Which ball wins?",FB,100,170,WHITE),("Comment your guess before the start!",FM,46,295,SOFT)])),
   (4.8,9.6,text_layer([("Same start. Same finish.",FB,72,190,WHITE),("Only the shape differs.",FM,50,290,SOFT)])),
   (10.0,13.2,text_layer([("The shortest path",FB,84,180,WHITE),("finished last.",FB,84,280,(255,140,200,255))])),
   (13.6,21.6,text_layer([("The winner is a cycloid:",FB,70,180,(255,215,120,255)),("the curve a point on a",FM,52,280,WHITE),("rolling wheel traces.",FM,52,346,WHITE)])),
   (22.0,DUR-1+0.05,text_layer([("Fastest ≠ shortest.",FB,90,180,WHITE),("Johann Bernoulli's puzzle from 1696.",FM,46,300,SOFT)]))]
HND=handle(1720)
def compose(f):
    t=f/FPS; rgb,al=draw(t)
    img=bg*(1-al)+rgb
    img=img+bloom(rgb*al*1.0)*0.55
    img=tonemap(img,200)
    for a_,b_,Lr in T: img=over(img,Lr,env(t,a_,b_,hold_end=(b_>=DUR-1)))
    return over(img,HND,1.0)
Cc={}
def final(f):
    t=f/FPS
    if t>DUR-1:
        if 'f0' not in Cc: Cc['f0']=compose(0); Cc['bgt']=over(tonemap(bg.copy(),200),HND,1.0)
        img=loop_fade(compose(f),Cc['f0'],Cc['bgt'],t-(DUR-1))
    else: img=compose(f)
    return np.clip(img,0,255).astype(np.uint8)
if __name__=='__main__':
    print({k:round(FIN[k],2) for k in KEYS})
    run(final,NF,'brach',sys.argv[1:])
