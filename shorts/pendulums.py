import numpy as np, cairo, colorsys, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pendulum_sim import deriv
from rtu import font
W,H,FPS=1080,1920,30
DUR=24.0; NF=int(DUR*FPS); XF=1.0   # last 1s crossfades back to frame 0 (loop)
N=1000; STEP_DEG=1e-6
PX,PY=540,860; L=228

# ---------- simulation ----------
if not os.path.exists('traj.npy'):
    off=(np.arange(N)-(N-1)/2)*np.radians(STEP_DEG)
    s=np.array([np.radians(120)+off,np.full(N,np.radians(120)),np.zeros(N),np.zeros(N)])
    sub=60; dt=1/FPS/sub; out=np.zeros((NF,2,N))
    for f in range(NF):
        out[f]=s[:2]
        for _ in range(sub):
            k1=deriv(s);k2=deriv(s+dt/2*k1);k3=deriv(s+dt/2*k2);k4=deriv(s+dt*k3)
            s=s+dt/6*(k1+2*k2+2*k3+k4)
    np.save('traj.npy',out)
traj=np.load('traj.npy')

# ---------- colours (cyan -> violet -> magenta -> amber) ----------
cols=[]
for i in range(N):
    u=i/(N-1); h=(0.52+0.58*u)%1.0
    cols.append(colorsys.hsv_to_rgb(h,0.85,1.0))

# ---------- background ----------
rng=np.random.default_rng(7)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
r=np.hypot((xx-PX)/W,(yy-PY)/H*1.1)
bg=np.zeros((H,W,3),np.float32)
bg[...,0]=6+10*np.exp(-r*3.2); bg[...,1]=8+12*np.exp(-r*3.2); bg[...,2]=18+34*np.exp(-r*2.6)
stars=Image.new('L',(W,H),0); d=ImageDraw.Draw(stars)
for _ in range(260):
    x,y=rng.uniform(0,W),rng.uniform(0,H); b=int(rng.uniform(40,170)); rr=rng.choice([0.6,0.9,1.3],p=[.6,.3,.1])
    d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=b)
st=np.asarray(stars.filter(ImageFilter.GaussianBlur(0.6)),np.float32)
bg+=st[...,None]*np.array([0.8,0.85,1.0])
# vignette
bg*= (1-0.55*np.clip(r*1.3-0.25,0,1))[...,None]

# ---------- text ----------
FB=font('Inter-Bold.otf')
FM=font('Inter-Medium.otf')
def text_layer(lines):
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    for (txt,font,size,y,col) in lines:
        f=ImageFont.truetype(font,size); w=d.textlength(txt,font=f)
        d.text(((W-w)/2,y),txt,font=f,fill=col)
    # soft shadow for legibility
    a=np.asarray(im,np.float32)/255
    sh=np.asarray(im.split()[3].filter(ImageFilter.GaussianBlur(10)),np.float32)/255*0.7
    return a,sh
WHITE=(255,255,255,255); SOFT=(170,190,235,255); ACC=(120,220,255,255)
T=[ # (start,end,layer)
 (0.0,6.6, text_layer([("1,000 pendulums.",FB,92,200,WHITE),
                       ("Each released 0.000001° apart.",FM,50,322,SOFT)])),
 (7.0,11.2,text_layer([("A difference too small",FB,74,210,WHITE),
                       ("to ever measure…",FB,74,302,WHITE)])),
 (11.6,16.0,text_layer([("…becomes total chaos.",FB,82,250,ACC)])),
 (16.4,DUR-XF+0.05,text_layer([("This is chaos theory.",FB,80,210,WHITE),
                       ("Tiny causes. Unpredictable futures.",FM,46,320,SOFT)])),
]
HANDLE=text_layer([("@RenderTheUniverse",FM,36,1460,(150,165,210,200))])
def env(t,a,b,fi=0.35,fo=0.35):
    if t<a or t>b: return 0.0
    v=1.0
    if a>0: v=min(v,(t-a)/fi)
    v=min(v,(b-t)/fo) if b<DUR-XF else v
    return max(0,min(1,v))

# ---------- frame ----------
surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
def draw_pend(f):
    ctx=cairo.Context(surf)
    ctx.set_operator(cairo.OPERATOR_CLEAR); ctx.paint()
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_width(2.4)
    t1,t2=traj[f]
    x1=PX+L*np.sin(t1); y1=PY+L*np.cos(t1)
    x2=x1+L*np.sin(t2); y2=y1+L*np.cos(t2)
    for i in range(N):
        c=cols[i]; ctx.set_source_rgba(c[0],c[1],c[2],0.17)
        ctx.move_to(PX,PY); ctx.line_to(x1[i],y1[i]); ctx.line_to(x2[i],y2[i]); ctx.stroke()
    for i in range(0,N,1):
        c=cols[i]; ctx.set_source_rgba(c[0],c[1],c[2],0.45)
        ctx.arc(x2[i],y2[i],3.6,0,6.2832); ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER); ctx.set_source_rgba(0.85,0.9,1,1)
    ctx.arc(PX,PY,6,0,6.2832); ctx.fill()
    a=np.ndarray((H,W,4),np.uint8,surf.get_data())
    lines=a[...,[2,1,0]].astype(np.float32)
    # pivot
    return lines
def bloom(lines):
    sm=Image.fromarray(np.clip(lines,0,255).astype(np.uint8)).resize((W//4,H//4),Image.BILINEAR)
    b1=np.asarray(sm.filter(ImageFilter.GaussianBlur(4)),np.float32)
    b2=np.asarray(sm.filter(ImageFilter.GaussianBlur(14)),np.float32)
    b=Image.fromarray(np.clip(b1*0.9+b2*1.1,0,255).astype(np.uint8)).resize((W,H),Image.BILINEAR)
    return np.asarray(b,np.float32)
def over(img,layer,k):
    if k<=0: return img
    a,sh=layer
    img=img*(1-sh[...,None]*k)
    al=a[...,3:4]*k
    return img*(1-al)+a[...,:3]*255*al
def compose(f):
    t=f/FPS
    lines=draw_pend(f)
    x=bg+lines+bloom(lines)*0.75
    img=255*(1-np.exp(-x/170.0))/(1-np.exp(-255/170.0))*(x<1e9)
    img=np.clip(img,0,255)
    for (a,b,lay) in T: img=over(img,lay,env(t,a,b))
    img=over(img,HANDLE,1.0)
    return img
F0=None
BGT=None
def final(f):
    global F0,BGT
    if BGT is None: BGT=np.clip(255*(1-np.exp(-bg/170.0))/(1-np.exp(-255/170.0)),0,255)
    img=compose(f)
    t=f/FPS
    if t>DUR-XF:
        if F0 is None: F0=compose(0)
        u=(t-(DUR-XF))/XF
        a=np.clip(u/0.6,0,1); a=a*a*(3-2*a)
        b=np.clip((u-0.45)/0.55,0,1); b=b*b*(3-2*b)
        img=BGT+(img-BGT)*(1-a)
        img=img*(1-b)+F0*b
    return np.clip(img,0,255).astype(np.uint8)

if __name__=='__main__':
    if sys.argv[1]=='stills':
        for t in map(float,sys.argv[2:]):
            Image.fromarray(final(int(t*FPS))).save(f'still_{t:05.1f}.jpg',quality=92)
    else:
        tmp='pendulums.tmp.mp4'
        p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
            '-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-shortest',
            '-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-profile:v','high','-movflags','+faststart',
            '-c:a','aac','-b:a','128k',tmp],stdin=subprocess.PIPE)
        F0=compose(0)
        for f in range(NF):
            p.stdin.write(final(f).tobytes())
            if f%90==0: print(f,flush=True)
        p.stdin.close(); rc=p.wait()
        if rc==0: os.rename(tmp,'pendulums.mp4')
        print('rc',rc)
