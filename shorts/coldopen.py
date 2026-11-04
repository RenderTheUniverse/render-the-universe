"""Render a 1.2 s cold open from a Short's climax with a hook line, ending in a quick dip."""
import sys, importlib, numpy as np
from rtu import *
mod_name, t0, l1, l2 = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
M=importlib.import_module(mod_name)
NFC=36
hook=text_layer([(l1,FB,84,170,WHITE),(l2,FB,84,268,ACC)])
M.T=[(0.0,M.DUR,hook)]                      # replace the timeline captions with the hook
def final(i):
    img=M.compose(int(round(t0*FPS))+i)
    k=smooth((i-(NFC-6))/5.0)                 # quick dip into the real start
    img=img*(1-0.85*k)
    return np.clip(img,0,255).astype(np.uint8)
if __name__=='__main__':
    if len(sys.argv)>5 and sys.argv[5]=='still':
        from PIL import Image; Image.fromarray(final(0)).save(f'cold_{mod_name}.jpg',quality=90)
    else: run(final,NFC,f'cold_{mod_name}',['render'])
