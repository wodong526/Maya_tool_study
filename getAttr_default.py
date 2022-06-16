#api方法
import pymel.core as pm
import maya.OpenMaya as om

pm_node = pm.ls(sl = 1)[0]
api_node = pm_node.__apimobject__()

node_n = om.MFnDependencyNode(api_node)
plug_n = node_n.findPlug('aaa')

numFn = om.MFnNumericAttribute(plug_n.attribute())

float_tul = om.MScriptUtil()
u_ptr = float_tul.asDoublePtr()
numFn.getDefault(u_ptr)
print om.MScriptUtil.getDouble(u_ptr)


#cmds方法
import maya.cmds as mc

print mc.attributeQuery('aaa', n = mc.ls(sl = 1)[0], ld = 1)
print mc.addAttr('nurbsCircle1.aaa', q = 1, dv = 1)