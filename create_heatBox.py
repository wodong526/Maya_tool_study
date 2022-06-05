import maya.cmds as mc
import pymel.core as pm

redBox_name = 'haha'
class redBox(object):
    def __init__(self):
        self._removeOld()
        self._build()
    
    def _removeOld(self):
        if mc.popupMenu(redBox_name, ex = 1):
            mc.deleteUI(redBox_name)
            
    def _build(self):
        menu = mc.popupMenu(redBox_name, mm = 1, b = 1, aob = 1, ctl = 1, alt = 1, sh = 0, p = 'viewPanes', pmo = 1, pmc = self._buildMenu)
    
    def _buildMenu(self, menu, *args):
        mc.popupMenu(redBox_name, e = True, dai = True)
        
        mc.menuItem(p = menu, l = '方向', c = 'print "Ì«"')
        mc.menuItem(p = menu, l = '下沉', rp = 'N', c = pm.Callback(pm.mel.eval, 'print "hello";'))

redBox()
