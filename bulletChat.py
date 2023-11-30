#coding:gbk
#*******************************************
#作者: 我東
#mail:wodong526@dingtalk.com
#time:2021/11/28
#版本：V1.1
#******************************************

from PySide2.QtCore import Qt, QPoint, QParallelAnimationGroup, QEasingCurve, QPropertyAnimation
from PySide2.QtGui import QFont, QMovie
from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication

gif_path = r''      #gif路径（包括gif本身）
text = u''          #弹幕内容

class barrageWindow(QWidget):
    def __init__(self):
        super(barrageWindow, self).__init__()
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint)#设置窗口为无边框窗口且在窗口最前方显示
        self.setAttribute(Qt.WA_TranslucentBackground, True)               #设置窗口属性为背景透明

        self.label_aim = QLabel(self)                                      #这个控件可以显示文本和图像、动画
        self.label_tex = QLabel(self)

        self.main_layout = QHBoxLayout(self)                               #生成横布局
        self.main_layout.addWidget(self.label_aim)
        self.main_layout.addWidget(self.label_tex)

        self.desktop = QApplication.instance().desktop()                   #类似获取所有显示器（有明白的大佬麻烦教教我^_^）

        self.setText(text)
        self.setAim(gif_path)

    def setText(self, tex):
        self.Font_obj = QFont(u"微软雅黑", 30)
        self.label_tex.setText(tex)
        self.label_tex.setFont(self.Font_obj)
        self.label_tex.setStyleSheet('color:rgb(255, 255, 0)')

    def setAim(self, aimPath):
        self.movie_obj = QMovie('{}'.format(aimPath))
        self.label_aim.setMovie(self.movie_obj)
        self.movie_obj.start()

    def initAim(self, start, end):
        prop_aim = QPropertyAnimation(self, 'pos')#设置动画
        prop_aim.setStartValue(start)
        prop_aim.setEndValue(end)

        prop_aim.setEasingCurve(QEasingCurve.OutInCubic)#加速度变化方式，其它方式参见https://doc.bccnsoft.com/docs/PyQt4/qeasingcurve.html#Type-enum

        prop_aim.setDuration(20000)                     #动画时长，单位：微秒

        self.aim_grp = QParallelAnimationGroup(self)    #生成一个动画组，可以加入其它控件
        self.aim_grp.addAnimation((prop_aim))           #将这个动画窗口放入动画组
        self.aim_grp.finished.connect(self.stop)        #将信号和槽链接
        self.aim_grp.start()                            #动画组开始动画

    def stop(self):
        self.aim_grp.stop()#动画组停止
        self.movie_obj.setFileName('')#设置一个空对象来释放之前的gif占用
        self.close()       #窗口关闭

    def run(self):
        super(barrageWindow, self).show()
        start_poistion = QPoint(self.desktop.screenGeometry().width(), 100)#弹幕发出的初始位置（所有显示桌面的宽像素， 从上向下第100个像素）
        end_poistion = QPoint(-500, 100)                                   #弹幕的结束位置
        self.move(start_poistion)                                          #移动窗口到初始位置
        self.initAim(start_poistion, end_poistion)

a = barrageWindow()
a.run()

