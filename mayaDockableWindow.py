#conding=gbk
from PySide2 import QtWidgets
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.cmds as mc

from PySide2 import QtWidgets
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

class MyDockableWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):

    def __init__(self, objname):
        super(MyDockableWindow, self).__init__()        

        self.setWindowTitle('My Dockable Window')
        self.resize(500, 400)
        self.setObjectName(objname)

objname = 'ssa'#窗口的objname，不指定则会每次随机生成一个，且窗口会新建立，不能保证窗口唯一
try:
    #由于窗口唯一，所以要先删除原有窗口，否则报错对象名称不唯一，删除时必须objname加'WorkspaceControl'
    mc.deleteUI('{}WorkspaceControl'.format(objname))
except:
    pass
finally:
    my_window = MyDockableWindow(objname)
    my_window.show(dockable=True)