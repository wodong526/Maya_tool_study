import maya.cmds as mc
import maya.mel as mm

def create_ctl(nam):
    with open('{}{}.cs'.format('C:/Rig_Tools/tools/data/ControllerFiles/', 'C01'), 'r') as f:
        con = f.read()
    trs = mc.createNode('transform', n=nam)
    mc.createNode('nurbsCurve', p=trs, n='{}Shape'.format(trs))
    mm.eval(con)
    return trs

def createRibbon(nam, ctl_n, jnt_n):
    sel_lis = mc.ls(sl=True)
    for cvr in sel_lis:
        mc.rebuildCurve(cvr, rpo=True, end=1, kr=0, kt=False, s=ctl_n-1)
    surf = mc.loft(sel_lis[0], sel_lis[1], ch=False, u=True, rn=False, po=0, n='surf_{}_{:03d}'.format(nam, 1))[0]
    mc.setAttr('{}.inheritsTransform'.format(surf), False)

    crvFromSur = mc.createNode('curveFromSurfaceIso', n='crvFromSur_{}_{:03d}'.format(nam, 1))
    mc.setAttr('{}.isoparmValue'.format(crvFromSur), 0.5)
    mc.setAttr('{}.isoparmDirection'.format(crvFromSur), 1)
    lsoShape = mc.createNode('nurbsCurve', n='crv_{}_{:03d}Shape'.format(nam, 1))
    lso = mc.rename(mc.listRelatives(lsoShape, p=True), 'crv_{}_{:03d}'.format(nam, 1))
    mc.setAttr('{}.v'.format(lso), False)
    mc.connectAttr('{}.worldSpace[0]'.format(surf), '{}.inputSurface'.format(crvFromSur))
    mc.connectAttr('{}.outputCurve'.format(crvFromSur), '{}.create'.format(lsoShape))

    motPath_node = mc.createNode('motionPath', n='motPath_{}_{:03d}'.format(nam, 1))
    mc.setAttr('{}.fractionMode'.format(motPath_node), 1)
    mc.connectAttr('{}.worldSpace[0]'.format(lsoShape), '{}.geometryPath'.format(motPath_node))
    jnt_lis = []
    for i in range(1, jnt_n+1):
        mc.select(cl=True)
        jnt = mc.joint(n='jnt_{}_{:03d}'.format(nam, i))
        mc.connectAttr('{}.allCoordinates'.format(motPath_node), '{}.translate'.format(jnt))
        mc.setAttr('{}.uValue'.format(motPath_node), (i-1)/(jnt_n-1.0))
        mc.disconnectAttr('{}.allCoordinates'.format(motPath_node), '{}.translate'.format(jnt))
        mc.makeIdentity(jnt, a=True, r=True)
        if jnt_lis:
            mc.parent(jnt, jnt_lis[-1])
        jnt_lis.append(jnt)

    grp_lis = []
    ctl_lis = []
    ctlJnt_lis = []
    for i in range(1, ctl_n + 1):
        ctl = create_ctl('ctl_{}_{:03d}'.format(nam, i))
        grp = mc.group(em=True, n='zero_{}_{:03d}'.format(nam, i), w=True)
        grpOffset = mc.group(em=True, p=grp, n='Offset_{}_{:03d}'.format(nam, i))
        mc.select(cl=True)
        ctlJnt = mc.joint(n='jnt_ctl_{}_{:03d}'.format(nam, i))
        mc.setAttr('{}.v'.format(ctlJnt), False)
        mc.parent(ctl, grpOffset)
        mc.parent(ctlJnt, ctl)
        grp_lis.append(grp)
        ctl_lis.append(ctl)
        ctlJnt_lis.append(ctlJnt)

        mc.connectAttr('{}.allCoordinates'.format(motPath_node), '{}.translate'.format(grp))
        mc.setAttr('{}.uValue'.format(motPath_node), (i - 1) / (ctl_n - 1.0))
        mc.disconnectAttr('{}.allCoordinates'.format(motPath_node), '{}.translate'.format(grp))

    mc.joint(jnt_lis[0], e=True, oj='xyz', sao='yup', zso=True, ch=True)
    ikHad = mc.ikHandle(sj=jnt_lis[0], ee=jnt_lis[-1], c=lso, sol='ikSplineSolver', ccv=False,
                        n='ikHad_{}_{:03d}'.format(nam, 1))[0]
    surSkin = mc.skinCluster(ctlJnt_lis, surf, n='skin_{}_{:03d}'.format(nam, 1))[0]

    grp_main = mc.group(n='grp_{}_001'.format(nam), w=True, em=True)
    mc.parent(ikHad, jnt_lis[0], grp_lis, surf, lso, grp_main)


    cvr_info = mc.createNode('curveInfo', n='cvrInfo_{}_{:03d}'.format(nam, 1))
    mc.connectAttr('{}.worldSpace[0]'.format(lsoShape), '{}.inputCurve'.format(cvr_info))
    cvr_length = mc.getAttr('{}.arcLength'.format(cvr_info))

    mult_node = mc.createNode('multiplyDivide', n='mult_{}_cvrLength_{:03d}'.format(nam, 1))
    mc.setAttr('{}.operation'.format(mult_node), 2)
    mc.setAttr('{}.input2X'.format(mult_node), cvr_length)
    mc.connectAttr('{}.arcLength'.format(cvr_info), '{}.input1X'.format(mult_node))

    for i in range(len(jnt_lis)-1):
        mc.connectAttr('{}.outputX'.format(mult_node), '{}.scaleX'.format(jnt_lis[i]))

createRibbon('Head_Pipe_A', 4, 10)