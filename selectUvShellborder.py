import maya.cmds as mc
import maya.api.OpenMaya as om

def get_border(dag):
    edge_set = set()
    mit = om.MItMeshEdge(dag.node())
    while not mit.isDone():
        if mit.onBoundary():
            edge_set.add('{}.e[{}]'.format(dag.fullPathName(), mit.index()))
        else:
            i = mit.index()
            uvs = mc.ls(mc.polyListComponentConversion('{}.e[{}]'.format(dag.fullPathName(), i), tuv=1), fl=1)
            if uvs.__len__() > 2:
                edge_set.add('{}.e[{}]'.format(dag.fullPathName(), mit.index()))
        mit.next()
    return edge_set

edge_border_set = set()
sel = om.MGlobal.getActiveSelectionList()
for i in range(sel.length()):
    dag = om.MDagPath()
    dag = sel.getDagPath(i)
    dag.extendToShape()
    
    edge_border_set = get_border(dag).symmetric_difference(edge_border_set)
mc.select(list(edge_border_set))