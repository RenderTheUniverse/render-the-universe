"""Seamless Short: cold open (zoomed climax + hook) -> crossfade into the real start -> body -> crossfade back
into the cold-open frame, so the end flows straight into the loop. No dips, no jump to a separate image."""
import sys, importlib, subprocess, os, numpy as np, cv2
from PIL import ImageFont, ImageDraw, Image
from rtu import *
mod_name,t0,Z,cx,cy,l1,l2,out = sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),sys.argv[6],sys.argv[7],sys.argv[8]
M=importlib.import_module(mod_name)
T_ORIG=list(M.T)
NFC=36; XIN=12; XOUT=18; HOLD=2
def fitsize(txt,path,maxw,start):
    d=ImageDraw.Draw(Image.new('L',(1,1))); s=start
    while s>40 and d.textlength(txt,font=ImageFont.truetype(path,s))>maxw: s-=2
    return s
s1=fitsize(l1,FB,980,96); s2=fitsize(l2,FB,980,100)
hook=text_layer([(l1,FB,s1,330,WHITE),(l2,FB,s2,330+s1+22,ACC)])
def zoom(img,z,r=0.0):
    """zoom by z around the subject; r in [0,1] slides the zoom centre back to the frame centre (r=1, z=1 -> identity)."""
    px=cx*(1-r)+W/2*r; py=cy*(1-r)+H/2*r
    Mx=np.float32([[z,0,W/2-z*px],[0,z,H/2-z*py]])
    return cv2.warpAffine(img,Mx,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
def body(f):                       # original frame with the original captions, no loop fade
    M.T=T_ORIG; return np.clip(M.compose(f),0,255).astype(np.float32)
def look(img,z,g):
    """zoom + the cold-open grade; g in [0,1] blends the grade in."""
    img=zoom(img,z,1-g)
    lum=img.mean(2,keepdims=True); img=lum+(img-lum)*(1+0.25*g)
    img=np.clip(img*(1+0.22*g),0,255)
    yy=np.arange(H)[:,None,None]/H; img=img*(1-0.55*g*np.exp(-((yy-0.215)/0.07)**2))
    return img
def cold(i,release=0.0):
    M.T=[]
    u=i/(NFC-1)
    img=np.clip(M.compose(int(round(t0*FPS))+i),0,255).astype(np.float32)
    z=Z*(1.07-0.07*u); z=z*(1-release)+1.0*release          # zoom back out while handing over
    img=look(img,z,1-release)
    return over(img,hook,1-release)
B0=body(0)
C0=cold(0)
NB=M.NF-FPS                        # body frames without the old 1 s loop fade
def frame(k):
    if k<NFC:                      # cold open, last XIN frames crossfade into the real first frame
        a=smooth((k-(NFC-XIN))/XIN)
        return cold(k,a)*(1-a)+B0*a
    k-=NFC
    if k<NB: return body(k)
    k-=NB                          # crossfade from the running body into the cold-open frame (= loop point)
    az=smooth((k+1)/(XOUT*0.7)) if k<XOUT else 1.0            # push into the cold-open framing first...
    ab=smooth((k+1-XOUT*0.35)/(XOUT*0.65)) if k<XOUT else 1.0  # ...then dissolve into the cold-open frame
    b=look(body(min(NB+k,M.NF-1)),1.0*(1-az)+Z*1.07*az,az)
    return b*(1-ab)+C0*ab
TOTAL=NFC+NB+XOUT+HOLD
def final(k): return np.clip(frame(k),0,255).astype(np.uint8)
if __name__=='__main__':
    if len(sys.argv)>9 and sys.argv[9]=='stills':
        for k in map(int,sys.argv[10:]): Image.fromarray(final(k)).save(f'sm_{mod_name}_{k}.jpg',quality=88)
    else:
        run(final,TOTAL,out,['render']); print('frames',TOTAL,'dur',TOTAL/FPS)
