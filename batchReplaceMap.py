#coding:gbk

#*******************************************
#作者: 我東
#mail:wodong526@dingtalk.com
#time:2021/11/17
#版本：V1.6
#******************************************

import os
from PySide2 import QtCore, QtGui, QtWidgets
import shiboken2
import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omUI

edition = 'V1.6'    #版本号

def get_maya_parentUi():
    ptr = omUI.MQtUtil.mainWindow()
    if ptr:
        widget = shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
        return widget
class select_file(object):
    def get_mesh(self):
        sel = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(sel)

        sel_dag_node = om.MDagPath()
        sel.getDagPath(0, sel_dag_node)

        sel_fn_dag_path = om.MFnDagNode(sel_dag_node)
        sel_mesh = None
        for i in range(sel_fn_dag_path.childCount()):
            child_obj = sel_fn_dag_path.child(i)
            child_fn_dag_path = om.MFnDagNode(child_obj)
            if child_fn_dag_path.typeName() == 'mesh':
                sel_mesh = child_obj
                break
        return sel_mesh

    def get_shadingNode(self, mobject):
        shading = None
        mit_nodes = om.MItDependencyGraph(mobject, om.MFn.kShadingEngine)

        while not mit_nodes.isDone():
            it = mit_nodes.currentItem()
            shading = om.MFnDependencyNode(it)
            mit_nodes.next()
        shading_node = shading.object()
        return shading_node

    def get_fileNode(self, shading):
        file_l = list()
        mit_nodes = om.MItDependencyGraph(shading, om.MFn.kFileTexture,
                                          om.MItDependencyGraph.kUpstream,
                                          om.MItDependencyGraph.kBreadthFirst,
                                          om.MItDependencyGraph.kNodeLevel)
        while not mit_nodes.isDone():
            it = mit_nodes.currentItem()
            file_node = om.MFnDependencyNode(it)
            file_l.append(file_node)
            mit_nodes.next()

        #阿诺德aiImage
        ai_node_l = list()
        dg_mod = om.MDGModifier()
        aiImage_type = om.MTypeId(om.MFnDependencyNode(dg_mod.createNode('aiImage')).typeId().id())

        mit_ard_node = om.MItDependencyNodes(om.MFn.kPluginDependNode)#这里使用MItDependencyGraph也可以，指定好kInvalid类型就可以
        while not mit_ard_node.isDone():
            aiFile = om.MFnDependencyNode(mit_ard_node.thisNode())
            if aiFile.typeId() == aiImage_type:
                ai_node_l.append(aiFile)
            mit_ard_node.next()
        return file_l, ai_node_l

    def set_plug(self, file_node_l, new_path):
        s_tex_p = str(new_path)
        s_tex_p.replace('\\', '/', 100)
        for f_nod in file_node_l[0]:
            tex_plug = f_nod.findPlug('fileTextureName')
            tex_nm = os.path.basename(tex_plug.asString())
            tex_plug.setString('{}/{}'.format(s_tex_p, tex_nm))

        for aif_nod in file_node_l[1]:
            ai_tex_plug = aif_nod.findPlug('filename')
            ai_tex_nm = os.path.basename(ai_tex_plug.asString())
            ai_tex_plug.setString('{}/{}'.format(s_tex_p, ai_tex_nm))

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(398, 213)
        MainWindow.setWindowTitle(u"東牌贴图替换工具.{}".format(edition))
        MainWindow.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        MainWindow.setAnimated(True)
        MainWindow.setDocumentMode(False)
        MainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)
        MainWindow.setDockNestingEnabled(True)
        MainWindow.setDockOptions(QtWidgets.QMainWindow.AllowNestedDocks|QtWidgets.QMainWindow.AllowTabbedDocks|QtWidgets.QMainWindow.AnimatedDocks)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setMaximumSize(QtCore.QSize(16777215, 100))
        self.label.setSizeIncrement(QtCore.QSize(0, 0))
        self.label.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setWeight(75)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setText("")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(19)
        self.lineEdit.setFont(font)
        self.lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit.setPlaceholderText("")
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setMinimumSize(QtCore.QSize(40, 40))
        self.pushButton_2.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setEnabled(True)
        self.pushButton.setMinimumSize(QtCore.QSize(0, 0))
        self.pushButton.setMaximumSize(QtCore.QSize(16777215, 50))
        self.pushButton.setSizeIncrement(QtCore.QSize(0, 0))
        self.pushButton.setBaseSize(QtCore.QSize(1, 0))
        font = QtGui.QFont()
        font.setPointSize(23)
        font.setWeight(75)
        font.setStrikeOut(False)
        font.setBold(True)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        self.pushButton.setText(QtWidgets.QApplication.translate("MainWindow", "<<  RUN  >>", None, -1))

class createUi(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent = get_maya_parentUi()):
        super(createUi, self).__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.change_tex)
        self.pushButton_2.setToolTip(u'选择新贴图文件路径')
        self.pushButton_2.clicked.connect(self.open_path)
        self.label.setText(u'先复制新的贴图路径\n再点击RUN')
        self.lineEdit.setPlaceholderText(u'粘贴新的路径到这里')

    def open_path(self):
        file_path = QtWidgets.QFileDialog.getExistingDirectory(self, u'新路径选择窗口', '{}/images'.format(mc.workspace(q = 1, rd = 1)))
        self.lineEdit.setText(file_path)

    def change_tex(self):
        new_path = r'{}'.format(self.lineEdit.text())
        if os.path.exists(new_path) == False:
            om.MGlobal.displayError(u'加载的路径无效。')
            return False

        may_run = select_file()
        try:
            sel_mesh = may_run.get_mesh()
            sel_shading = may_run.get_shadingNode(sel_mesh)
        except:
            om.MGlobal.displayError(u'请选择有效的节点。')
            return False
        else:
            sel_file = may_run.get_fileNode(sel_shading)
            may_run.set_plug(sel_file, new_path)


try:
    wnd.close()
    wnd.deleteLater()
except:
    pass

wnd = createUi()
wnd.show()
