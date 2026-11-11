import numpy as np, cairo, sys, math
from PIL import Image, ImageDraw, ImageFont
from rtu import *
DUR=30.0; NF=int(DUR*FPS); N=10000
rng=np.random.default_rng(3)
car=rng.integers(0,3,N); pick=rng.integers(0,3,N)
car[:3]=[2,1,0]; pick[:3]=[0,1,2]
host=np.zeros(N,int)
for i in range(N):
    opts=[d for d in range(3) if d!=pick[i] and d!=car[i]]
    host[i]=opts[rng.integers(0,len(opts))]
sw=(pick!=car)                        # switching wins
CUMSW=np.concatenate([[0],np.cumsum(sw)])
GL=2.4; NSLOW=3; TF0=GL*NSLOW; TF1=21.5; BB=0.42
def done(t):
    if t<TF0:
        g=int(t//GL); return g+(1 if (t-g*GL)>=1.45 else 0)
    if t>=TF1: return N
    return int(NSLOW+(N-NSLOW)*(math.exp(BB*(t-TF0))-1)/(math.exp(BB*(TF1-TF0))-1))
# emoji icons
EF=ImageFont.truetype(font('NotoColorEmoji.ttf'),109)
def emoji(ch,size):
    im=Image.new('RGBA',(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=EF,embedded_color=True)
    im=im.crop(im.getbbox()).resize((size,size),Image.LANCZOS); return im
ICON={True:emoji('🚗',150),False:emoji('🐐',140)}
def to_surf(pil):
    a=np.asarray(pil.convert('RGBA'),np.float32)/255
    pm=np.dstack([a[...,2]*a[...,3],a[...,1]*a[...,3],a[...,0]*a[...,3],a[...,3]])
    buf=(pm*255).astype(np.uint8).copy()
    return cairo.ImageSurface.create_for_data(buf,cairo.FORMAT_ARGB32,pil.width,pil.height),buf
ICS={k:to_surf(v) for k,v in ICON.items()}
DX=[290,540,790]; DW=210; DH=320; DT=455
GC,GRW,P=125,80,7.2; GX0=(W-GC*P)/2; GY0=1080
yy,xx=np.mgrid[0:int(GRW*P),0:int(GC*P)]
col=(xx/P).astype(int); row=(yy/P).astype(int)
inside=((xx%P)<P-1.4)&((yy%P)<P-1.4)
IDX=np.where(inside,row*GC+col,-1)
CSW=np.array([90,215,255],np.float32); CST=np.array([255,95,200],np.float32)
GCOL=np.where(sw[:,None],CSW,CST)
bg=make_bg(540,820)
surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
def rrect(c,x,y,w,h,r):
    c.new_sub_path(); c.arc(x+w-r,y+r,r,-math.pi/2,0); c.arc(x+w-r,y+h-r,r,0,math.pi/2)
    c.arc(x+r,y+h-r,r,math.pi/2,math.pi); c.arc(x+r,y+r,r,math.pi,1.5*math.pi); c.close_path()
def door(c,d,openf,content_car,picked,dim=1.0,result=None):
    x=DX[d]-DW/2; y=DT
    # frame / interior
    rrect(c,x,y,DW,DH,14); c.set_source_rgba(0.03,0.04,0.10,1); c.fill_preserve()
    c.set_source_rgba(0.45,0.55,0.95,0.7*dim); c.set_line_width(3); c.stroke()
    if openf>0.02:
        s,_=ICS[content_car]; iw=s.get_width()
        c.save(); c.translate(DX[d]-iw/2,y+DH/2-iw/2+10); c.set_source_surface(s,0,0); c.paint_with_alpha(min(1,openf*1.4)*dim); c.restore()
    # door panel swinging on the left hinge
    w=DW*(1-0.84*openf)
    rrect(c,x,y,w,DH,14)
    g=cairo.LinearGradient(x,y,x+w,y+DH); g.add_color_stop_rgba(0,0.16,0.22,0.48,1); g.add_color_stop_rgba(1,0.09,0.12,0.30,1)
    c.set_source(g); c.fill_preserve(); c.set_source_rgba(0.55,0.65,1.0,0.8*dim); c.set_line_width(3); c.stroke()
    if openf<0.5:
        c.select_font_face('Inter',cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD); c.set_font_size(96)
        e=c.text_extents(str(d+1)); c.move_to(x+w/2-e.x_advance/2*(1-openf),y+DH/2+34)
        c.set_source_rgba(0.85,0.9,1,(1-2*openf)*dim); c.show_text(str(d+1))
        c.arc(x+w-28,y+DH/2+10,8,0,6.2832); c.set_source_rgba(0.85,0.75,0.4,0.9*(1-openf)*dim); c.fill()
    if picked>0:
        rrect(c,x-9,y-9,DW+18,DH+18,20); c.set_source_rgba(0.45,0.9,1.0,picked*dim); c.set_line_width(5); c.stroke()
def scene(c,t):
    if t<TF0:
        g=int(t//GL); u=t-g*GL
        pk=smooth(u/0.35); ho=smooth((u-0.55)/0.35); rv=smooth((u-1.15)/0.35); cl=smooth((u-2.05)/0.3)
        for d in range(3):
            of=ho if d==host[g] else (rv if True else 0)
            if d==host[g]: of=ho
            of=of*(1-cl)
            door(c,d,of,car[g]==d,pk*(1-cl) if d==pick[g] else 0)
        cap=None
        if u<0.55: cap=(f"You pick door {pick[g]+1}",(0.75,0.85,1))
        elif u<1.15: cap=("The host opens a goat door",(0.75,0.85,1))
        elif u<2.1: cap=(("Switching wins" if sw[g] else "Staying wins"),(0.35,0.85,1) if sw[g] else (1,0.4,0.8))
        return cap,(1 if u<0.3 or u>2.1 else 1)
    else:
        n=max(1,done(t)); g=min(N-1,n-1)
        dim=0.75 if t<TF1 else 0.6
        for d in range(3): door(c,d,1.0,car[g]==d,1.0 if d==pick[g] else 0,dim)
        return ((f"Game {n:,}",(0.75,0.85,1)) if t<TF1+0.3 else ("10,000 games",(0.75,0.85,1))),1
FNT={s:ImageFont.truetype(FB,s) for s in (40,46,92)}; FNM=ImageFont.truetype(FM,34)
def counters(n):
    im=Image.new('RGBA',(W,190),(0,0,0,0)); d=ImageDraw.Draw(im)
    s=int(CUMSW[n]); st=n-s
    for cx,lab,v,colr in ((300,'SWITCH WINS',s,(110,220,255,255)),(780,'STAY WINS',st,(255,120,215,255))):
        w=d.textlength(lab,font=FNT[40]); d.text((cx-w/2,0),lab,font=FNT[40],fill=colr)
        pct=f"{100*v/n:.1f}%" if n>0 else "–"
        w=d.textlength(pct,font=FNT[92]); d.text((cx-w/2,46),pct,font=FNT[92],fill=(255,255,255,255))
        cnt=f"{v:,}"; w=d.textlength(cnt,font=FNM); d.text((cx-w/2,150),cnt,font=FNM,fill=(170,185,230,255))
    a=np.asarray(im,np.float32)/255
    return a
def grid(n,t):
    m=(IDX>=0)&(IDX<n)
    img=np.zeros(IDX.shape+(3,),np.float32)+np.array([22,26,48],np.float32)*(IDX>=0)[...,None]
    img[m]=GCOL[IDX[m]]
    # flash for freshly finished games
    fresh=(IDX>=0)&(IDX<n)&(IDX>=done(max(0,t-0.35)))
    img[fresh]=np.minimum(255,img[fresh]*0.4+180)
    return img
T=[(0.0,7.0,text_layer([("Stay or switch?",FB,100,170,WHITE),("Most people say it doesn't matter.",FM,48,295,SOFT)])),
   (7.4,13.6,text_layer([("So I played",FB,86,180,WHITE),("10,000 games.",FB,86,280,WHITE)])),
   (14.0,21.6,text_layer([("Switching keeps",FB,86,180,(110,220,255,255)),("winning…",FB,86,280,(110,220,255,255))])),
   (22.0,DUR-1+0.05,text_layer([("Switch → win 2 of 3.",FB,86,170,WHITE),("Your first pick is right only 1 time in 3.",FM,42,290,SOFT)]))]
HND=handle(1700)
def compose(f):
    t=f/FPS
    c=cairo.Context(surf); c.set_operator(cairo.OPERATOR_CLEAR); c.paint(); c.set_operator(cairo.OPERATOR_OVER)
    cap,_=scene(c,t)
    lay=np.ndarray((H,W,4),np.uint8,surf.get_data()).astype(np.float32)
    al=lay[...,3:4]/255; rgb=lay[...,[2,1,0]]
    img=bg*(1-al)+rgb
    n=done(t)
    gimg=grid(n,t); y0=int(GY0); x0=int(GX0)
    img[y0:y0+gimg.shape[0],x0:x0+gimg.shape[1]]=np.maximum(img[y0:y0+gimg.shape[0],x0:x0+gimg.shape[1]]*0.3,gimg)
    a=counters(n); img[875:875+190]=img[875:875+190]*(1-a[...,3:4])+a[...,:3]*255*a[...,3:4]
    g=bloom(np.maximum(img-60,0)*0.6,3,10); img=img+g*0.35
    if cap:
        L=text_layer([(cap[0],FS,48,795,tuple(int(255*v) for v in cap[1])+(255,))]); img=over(img,L,1.0)
    for a_,b_,Lr in T: img=over(img,Lr,env(t,a_,b_,hold_end=(b_>=DUR-1)))
    return over(np.clip(img,0,255),HND,1.0)
Cc={}
def final(f):
    t=f/FPS
    if t>DUR-1:
        if 'f0' not in Cc:
            Cc['f0']=compose(0); Cc['bgt']=over(bg.copy(),HND,1.0)
        img=loop_fade(compose(f),Cc['f0'],Cc['bgt'],(t-(DUR-1)))
    else: img=compose(f)
    return np.clip(img,0,255).astype(np.uint8)
if __name__=='__main__':
    print('switch wins',CUMSW[-1],CUMSW[-1]/N)
    run(final,NF,'monty',sys.argv[1:])
