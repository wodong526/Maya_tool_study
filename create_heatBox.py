import maya.cmds as mc

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
        
        mc.menuItem(p = menu, l = '下沉', c = 'print "ss"')
        mc.menuItem(p = menu, l = '方向', rp = 'N', c = 'print "ll"')
        subMenu = mc.menuItem(p = menu, l = '子菜单', rp = 'E', subMenu = 1)
        mc.menuItem(p = subMenu, l = '发生什么事了', rp = 'NE', c = 'print "发生什么事了",')

redBox()