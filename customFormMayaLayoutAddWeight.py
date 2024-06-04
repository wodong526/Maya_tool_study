# -*- coding:gbk -*-
import maya.cmds as mc
import maya.mel as mm
from functools import partial

class ShowPanel():
    def __init__(self):
        self.showPanel()

    def showPanel(self):
        gHelpLineForm = mm.eval('$gHelpLineForm')#获取帮助控件对象
        button_labels = ['All', 'Crv', 'CVs', 'Poly', 'Joint', 'Loc', 'Def', 'Sur', 'Fol', 'IK', 'Cam', 'Lgt']#按钮名称
        commonds_flag = ['allObjects', 'nurbsCurves', 'cv', 'polymeshes', 'joints', 'locators', 'deformers',
                         'nurbsSurfaces', 'follicles', 'ikHandles', 'cameras', 'lights']#按钮要传递的参数

        #创建一个横布局
        rawLayout1_return = mc.rowLayout('RowLayout1', q=True, exists=True)
        formChildren = None
        if not rawLayout1_return:
            formChildren = mc.formLayout(gHelpLineForm, q=True, childArray=True)#获取帮助控件中原生的控件
            rawLayout1 = mc.rowLayout('RowLayout1', numberOfColumns=len(button_labels) * 2, parent=gHelpLineForm)
        else:
            rawLayout1 = 'RowLayout1'

        mc.setParent('RowLayout1')
        children = mc.rowLayout('RowLayout1', q=True, childArray=True)
        if children:
            mc.deleteUI(children)
        for label, flag in zip(button_labels, commonds_flag):#向横布局里添加按钮
            mc.button(label=label, width=30, height=15, command=partial(self.toggleVisibility, flag))
        #创建一个横布局
        rawLayout2_return = mc.rowLayout('RowLayout2', q=True, exists=True)
        if not rawLayout2_return:
            rawLayout2 = mc.rowLayout('RowLayout2', numberOfColumns=25, parent=gHelpLineForm)
        else:
            rawLayout2 = 'RowLayout2'

        mc.setParent('RowLayout2')
        children = mc.rowLayout('RowLayout2', q=True, childArray=True)
        if children:
            mc.deleteUI(children)
        if formChildren:#将帮助控件中原生的控件放入新的这个横布局中
            for i in formChildren:
                mc.frameLayout(i, edit=True, parent='RowLayout2')
        #设置两个布局的上下左右像素偏移，ac表示两个控件之间的像素偏移
        mc.formLayout(gHelpLineForm, edit=True,
                        attachForm=[
                            (rawLayout1, 'top', 0),
                            (rawLayout1, 'left', 10),
                            (rawLayout1, 'right', 0),
                            (rawLayout2, 'left', 1),
                            (rawLayout2, 'right', 0)
                        ],
                        attachControl=[(rawLayout2, 'top', 2, rawLayout1)])

    def toggleVisibility(self, obj_type, *args):
        current_panel = mc.getPanel(withFocus=True)
        if mc.getPanel(typeOf=current_panel) == "modelPanel":
            current_state = mc.modelEditor(current_panel, q=True, **{obj_type: True})
            new_state = not current_state
            mc.modelEditor(current_panel, e=True, **{obj_type: new_state})

ShowPanel()