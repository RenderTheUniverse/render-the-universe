import numpy as np, sys
g=9.81
def deriv(s):
    t1,t2,w1,w2=s
    d=t1-t2
    den=3-np.cos(2*d)   # m1=m2=1: 2m1+m2 - m2 cos(2d)
    a1=(-g*3*np.sin(t1)-g*np.sin(t1-2*t2)-2*np.sin(d)*(w2**2+w1**2*np.cos(d)))/den
    a2=(2*np.sin(d)*(w1**2*2+g*2*np.cos(t1)+w2**2*np.cos(d)))/den
    return np.array([w1,w2,a1,a2])
def run(th1,th2,spread_deg,N=1000,T=30,fps=30,sub=40,speed=1.0):
    off=np.linspace(-0.5,0.5,N)*np.radians(spread_deg)
    s=np.array([np.full(N,np.radians(th1))+off,np.full(N,np.radians(th2)),np.zeros(N),np.zeros(N)])
    dt=speed/fps/sub
    out=np.zeros((T*fps,2,N))
    for f in range(T*fps):
        out[f]=s[:2]
        for _ in range(sub):
            k1=deriv(s);k2=deriv(s+dt/2*k1);k3=deriv(s+dt/2*k2);k4=deriv(s+dt*k3)
            s=s+dt/6*(k1+2*k2+2*k3+k4)
    return out
if __name__=="__main__":
    th1,th2,sp=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3])
    o=run(th1,th2,sp)
    x2=np.sin(o[:,0])+np.sin(o[:,1]); y2=-np.cos(o[:,0])-np.cos(o[:,1])
    spread=np.hypot(x2.max(1)-x2.min(1),y2.max(1)-y2.min(1))
    for t in range(0,30,1): print(t, round(float(spread[t*30]),4))
