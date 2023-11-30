# coding:gbk
# *******************************************
# 作者: 我東
# mail:wodong526@dingtalk.com
# time:2022/2/1
# 版本：V1.2
# ******************************************

from PySide2 import QtGui
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import os
from functools import partial
import re

edition = 'V1.2'    #版本号

def maya_main_window():
    main_window_par = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_par), QtWidgets.QWidget)


class MyTextEdit(QtWidgets.QTextEdit):
    '''
    重写textEdit控件的键盘回车信号，包括小键盘回车
    '''
    enter_pressed = QtCore.Signal(str)

    def keyPressEvent(self, e):
        super(MyTextEdit, self).keyPressEvent(e)

        if e.key() == QtCore.Qt.Key_Enter:
            self.enter_pressed.emit(u'得数为：')

        elif e.key() == QtCore.Qt.Key_Return:
            self.enter_pressed.emit(u'得数为：')


class Calculator(QtWidgets.QDialog):
    def __init__(self, parent = maya_main_window()):
        super(Calculator, self).__init__(parent)

        self.setWindowTitle(u'東牌计算机.{}'.format(edition))
        self.setMinimumWidth(330)
        self.setMinimumHeight(640)

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)  # 去除窗口上的问号
        self.setFixedSize(self.width(), self.height())

        self.crea_widgets()
        self.crea_layouts()
        self.crea_connections()

    def crea_widgets(self):
        self.input_tex = MyTextEdit()
        self.input_tex.setFixedSize(310, 100)
        self.input_tex.setFont(QtGui.QFont('黑体', 30))

        self.output_tex = QtWidgets.QTextEdit()
        self.output_tex.setFixedSize(310, 60)
        self.output_tex.setFont(QtGui.QFont('黑体', 30))
        self.output_tex.setReadOnly(True)#不允许在输出框内手动输入

        #循环放置0到9的按钮
        for inf in range(10):
            exec('self.but_{} = QtWidgets.QPushButton(u"{}")'.format(inf, inf))
            exec('self.but_{}.setFixedSize(70, 70)'.format(inf))
            exec('self.but_{}.setFont(QtGui.QFont("黑体", 60))'.format(inf))

        #循环放置运算符和括号按钮
        self.operator_dir = {'plus'     : '+',
                             'reduce'   : '-',
                             'ride'     : '*',
                             'except'   : '/',
                             'decimal'  : '.',
                             'bracket_f': '(',
                             'bracket_b': ')'}
        for inf in self.operator_dir:
            exec('self.but_{} = QtWidgets.QPushButton(u"{}")'.format(inf, self.operator_dir[inf]))
            exec('self.but_{}.setFixedSize(70, 70)'.format(inf))
            exec('self.but_{}.setFont(QtGui.QFont("黑体", 60))'.format(inf))

        self.but_run = QtWidgets.QPushButton(u'=')
        self.but_run.setFixedSize(150, 70)
        self.but_run.setFont(QtGui.QFont('黑体', 60))

        self.but_clos = QtWidgets.QPushButton(u'关闭计算器')
        self.but_clos.setFixedHeight(40)
        self.but_clos.setFont(QtGui.QFont('黑体', 15))
        self.but_copy = QtWidgets.QPushButton(u'复制得数')
        self.but_copy.setFixedHeight(40)
        self.but_copy.setFont(QtGui.QFont('黑体', 15))
        self.but_clear = QtWidgets.QPushButton(u'清除')
        self.but_clear.setFixedHeight(70)
        self.but_clear.setFont(QtGui.QFont('黑体', 20))

    def crea_layouts(self):
        but_top_layout = QtWidgets.QHBoxLayout()
        but_top_layout.addWidget(self.but_clear)
        but_top_layout.addWidget(self.but_bracket_f)
        but_top_layout.addWidget(self.but_bracket_b)
        but_top_layout.addWidget(self.but_ride)

        but_up_layout = QtWidgets.QHBoxLayout()
        but_up_layout.addWidget(self.but_7)
        but_up_layout.addWidget(self.but_8)
        but_up_layout.addWidget(self.but_9)
        but_up_layout.addWidget(self.but_except)

        but_well_layout = QtWidgets.QHBoxLayout()
        but_well_layout.addWidget(self.but_4)
        but_well_layout.addWidget(self.but_5)
        but_well_layout.addWidget(self.but_6)
        but_well_layout.addWidget(self.but_plus)

        but_lower_layout = QtWidgets.QHBoxLayout()
        but_lower_layout.addWidget(self.but_1)
        but_lower_layout.addWidget(self.but_2)
        but_lower_layout.addWidget(self.but_3)
        but_lower_layout.addWidget(self.but_reduce)

        but_end_layout = QtWidgets.QHBoxLayout()
        but_end_layout.addWidget(self.but_0)
        but_end_layout.addWidget(self.but_decimal)
        but_end_layout.addWidget(self.but_run)
        but_end_layout.addWidget(self.but_decimal)

        but_other_layout = QtWidgets.QHBoxLayout()
        but_other_layout.addWidget(self.but_clos)
        but_other_layout.addWidget(self.but_copy)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.input_tex)
        main_layout.addWidget(self.output_tex)
        main_layout.addLayout(but_top_layout)
        main_layout.addLayout(but_up_layout)
        main_layout.addLayout(but_well_layout)
        main_layout.addLayout(but_lower_layout)
        main_layout.addLayout(but_end_layout)
        main_layout.addLayout(but_other_layout)

    def crea_connections(self):
        #循环链接同一个槽，在输入窗口内输入内容
        for inf in range(10):
            exec('self.but_{}.clicked.connect(partial(self.crea_tex, {}))'.format(inf, inf))

        for inf in self.operator_dir:
            exec('self.but_{}.clicked.connect(partial(self.crea_tex, "{}"))'.format(inf, self.operator_dir[inf]))

        #在窗口和键盘上按下的信号都链接到输入槽内
        self.but_run.clicked.connect(self.crea_run)
        self.input_tex.enter_pressed.connect(self.crea_run)

        self.but_copy.clicked.connect(self.crea_clipboard)
        self.but_clear.clicked.connect(self.crea_clear)
        self.but_clos.clicked.connect(self.wnd_close)

    def crea_tex(self, tex):
        old_tex = self.input_tex.toPlainText()

        cursor = self.input_tex.textCursor()
        cru_pos = cursor.position()  # 获取光标位置

        self.input_tex.setText(old_tex[:cru_pos] + str(tex) + old_tex[cru_pos:])#在光标处插入新输入的内容

        cursor.setPosition(cru_pos + 1)
        self.input_tex.setTextCursor(cursor)  # 移动光标到新输入的字符身后

    def crea_run(self, *inf):
        number_str = self.input_tex.toPlainText()#获取输入窗口内容
        if number_str:#如果有内容就计算内容
            str_lis = '0123456789.+-*/()'
            for num_inf in number_str:#查看输入框中是否有非法字符
                if num_inf not in str_lis:
                    print u'您输入的字符中有非法字符{}'.format(num_inf)
                    return False
                else:
                    pass

            number_str = self.brackets(number_str)
            self.output_tex.setText(str(number_str))#并在输出框内填入内容
        else:#如果没有内容就抛出提示
            print u'你的输入框中没有式子。'
            return False

        if inf:#如果是键盘回车信号
            cursor = self.input_tex.textCursor()
            cursor.clearSelection()
            cursor.deletePreviousChar()#使光标位置不变
            print u"{}{}".format(inf[0], number_str)
        else:#如果是窗口按钮‘=’的信号
            print '得数为:{}'.format(number_str)

    def atom_seek(self, seek_str):
        # 算单个乘除并返回这个乘除后的式子，通过拆分乘除号两边的数来重新计算得数
        if "*" in seek_str:
            s1, s2 = seek_str.split("*")
            return str(float(s1) * float(s2))
        elif "/" in seek_str:
            s1, s2 = seek_str.split("/")
            return str(float(s1) / float(s2))

    def mulOrDiv(self, exp):
        #乘除法
        while True:
            exp_res = re.search(r"\d+(\.\d+)?[*/]-?\d+(\.\d+)?", exp)
            if exp_res:
                atom_exp = exp_res.group()
                res = self.atom_seek(atom_exp)
                exp = exp.replace(atom_exp, res)
            else:
                return str(exp)

    def addOrSub(self, exp):
        #加减法
        exp_sum = 0
        while True:
            exp_res = re.findall(r"-?\d+(?:\.\d+)?", exp)
            if exp_res:
                for i in exp_res:
                    exp_sum += float(i)
                return exp_sum

    def brackets(self, exp):
        #循环查找是否有括号
        while True:
            exp_res = re.search(r"\([^()]+\)", exp)#查有没有括号,并把所有的括号提出来
            if exp_res:#当有括号时
                exp_group = exp_res.group()#括号的内容，包括括号
                new_num = self.mulOrDiv(exp_group)
                new_num = self.addOrSub(new_num)
                exp = exp.replace(exp_group, str(new_num))#把括号外的字符和括号算出的内容重新组合
            else:#如果没有括号 则直接抛出计算结果
                num = self.mulOrDiv(exp)
                num = self.addOrSub(num)
                return num

    def crea_clear(self):
        #清空输入框，如果想双击清空输出框得重写按钮，或者根据两次点击时差判断是否双击，这里没写
        self.input_tex.clear()

    def crea_clipboard(self):
        #用os模块把得数粘贴到windows的粘贴板
        tex = self.output_tex.toPlainText()
        com = 'echo | set /p unl = ' + tex.strip() + '| clip'
        os.system(com)
        print '得数{}已复制到粘贴板。'.format(tex)

    def wnd_close(self):
        self.close()
        print '计算器关闭。'
        self.deleteLater()


if __name__ == '__main__':
    try:
        a.wnd_close()
    except:
        pass

    a = Calculator()
    a.show()