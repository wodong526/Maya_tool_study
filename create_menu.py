import maya.cmds as mc
import pymel.core as pm

def createMenu():
    if mc.menu(my_menu, ex = True):
        mc.deleteUI(my_menu)
    myWindow = pm.language.melGlobals['gMainWindow']
    my_menu = pm.menu(to = True, l = '~菜单~', p = myWindow)
    pm.menuItem(to = 1, p = my_menu, l = '菜单一', c = 'print "发生什么事了"')
pmc.general.evalDeferred('createMenu()')
