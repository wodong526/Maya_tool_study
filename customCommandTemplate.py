# coding=gbk
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx

import math

cmdName = 'box_num'#命令名称，文件名是插件的名字
numFlag = '-num'
numFlagLong = '-number'

class PrintStringCmd(ompx.MPxCommand):
    @classmethod
    def creatorCmd(cls):
        return ompx.asMPxPtr(cls())

    @classmethod
    def syntaxCreator(cls):
        """
        用于修饰参数
        :return:
        """
        s = om.MSyntax()
        s.addFlag(numFlag, numFlagLong, om.MSyntax.kDouble)
        s.enableEdit(False)
        s.enableQuery(False)
        return s

    def __init__(self):
        super(PrintStringCmd, self).__init__()


    def doIt(self, args):
        """
        命令运行的内容在这里开始
        :param args:
        :return:
        """
        argData = om.MArgDatabase(self.syntax(), args)
        if argData.isFlagSet(numFlag):  #当收到的参数为该标志时
            self.val = argData.flagArgumentDouble(numFlag, 0)  #获取该标志的参数的第一个值
            self.redoIt()#运行时调用这个函数，重做时直接调用redoIt，不要向该函数传参
        else:
            om.MGlobal.displayError('没有输入有效值用于计算。')

    def redoIt(self):
        """
        重做命令，相当于ctrl-y
        不要将参数从该函数的形参传进来，否则重做会报错，因为重做出发时不会向该函数传参
        :return:
        """
        #dagMod必须放到运行代码中。该类会在启动插件时直接启动，如果将dagMod放到init中，
        # 即便使用撤销也只是将dagMod.doIt的操作结果放到堆栈，而dagMod还保留着上一次内容，而dagMod还保留着上一次内容
        # 继续运行dagMod.doIt将会把上一次的内容与这一次的内容一起释放
        #如果在该函数中，则每次运行都是重新实例化了一次om.MDagModifier，且不影响撤销
        self.dagMod = om.MDagModifier()
        node = self.dagMod.createNode('joint')
        self.dagMod.doIt()  #生成节点
        box = om.MFnDependencyNode(node)
        box.setName('box_{}'.format(self.val))  #设置节点名称
        plug = box.findPlug('translateY')
        plug.setFloat(self.val)  #设置节点属性值

        self.setResult(self.val)  #用# Result:的方式来返回信息
        self.displayInfo(self.val)  #用其他基本形式来返回，error也不会打断执行
        self.displayError(self.val)
        self.displayWarning(self.val)
        self.setResult(self.className())  #返回该类的类名称（继承的父类名称MPxCommand


    def undoIt(self):
        """
        当操作可以被撤销时，使用撤销会调用该函数
        :return:
        """
        self.dagMod.undoIt()

    def isUndoable(self):
        """
        默认返回false，当返回为false表示doIt中的操作不可撤销，运行后立即销毁；返回true则会保留到撤销管理器，用于在撤销时调用undoIt
        运行doIt后会立即调用该函数来判断该操作是否为可撤销
        :return: True
        """
        return True



def initializePlugin(mobject):
    plugin = ompx.MFnPlugin(mobject, 'woDong', '0.1', 'Any')#mobject,插进供应商，版本，插件适用的api版本（any为所有）
    try:
        plugin.registerCommand(cmdName, PrintStringCmd.creatorCmd, PrintStringCmd.syntaxCreator)
        om.MGlobal.displayInfo('加载成功！')
    except Exception as e:
        om.MGlobal.displayError('加载发生错误：{}。'.format(e))

def uninitializePlugin(mobject):
    plugin = ompx.MFnPlugin(mobject)
    try:
        plugin.deregisterCommand(cmdName)
        om.MGlobal.displayInfo('取消加载成功！')
    except Exception as e:
        om.MGlobal.displayError('取消加载发生错误：{}。'.format(e))
