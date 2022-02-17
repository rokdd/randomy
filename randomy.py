import numpy as np
import cv2
import matplotlib.pyplot as plt
import random
from string import Template as t
import copy
import sys
import palettable.wesanderson as pat
import io
import base64

def clean_defs(d):
    defs=copy.deepcopy(d)
    for x in ["img",'global_width','global_height','colors']:
        if x in defs:
            del defs[x]
    return defs
class item:
    def __init__(self,cb=None,must={},*args,**kwargs):
        self.cb = cb
        self.must = must
        self.args=args
        self.kwargs=kwargs
    def run(self,defs={},locked=[],exec=True,*args,**kwargs):
        args = {}

        for k, v in self.must.items():
            #print(defs)
            if  v[1] in locked:
                args[k]=defs[v[1]]
            elif isinstance(v, t):
                args[k] = int(v.safe_substitute(defs))
            elif isinstance(v, tuple) and v[1] in defs:
                args[k] = defs[v[1]]
            elif callable(v[1]):
                args[k] = v[1](defs)
            else:
                args[k] = v[1]
                print(type(v),k,v,defs.keys())
        if exec:
            return self.cb(**args,defs=defs,locked=locked)
        return args

    def __str__(self):
        return str(self.cb)

class library:
    def __init__(self,variants,ldefs):
        self.variants=variants
        self.ldefs=ldefs

    def prepare(self,defs={},locked=[],*args,**kwargs):
        locked.append(random.choice(list(defs.keys())))
        for k,v in self.ldefs.items():
            if not k in locked:
                defs[k]=v(defs)

        self.item = self.choice()
        #print('Choose ',self.item,clean_defs(defs))
        return defs,locked

    def run(self,defs={},locked=[],*args,**kwargs):
        self.item.run(defs=defs,locked=locked,*args,**kwargs)

    def choice(self):
        return random.choice(self.variants)

def distribute_solo(defs={},locked=[],*args,**kwargs):
    defs,locked=shapes.prepare(defs=defs,locked=locked,*args,**kwargs)
    #print('solo shape',shapes.item)
    shapes.run(defs=defs, locked=locked, *args, **kwargs)

def distribute_line(defs={},locked=[],*args,**kwargs):
    defs,locked=shapes.prepare(defs=defs, locked=locked, *args, **kwargs)
    # oki lets define numberts
    max_n=random.randint(3,60)
    #print('lets run',max_n,shapes.item)
    params=list(set(defs.keys()) & set(['pt1','pt2','center','radius']))

    pt = random.choice(params)
    pt_opp=[value for value in params if value is not pt]
    stepsize=random.randint(1,5)/70
    coord=random.choice([0,1])
    coord_opp=(0 if coord==1 else 1)
    diff={}
    bool_both=(True if random.randint(0,100)>30 else False)
    #config=random.choice([('pt1',0)])
    #print(clean_defs(defs))
    for n in range(max_n):

        for p in params:
            if p is not pt and not bool_both:
                continue
            if isinstance(defs[p],tuple):
                diff[coord]=(defs[p][coord]-defs[p][coord])+round(stepsize*max(defs['global_width'],defs['global_height']))
            else:
                diff[coord]=(defs[p]-defs[p])+round(stepsize*max(defs['global_width'],defs['global_height']))

            diff[coord_opp]=0
            if bool_both:
                diff[coord_opp]=diff[coord]
            #print('Diff is ',diff[coord],'by stepsize',stepsize,'applied to both:',bool_both,'coord is ',coord)
            if isinstance(defs[p],tuple):
                defs[p]=(defs[p][0]+diff[0],defs[p][1]+diff[1])
            else:
                defs[p] = defs[p][0] + diff[0]
        #print(clean_defs(defs))
        shapes.run(defs=defs,locked=locked,*args,**kwargs)

class shape(item):
    def run(self,defs={},locked=[], *args,**kwargs):
        #print('shape goes')
        args2=super().run(defs=defs,locked=locked,exec=False, *args,**kwargs)
        #print('shoes goes further')
        #print(args2)
        self.cb(defs['img'], **args2)


class line(shape):
    def run(self,defs={},locked=[], *args,**kwargs):
        defs2=copy.deepcopy(defs)
        defs['img']=defs2['img']
        diff_x=(defs2['pt1'][0]-defs2['pt2'][0])
        diff_y=(defs2['pt1'][1]-defs2['pt2'][1])
        stretch=100
        defs2['pt1']=(int(round(defs2['pt1'][0]+(diff_x*stretch))),int(round(defs2['pt1'][1]+(diff_y*stretch))))
        defs2['pt2']=(int(round(defs2['pt2'][0]-(diff_x*stretch))),int(round(defs2['pt2'][1]-(diff_y*stretch))))
        super().run(defs=defs2,locked=locked, *args,**kwargs)


class polyline(shape):
    def run(self,defs={},locked=[], *args,**kwargs):
        defs2=copy.deepcopy(defs)
        defs['img']=defs2['img']

        defs2['pts']=np.int32([defs2['pt1'],defs2['pt2'],(200,500),(900,100)])
        defs2['pts']=[defs2['pts'].reshape((-1, 1, 2))]
        super().run(defs=defs2,locked=locked, *args,lineType=cv2.LINE_AA,**kwargs)

'''
import numpy as np

sz, sh, of = 1000, 500, 100

# Create an Empty image with white background
im = 255 * np.ones(shape=[sz, sz, 3], dtype=np.uint8)

# Draw shapes
im = cv2.polylines(
    img=im,
    pts=[np.int32([
        [of, of], 
        [sh, of + of], 
        [sz - of, of],
        [sz-of-of,sh],
        [sz-of,sz-of],
        [sh,sz-of-of],
        [of,sz-of],
        [of+of,sh]])],
    isClosed=True,
    color=(128, 0, 200),
    thickness=30,
    lineType=cv2.LINE_AA,  # Anti-Aliased
)
'''

def thickness(defs,min=-1):
    r=round(random.randint(1,100)/10)
    return max(min,r-5)

def color(defs):
    if random.randint(0,10)>5:
        return defs['fg_color']
    return random.choice([color for color in defs['colors'] if color not in [defs['fg_color'],defs['bg_color']]])

distribtions=library([
    item(cb=distribute_solo,must={} ),
    item(cb=distribute_line,must={}),
],{'thickness':lambda defs:thickness(defs)})


shapes=library([
  shape(cb=cv2.rectangle,must={'pt1':('pt','pt1'),'pt2':('pt','pt2'),'color':('',lambda defs:color(defs)),'thickness':('',lambda defs:thickness(defs))}),
    line(cb=cv2.line,must={'pt1':('pt','pt1'),'pt2':('pt','pt2'),'color':('',lambda defs:color(defs)),'thickness':('',lambda defs:thickness(defs,min=1))}),
    shape(cb=cv2.circle,must={'center':('pt','pt1'),'radius':('pt',lambda defs:random.randint(1, round(max(defs['global_width'],defs['global_height'])/2))),'color':('',lambda defs:color(defs)),'thickness':('',lambda defs:thickness(defs))}),
polyline(cb=cv2.polylines,must={'pts':('pt','pts'),'isClosed':('',False),'lineType':('',cv2.LINE_AA),'color':('',lambda defs:color(defs)),'thickness':('',lambda defs:thickness(defs,min=1))}),
],{
    'pt1':lambda defs:(random.randint(1, defs['global_height']), random.randint(1, defs['global_width'])),
'pt2':lambda defs:(random.randint(1, defs['global_height']), random.randint(1, defs['global_width']))
})

def create_image(x,y,seed=None,output='show'):
    random.seed(seed,version=2)

    img= np.ones(shape=(y, x, 3))
    locked=[]
    pallete=random.choice([item for item in dir(pat) if not item.startswith("__") and item[0].isupper() ])
    #pallete=getattr(sys.modules['palettable.matplotlib'], pallete)
    pallete = getattr(sys.modules['palettable.wesanderson'], pallete)

    img[:]=random.choice(list(pallete.mpl_colors))
    defs = dict(img=img,global_width=y,global_height=x,colors=pallete.mpl_colors,fg_color=random.choice(list(pallete.mpl_colors)), bg_color=random.choice(list(pallete.mpl_colors)))
    distribtions.prepare(defs, locked)
    distribtions.run(defs,locked)
    plt.axis('off')
    if output=="io":
        f = io.BytesIO()

        plt.imsave(f,arr=defs['img'], format="png")
        contents = f.getvalue()
        #f.close()
        return contents,f,plt
    elif output == "file":
        plt.imsave("f.png",arr=defs['img'], format="png")
        #plt.savefig("file.png", format="png")
    elif output=="base64":
        f = io.BytesIO()
        plt.savefig(f, format="png", facecolor=(1, 1, 1))
        encoded_img = base64.b64encode(f.getvalue()).decode('utf-8').replace('\n', '')
        f.close()
        return encoded_img
    elif output=='show':
        plt.imshow(defs['img'])
        plt.show()
    else:
        plt.imsave(output,arr=defs['img'], format="png")

