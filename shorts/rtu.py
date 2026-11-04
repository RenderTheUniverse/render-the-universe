"""Shared look for Render the Universe Shorts (cosmic dark, 1080x1920, 30 fps)."""
import numpy as np, subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS=1080,1920,30
def font(name):
    """Find a font file by name: ./fonts next to this script first, then the usual system font folders."""
    here=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','fonts')
    roots=[here,'fonts',os.path.expanduser('~/Library/Fonts'),'/Library/Fonts','/System/Library/Fonts',
           os.path.expanduser('~/.fonts'),os.path.expanduser('~/.local/share/fonts'),'/usr/share/fonts','/usr/local/share/fonts','/usr/share/texmf/fonts','C:/Windows/Fonts']
    for r in roots:
        if not os.path.isdir(r): continue
        for dp,_,fs in os.walk(r):
            for f in fs:
                if f.lower()==name.lower(): return os.path.join(dp,f)
    raise FileNotFoundError(f"Font '{name}' not found. Put it in the fonts/ folder (see README).")
FB=font('Inter-Bold.otf')
FM=font('Inter-Medium.otf')
FS=font('Inter-SemiBold.otf')
WHITE=(255,255,255,255); SOFT=(170,190,235,255); ACC=(120,220,255,255); PINK=(255,120,220,255)

def make_bg(cx=540,cy=900,seed=7,stars_n=260):
    rng=np.random.default_rng(seed)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    r=np.hypot((xx-cx)/W,(yy-cy)/H*1.1)
    bg=np.zeros((H,W,3),np.float32)
    bg[...,0]=6+10*np.exp(-r*3.2); bg[...,1]=8+12*np.exp(-r*3.2); bg[...,2]=18+34*np.exp(-r*2.6)
    st=Image.new('L',(W,H),0); d=ImageDraw.Draw(st)
    for _ in range(stars_n):
        x,y=rng.uniform(0,W),rng.uniform(0,H); b=int(rng.uniform(40,170)); rr=rng.choice([0.6,0.9,1.3],p=[.6,.3,.1])
        d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=b)
    s=np.asarray(st.filter(ImageFilter.GaussianBlur(0.6)),np.float32)
    bg+=s[...,None]*np.array([0.8,0.85,1.0])
    bg*=(1-0.55*np.clip(r*1.3-0.25,0,1))[...,None]
    return bg

def text_layer(lines):
    """lines: (text,font,size,y,colour[,x_center])"""
    im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    for ln in lines:
        txt,font,size,y,col=ln[:5]; cx=ln[5] if len(ln)>5 else W/2
        f=ImageFont.truetype(font,size); w=d.textlength(txt,font=f)
        d.text((cx-w/2,y),txt,font=f,fill=col)
    a=np.asarray(im,np.float32)/255
    sh=np.asarray(im.split()[3].filter(ImageFilter.GaussianBlur(10)),np.float32)/255*0.7
    ys=np.where(a[...,3].max(1)>0)[0]
    y0,y1=(max(0,ys.min()-40),min(H,ys.max()+40)) if len(ys) else (0,1)
    return (a[y0:y1],sh[y0:y1],y0)

def over(img,layer,k):
    if k<=0: return img
    a,sh,y0=layer; y1=y0+a.shape[0]
    sub=img[y0:y1]
    sub=sub*(1-sh[...,None]*k)
    al=a[...,3:4]*k
    img[y0:y1]=sub*(1-al)+a[...,:3]*255*al
    return img

def env(t,a,b,fi=0.35,fo=0.35,hold_end=False):
    if t<a or t>b: return 0.0
    v=1.0
    if a>0: v=min(v,(t-a)/fi)
    if not hold_end: v=min(v,(b-t)/fo)
    return max(0.0,min(1.0,v))

def tonemap(x,k=170.0):
    return np.clip(255*(1-np.exp(-x/k))/(1-np.exp(-255/k)),0,255)

def bloom(lines,g1=4,g2=14):
    sm=Image.fromarray(np.clip(lines,0,255).astype(np.uint8)).resize((W//4,H//4),Image.BILINEAR)
    b1=np.asarray(sm.filter(ImageFilter.GaussianBlur(g1)),np.float32)
    b2=np.asarray(sm.filter(ImageFilter.GaussianBlur(g2)),np.float32)
    b=Image.fromarray(np.clip(b1*0.9+b2*1.1,0,255).astype(np.uint8)).resize((W,H),Image.BILINEAR)
    return np.asarray(b,np.float32)

def smooth(x): x=np.clip(x,0,1); return x*x*(3-2*x)

def loop_fade(img,f0,bgt,u):
    """u in [0,1] over the last second: content fades to background, then frame 0 fades in."""
    a=smooth(u/0.6); b=smooth((u-0.45)/0.55)
    img=bgt+(img-bgt)*(1-a)
    return img*(1-b)+f0*b

HANDLE=None
def handle(y=1460):
    global HANDLE
    if HANDLE is None: HANDLE=text_layer([("@RenderTheUniverse",FM,36,y,(150,165,210,200))])
    return HANDLE

def run(final, NF, out, argv):
    """final(f)->uint8 HxWx3. argv: ['stills', t...] or ['render']"""
    if argv[0]=='stills':
        for t in map(float,argv[1:]):
            Image.fromarray(final(min(NF-1,int(round(t*FPS))))).save(f'{out}_still_{t:05.1f}.jpg',quality=92)
        return
    tmp=out+'.tmp.mp4'
    p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
        '-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-shortest',
        '-c:v','libx264','-preset','slow','-crf','20','-pix_fmt','yuv420p','-profile:v','high','-movflags','+faststart',
        '-c:a','aac','-b:a','128k',tmp],stdin=subprocess.PIPE)
    for f in range(NF):
        p.stdin.write(final(f).tobytes())
        if f%150==0: print(out,f,flush=True)
    p.stdin.close(); rc=p.wait()
    if rc==0: os.rename(tmp,out+'.mp4')
    print(out,'rc',rc)

def contact(paths,out,cols=4,w=360,h=640):
    ims=[Image.open(p).resize((w,h)) for p in paths]
    rows=(len(ims)+cols-1)//cols
    s=Image.new('RGB',(cols*(w+10),rows*(h+10)),(40,40,40))
    for i,im in enumerate(ims): s.paste(im,((i%cols)*(w+10),(i//cols)*(h+10)))
    s.save(out,quality=88)
