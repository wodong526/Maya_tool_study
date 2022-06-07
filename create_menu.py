import maya.cmds as mc
import pymel.core as pm

def createMenu():
    if mc.menu(my_menu, ex = True):
        mc.deleteUI(my_menu)
    myWindow = pm.language.melGlobals['gMainWindow']
    my_menu = pm.menu(to = True, l = '~萌萌菜单栏~', p = myWindow)
    pm.menuItem(to = 1, p = my_menu, l = '菜单1', c = 'print "菜单一"')
pmc.general.evalDeferred('createMenu()')
