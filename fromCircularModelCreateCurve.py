#选模型开口处的环形边运行

import maya.cmds as mc
import maya.mel as mm

def get_pos(pit_lis):

    pos_lis = []
    for obj in pit_lis:
        pos_lis.append(mc.xform(obj, ws=True, q=True, t=True))

    crv = mc.curve(d=1, p=pos_lis)
    clst = mc.cluster()
    loc = mc.spaceLocator()[0]
    mc.matchTransform(loc, clst)
    pos = mc.xform(loc, ws=1, q=1, t=1)
    mc.delete(crv, clst, loc)
    
    return pos

mm.eval('PolySelectConvert 3;')

sel = mc.ls(sl=1, fl=1)
point_lis = [get_pos(sel)]

mc.select(sel)
while True:
    old = mc.ls(sl=1, fl=1)
    mm.eval('PolySelectTraverse 1;')
    new = mc.ls(sl=1, fl=1)

    list3 = [item for item in new if item not in set(old)]
    if list3:
        point_lis.append(get_pos(list3))
        mc.select(new)
        old = new
    else:
        break

mc.curve(d=3, p=point_lis)

    

