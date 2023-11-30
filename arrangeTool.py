# coding:gbk
# *******************************************
# 作者: 我東
# mail:wodong526@dingtalk.com
# time:2022/3/19
# 版本：V1.3
# ******************************************
from PySide2 import QtGui
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.cmds as mc
import maya.OpenMaya as om


edition = 'V1.3'  # 版本号


def maya_main_window():
    main_window_par = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_par), QtWidgets.QWidget)


class PlaceObj(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(PlaceObj, self).__init__(parent)

        self.setWindowTitle(u'東牌排布工具.{}'.format(edition))
        self.setMinimumWidth(250)
        self.setMinimumHeight(150)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)  # 去除窗口上的问号

        self.crea_widgets()
        self.crea_layouts()
        self.crea_connections()

    def crea_widgets(self):
        self.but_getObj = QtWidgets.QPushButton(u'获取物体')
        self.but_getObj.setFont(QtGui.QFont('黑体', 15))
        
        self.but_run = QtWidgets.QPushButton(u'排  布')
        self.but_run.setFont(QtGui.QFont('黑体', 20))
        self.but_run.setMinimumSize(80,50)
        self.but_run.setEnabled(False)
        
        self.but_undo = QtWidgets.QPushButton()
        self.but_undo.setMaximumSize(40, 50)
        self.but_undo.setIcon(QtGui.QIcon(':undo.png'))
        self.but_undo.setToolTip(u'回归物体原始位置')
        
        self.lab_wid_ivl = QtWidgets.QLabel(u'横向间隔:')
        self.lab_wid_ivl.setFont(QtGui.QFont('黑体', 9))
        self.lab_wid_ivl.setMinimumSize(50,30)
        
        self.lab_hgt_ivl = QtWidgets.QLabel(u'竖向间隔')
        self.lab_hgt_ivl.setFont(QtGui.QFont('黑体', 9))
        self.lab_hgt_ivl.setMinimumSize(50, 30)
        
        self.lab_num = QtWidgets.QLabel(u'每行个数:')
        self.lab_num.setFont(QtGui.QFont('黑体', 9))
        self.lab_num.setMinimumSize(50,30)
        
        self.dsbox_hgt_ivl = QtWidgets.QDoubleSpinBox()
        self.dsbox_hgt_ivl.setMinimumHeight(20)
        self.dsbox_hgt_ivl.setFont(QtGui.QFont('黑体', 10))
        self.dsbox_hgt_ivl.setSingleStep(0.01)
        self.dsbox_hgt_ivl.setMinimum(-999)
        
        self.dsbox_wid_ivl = QtWidgets.QDoubleSpinBox()
        self.dsbox_wid_ivl.setMinimumHeight(20)
        self.dsbox_wid_ivl.setFont(QtGui.QFont('黑体', 10))
        self.dsbox_wid_ivl.setSingleStep(0.01)
        self.dsbox_wid_ivl.setMinimum(-999)
        
        self.spbox_num = QtWidgets.QSpinBox()
        self.spbox_num.setMinimumHeight(20)
        self.spbox_num.setFont(QtGui.QFont('黑体', 10))
        self.spbox_num.setMinimum(1)
        self.spbox_num.setMaximum(9999)
        
        radBut_lis = [u'+xy', u'+xz', u'+zy']
        self.radBut_dir = {}
        for inf in radBut_lis:
            rad_but = QtWidgets.QRadioButton()
            rad_but.setText(inf)
            rad_but.setFont(QtGui.QFont('黑体', 15))
            self.radBut_dir[inf] = rad_but
        self.radBut_dir[u'+xy'].setChecked(True)

    def crea_layouts(self):
        rad_layout = QtWidgets.QHBoxLayout()
        rad_layout.addWidget(self.but_getObj)
        rad_layout.addWidget(self.radBut_dir[u'+xy'])
        rad_layout.addWidget(self.radBut_dir[u'+xz'])
        rad_layout.addWidget(self.radBut_dir[u'+zy'])
        
        run_layout = QtWidgets.QHBoxLayout()
        run_layout.addWidget(self.but_run)
        run_layout.addWidget(self.but_undo)
        
        hgt_layout = QtWidgets.QHBoxLayout()
        hgt_layout.addWidget(self.lab_hgt_ivl)
        hgt_layout.addWidget(self.dsbox_hgt_ivl)
        
        wid_layout = QtWidgets.QHBoxLayout()
        wid_layout.addWidget(self.lab_wid_ivl)
        wid_layout.addWidget(self.dsbox_wid_ivl)
        
        ivl_layout = QtWidgets.QVBoxLayout()
        ivl_layout.addLayout(hgt_layout)
        ivl_layout.addLayout(wid_layout)
        
        num_layout = QtWidgets.QHBoxLayout()
        num_layout.addWidget(self.lab_num)
        num_layout.addWidget(self.spbox_num)
        num_layout.addLayout(ivl_layout)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(rad_layout)
        main_layout.addLayout(num_layout)
        main_layout.addLayout(run_layout)
        
    def crea_connections(self):
        self.but_getObj.clicked.connect(self.get_sel_lis)
        self.but_run.clicked.connect(self.crea_run)
        self.but_undo.clicked.connect(self.crea_undo)

    def crea_undo(self):
        for inf in self.sel_position.keys():
            mc.setAttr('{}.translate'.format(inf), self.sel_position[inf][0], self.sel_position[inf][1], self.sel_position[inf][2])
    
    def crea_run(self):
        if int(self.spbox_num.value()) > len(self.sel_nem_lis):
            mc.warning('每行个数超出所选择的物体个数。')
            return False
        
        sel_bbox_lis = []
        [sel_bbox_lis.append(mc.xform(inf, bb = True, q = True)) for inf in self.sel_nem_lis]

        self.sel_dir = {}
        for inf in range(len(sel_bbox_lis)):
            self.sel_dir[self.sel_nem_lis[inf]] = sel_bbox_lis[inf]
        
        obj_lis = self.get_sort_lis(self.sel_dir, self.if_redBool())#整数行列的物体
        ivl_num = float(self.dsbox_wid_ivl.value())                 #横向间隔距离
        hg_num  = float(self.dsbox_hgt_ivl.value())                 #竖向间隔距离
        col_num = int(self.spbox_num.value())                       #列数
        row_num = int(len(self.sel_nem_lis) / col_num)              #行数
        row_hgt = self.crea_sort(obj_lis, row_num, col_num, hg_num) #物体的高度值
        
        obj_abs = self.get_absolutely_position()
        if self.if_redBool() == '+xy':
            obj_n = 0
            for row in range(row_num):
                move_x = 0
                for col in range(col_num):
                    if col == 0:
                        if row == 0:
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), obj_abs[obj_lis[obj_n][0]][1] * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                            mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                            #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), hgt[0], hgt[1], hgt[2])
                        else:
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), (obj_abs[obj_lis[obj_n][0]][1] - row_hgt[row]) * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                            mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                            #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), hgt[0], hgt[1], hgt[2])
                        move_x = obj_lis[obj_n][2] + ivl_num
                        obj_n += 1
                    else:
                        if row == 0:
                            hgt = [((obj_abs[obj_lis[obj_n][0]][0] - (move_x + obj_lis[obj_n][2])) * -1), obj_abs[obj_lis[obj_n][0]][1] * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                        else:
                            hgt_num = row_hgt[row]
                            hgt = [(obj_abs[obj_lis[obj_n][0]][0] - (move_x + obj_lis[obj_n][2])) * (-1), (obj_abs[obj_lis[obj_n][0]][1] - hgt_num) * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                        mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                        #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), move_x + obj_lis[obj_n][2], hgt_num, 0)
                        move_x = mc.getAttr("{}.translateX".format(obj_lis[obj_n][0])) + obj_lis[obj_n][2] + ivl_num
                        obj_n += 1
            
            rema_obj = obj_lis[:]
            for n in range(col_num * row_num):
                del rema_obj[0]
            if len(rema_obj) > 0:
                rema_hgt = row_hgt[-1] + obj_lis[obj_n - 1][3] / 2 + rema_obj[-1][3] / 2 + hg_num
                rema_moveX = 0
                for inf in range(len(rema_obj)):
                    hgt = [obj_abs[rema_obj[inf][0]][0] * (-1), (obj_abs[rema_obj[inf][0]][1] - rema_hgt) * (-1), obj_abs[rema_obj[inf][0]][2] * (-1)]
                    if inf == 0:
                        mc.move(hgt[0], hgt[1], hgt[2], rema_obj[inf][0], r = True)
                        #mc.setAttr('{}.translate'.format(rema_obj[inf][0]), 0, rema_hgt, 0)
                        rema_moveX = rema_obj[inf][2] + ivl_num
                    else:
                        mc.move((obj_abs[rema_obj[inf][0]][0] - (rema_moveX + rema_obj[inf][2])) * (-1), hgt[1], hgt[2], rema_obj[inf][0], r = True)
                        #mc.setAttr('{}.translate'.format(rema_obj[inf][0]), rema_moveX + rema_obj[inf][2], rema_hgt, 0)
                        rema_moveX = mc.getAttr('{}.translateX'.format(rema_obj[inf][0])) + rema_obj[inf][2] + ivl_num
        
        elif self.if_redBool() == '+xz':
            obj_n = 0
            for row in range(row_num):
                move_x = 0
                for col in range(col_num):
                    if col == 0:
                        if row == 0:
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), obj_abs[obj_lis[obj_n][0]][1] * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                            mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                            #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), hgt[0], hgt[1], hgt[2])
                        else:
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), obj_abs[obj_lis[obj_n][0]][1] * (-1), (obj_abs[obj_lis[obj_n][0]][2] - row_hgt[row]) * (-1)]
                            mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                            #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), hgt[0], hgt[1], hgt[2])
                        move_x = obj_lis[obj_n][2] + ivl_num
                        obj_n += 1
                    else:
                        if row == 0:
                            hgt = [((obj_abs[obj_lis[obj_n][0]][0] - (move_x + obj_lis[obj_n][2])) * -1), obj_abs[obj_lis[obj_n][0]][1] * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                        else:
                            hgt_num = row_hgt[row]
                            hgt = [(obj_abs[obj_lis[obj_n][0]][0] - (move_x + obj_lis[obj_n][2])) * (-1), obj_abs[obj_lis[obj_n][0]][1] * (-1), (obj_abs[obj_lis[obj_n][0]][2] - hgt_num) * (-1)]
                        mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                        #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), move_x + obj_lis[obj_n][2], hgt_num, 0)
                        move_x = mc.getAttr("{}.translateX".format(obj_lis[obj_n][0])) + obj_lis[obj_n][2] + ivl_num
                        obj_n += 1
            
            rema_obj = obj_lis[:]
            for n in range(col_num * row_num):
                del rema_obj[0]
            if len(rema_obj) > 0:
                rema_hgt = row_hgt[-1] + obj_lis[obj_n - 1][3] / 2 + rema_obj[-1][3] / 2 + hg_num
                rema_moveX = 0
                for inf in range(len(rema_obj)):
                    hgt = [obj_abs[rema_obj[inf][0]][0] * (-1), obj_abs[rema_obj[inf][0]][1] * (-1), (obj_abs[rema_obj[inf][0]][2] - rema_hgt) * (-1)]
                    if inf == 0:
                        mc.move(hgt[0], hgt[1], hgt[2], rema_obj[inf][0], r = True)
                        #mc.setAttr('{}.translate'.format(rema_obj[inf][0]), 0, rema_hgt, 0)
                        rema_moveX = rema_obj[inf][2] + ivl_num
                    else:
                        mc.move((obj_abs[rema_obj[inf][0]][0] - (rema_moveX + rema_obj[inf][2])) * (-1), hgt[1], hgt[2], rema_obj[inf][0], r = True)
                        #mc.setAttr('{}.translate'.format(rema_obj[inf][0]), rema_moveX + rema_obj[inf][2], rema_hgt, 0)
                        rema_moveX = mc.getAttr('{}.translateX'.format(rema_obj[inf][0])) + rema_obj[inf][2] + ivl_num
        
        elif self.if_redBool() == '+zy':
            obj_n = 0
            for row in range(row_num):
                move_x = 0
                for col in range(col_num):
                    if col == 0:
                        if row == 0:
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), obj_abs[obj_lis[obj_n][0]][1] * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                            mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                            #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), 0, 0, 0)
                        else:
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), (obj_abs[obj_lis[obj_n][0]][1] - row_hgt[row]) * (-1), obj_abs[obj_lis[obj_n][0]][2] * (-1)]
                            mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                            #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), 0, row_hgt[row], 0)
                        move_x = obj_lis[obj_n][2] + ivl_num
                        obj_n += 1
                    else:
                        if row == 0:
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), obj_abs[obj_lis[obj_n][0]][1] * (-1), ((obj_abs[obj_lis[obj_n][0]][2] - (move_x + obj_lis[obj_n][2])) * (-1))]
                        else:
                            hgt_num = row_hgt[row]
                            hgt = [obj_abs[obj_lis[obj_n][0]][0] * (-1), (obj_abs[obj_lis[obj_n][0]][1] - hgt_num) * (-1), (obj_abs[obj_lis[obj_n][0]][2] - (move_x + obj_lis[obj_n][2])) * (-1)]
                        mc.move(hgt[0], hgt[1], hgt[2], obj_lis[obj_n][0], r = True)
                        #mc.setAttr('{}.translate'.format(obj_lis[obj_n][0]), 0, hgt_num, move_x + obj_lis[obj_n][2])
                        move_x = mc.getAttr("{}.translateZ".format(obj_lis[obj_n][0])) + obj_lis[obj_n][2] + ivl_num
                        obj_n += 1
            
            rema_obj = obj_lis[:]
            for n in range(col_num * row_num):
                del rema_obj[0]
            if len(rema_obj) > 0:
                rema_hgt = row_hgt[-1] + obj_lis[obj_n - 1][3] / 2 + rema_obj[-1][3] / 2 + hg_num
                rema_moveX = 0
                for inf in range(len(rema_obj)):
                    hgt = [obj_abs[rema_obj[inf][0]][0] * (-1), (obj_abs[rema_obj[inf][0]][1] - rema_hgt) * (-1), obj_abs[rema_obj[inf][0]][2] * (-1)]
                    if inf == 0:
                        mc.move(hgt[0], hgt[1], hgt[2], rema_obj[inf][0], r = True)
                        #mc.setAttr('{}.translate'.format(rema_obj[inf][0]), 0, rema_hgt, 0)
                        rema_moveX = rema_obj[inf][2] + ivl_num
                    else:
                        mc.move(hgt[0], hgt[1], (obj_abs[rema_obj[inf][0]][2] - (rema_moveX + rema_obj[inf][2])) * (-1), rema_obj[inf][0], r = True)
                        #mc.setAttr('{}.translate'.format(rema_obj[inf][0]), 0, rema_hgt, rema_moveX + rema_obj[inf][2])
                        rema_moveX = mc.getAttr('{}.translateZ'.format(rema_obj[inf][0])) + rema_obj[inf][2] + ivl_num
        
    def get_sort_lis(self, obj_dir, axis):
        sort_lis = []
        if axis == '+xy':
            obj_hgt_dir = {}
            obj_wit_dir = {}
            for inf in obj_dir.keys():
                obj_hgt_xy = obj_dir[inf][4] - obj_dir[inf][1]#高度
                obj_wit_xy = obj_dir[inf][3] - obj_dir[inf][0]#宽度
                obj_hgt_dir[inf] = obj_hgt_xy
                obj_wit_dir[inf] = obj_wit_xy
                obj_dir[inf] = obj_wit_xy * obj_hgt_xy
            
            for inf in sorted(obj_dir, key = obj_dir.__getitem__):
                sort_lis.append([inf, obj_wit_dir[inf], obj_wit_dir[inf] / 2, obj_hgt_dir[inf]])

        elif axis == '+xz':
            obj_hgt_dir = {}
            obj_wit_dir = {}
            for inf in obj_dir.keys():
                obj_hgt_xz = obj_dir[inf][5] - obj_dir[inf][2]
                obj_wit_xz = obj_dir[inf][3] - obj_dir[inf][0]
                obj_hgt_dir[inf] = obj_hgt_xz
                obj_wit_dir[inf] = obj_wit_xz
                obj_dir[inf] = obj_wit_xz * obj_hgt_xz
                
            for inf in sorted(obj_dir, key = obj_dir.__getitem__):
                sort_lis.append([inf, obj_wit_dir[inf], obj_wit_dir[inf] / 2, obj_hgt_dir[inf]])

        elif axis == '+zy':
            obj_hgt_dir = {}
            obj_wit_dir = {}
            for inf in obj_dir.keys():
                obj_hgt_zy = obj_dir[inf][4] - obj_dir[inf][1]
                obj_wit_zy = obj_dir[inf][5] - obj_dir[inf][2]
                obj_hgt_dir[inf] = obj_hgt_zy
                obj_wit_dir[inf] = obj_wit_zy
                obj_dir[inf] = obj_wit_zy * obj_hgt_zy
                
            for inf in sorted(obj_dir, key = obj_dir.__getitem__):
                sort_lis.append([inf, obj_wit_dir[inf], obj_wit_dir[inf] / 2, obj_hgt_dir[inf]])
        return sort_lis#获取物体名、物体宽、宽的一半、高

    def crea_sort(self, obj_lis, row, col, height):
        hgt = [0]
        ret_lis = []
        obj_n = 0
        for row_n in range(row):
            obj_max = []
            for col_n in range(col):
                obj_max.append(obj_lis[obj_n])
                obj_n += 1
            ret_lis.append(sorted(obj_max, key = lambda x: x[3], reverse = True)[0])
        
        ret_lis_b = ret_lis[:]
        del ret_lis_b[0]
        for inf in range(len(ret_lis_b)):#从现在开始 求的是从第二行开始的物体的高度
            hgt.append(ret_lis_b[inf][3] / 2 + ret_lis[inf][3] / 2 + hgt[inf] + height)#这一行的最高物体的高度的一半，加上这一行的下一行的物体的高度的一半，加上这一行的下一行的高度
        return hgt
    
    def get_sel_lis(self):
        self.sel_nem_lis = mc.ls(sl = True)
        if not self.sel_nem_lis:
            om.MGlobal.displayError('选择列表为空。')
            return False
        elif self.sel_nem_lis:
            self.but_run.setEnabled(True)
        
        self.sel_position = {}
        for inf in self.sel_nem_lis:
            self.sel_position[inf] = mc.getAttr('{}.translate'.format(inf))[0]

    def if_redBool(self):
        for inf in self.radBut_dir:
            if self.radBut_dir[inf].isChecked() == True:
                return inf
    
    def get_absolutely_position(self):
        obj_abs_dir = {}
        for inf in self.sel_nem_lis:
            bb_lis = mc.xform(inf, ws = True, bb = True, q = True)
            x = round((bb_lis[0] + bb_lis[3]) / 2, 3)
            y = round((bb_lis[1] + bb_lis[4]) / 2, 3)
            z = round((bb_lis[2] + bb_lis[5]) / 2, 3)
            obj_abs_dir[inf] = [x, y, z]
        
        return obj_abs_dir

    def wnd_close(self):
        self.close()
        self.deleteLater()
    


if __name__ == '__main__':
    try:
        a.wnd_close()
    except:
        pass

    a = PlaceObj()
    a.show()