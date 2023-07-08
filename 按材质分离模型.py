import maya.cmds as mc

def matObj(obj):
    obj_p = mc.listRelatives(obj, p = 1)
    shap_node = mc.listRelatives(obj, shapes = True)
    dest = mc.listConnections(shap_node[0], s = False, t = "shadingEngine")
    mc.select(dest, r = True, ne = True)
    shadingGrp = mc.ls(sl = True)
    
    mc.group(em = True, n = '{}_shadingGrp'.format(obj))
    for i in range(len(shadingGrp)):
        mat_node = mc.listConnections(shadingGrp[i], d = False)
        dup_name = '{}_{}'.format(obj, mat_node[0])
        mc.duplicate(obj, n = dup_name)
        mc.parent(dup_name, '{}_shadingGrp'.format(obj))
        mc.select(dup_name)
        mc.ConvertSelectionToContainedFaces()
        sets = mc.sets()
        mat_gs = mc.listConnections(mat_node, t = 'shadingEngine')
        print mat_gs
        if mat_gs[0] == 'initialParticleSE':
            mat_gs[0] = mat_gs[-1]
        mc.select(mc.sets(mat_gs[0], int = sets))
        mc.InvertSelection()
        mc.delete()
        mc.delete(sets)
    mc.delete(obj)
    if obj_p:
        mc.parent('{}_shadingGrp'.format(obj), obj_p)
    
for obj_trs in mc.ls(sl = 1):
    matObj(obj_trs)

