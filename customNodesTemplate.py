# coding=gbk
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx

nodeName = 'meshToSphere'  #节点类型名也是节点名，文件名是插件的名字
nodeId = om.MTypeId(0x00004)  #管理 Maya 对象类型标识符。


class WoDongNode(ompx.MPxNode):
    @classmethod
    def creatorNode(cls):
        return ompx.asMPxPtr(cls())

    @classmethod
    def nodeInitialize(cls):
        """
        初始化节点
        :return:
        """
        pass

    def __init__(self):
        super(WoDongNode, self).__init__()

    def compute(self, plug, dataBlok):
        pass

    def doIt(self, args):
        pass

    def redoIt(self):
        pass

    def undoIt(self):
        """
        当操作可以被撤销时，使用撤销会调用该函数
        :return:
        """
        self.fn_mesh.setPoints(self.initial, om.MSpace.kWorld)

    def isUndoable(self):
        """
        默认返回false，当返回为false表示doIt中的操作不可撤销，运行后立即销毁；返回true则会保留到撤销管理器，用于在撤销时调用undoIt
        运行doIt后会立即调用该函数来判断该操作是否为可撤销
        :return: True
        """
        return True


def initializePlugin(mobject):
    plugin = ompx.MFnPlugin(mobject, 'woDong', '0.1', 'Any')  #mobject,插进供应商，版本，插件适用的api版本（any为所有）
    try:
        plugin.registerNode(nodeName, nodeId, WoDongNode.creatorNode, WoDongNode.nodeInitialize,
                            ompx.MPxNode.kDependNode)  #节点类型名，节点id，创建函数，初始化函数
        om.MGlobal.displayInfo('加载成功！')
    except Exception as e:
        om.MGlobal.displayError('加载发生错误：{}。'.format(e))


def uninitializePlugin(mobject):
    plugin = ompx.MFnPlugin(mobject)
    try:
        plugin.deregisterNode(nodeId)
        om.MGlobal.displayInfo('取消加载成功！')
    except Exception as e:
        om.MGlobal.displayError('取消加载发生错误：{}。'.format(e))
