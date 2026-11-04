import numpy as np, math
AX,AY=140.0,640.0; L=800.0; R=L/math.pi; HH=2*R; BX,BY=AX+L,AY+HH
G=R*math.pi**2/3.3**2          # cycloid descent takes 3.3 s
def path(kind,n=4000):
    if kind=='cyc':
        th=np.linspace(0,math.pi,n); return AX+R*(th-np.sin(th)),AY+R*(1-np.cos(th))
    u=np.linspace(0,1,n)
    if kind=='line': return AX+L*u,AY+HH*u
    if kind=='dive':
        y=HH*u+DIVE*np.sin(np.pi*u)**1.0*(1-0.25*u)
        return AX+L*u,AY+y
DIVE=450.0
def timing(x,y):
    ds=np.hypot(np.diff(x),np.diff(y)); h=(y[:-1]+y[1:])/2-AY
    v=np.sqrt(2*G*np.maximum(h,1e-9)); dt=ds/v
    # first segment: analytic start (v from 0)
    dt[0]=math.sqrt(2*ds[0]/(G*max((y[1]-y[0])/ds[0],1e-6)))
    t=np.concatenate([[0],np.cumsum(dt)]); return t
TR={}
for k in ('line','cyc','dive'):
    x,y=path(k); TR[k]=(x,y,timing(x,y))
if __name__=='__main__':
    for k,(x,y,t) in TR.items(): print(k,'time',round(t[-1],3),'maxy',round(y.max()),'len',round(np.hypot(np.diff(x),np.diff(y)).sum()))
