import maya.cmds as mc
import os

exp_path = r""
obj = mc.ls(sl = 1)[0]
sn_path = mc.file(q = 1, sn = 1)

obj_path = exp_path + '\\' + obj + '.fbx'
mc.file(obj_path, es = 1, typ = 'FBX export', f = 1)

mc.file(f = 1, new = 1)
mc.file(obj_path, typ = 'FBX', i = 1)
obj_bs = mc.ls(typ = 'blendShape')
if len(obj_bs) != 1:
    mc.error('文件中不止一个bs')
else:
    a = mc.aliasAttr(obj_bs, q = 1)
    for inf in a:
        try:
            mc.nodeType(inf) == 'transform'
        except:
            pass
        else:
            obj_shap = mc.listRelatives(inf, s = 1)[0]
            mc.select(inf, r = 1)
            shap_path = exp_path + '\\' + obj_shap
            mc.file(shap_path, es = 1, typ = 'OBJexport', f = 1)
            print '已导出BS模型{}'.format(inf),
if sn_path:
    mc.file(sn_path, o = 1)
    os.remove(obj_path)
