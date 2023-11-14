# coding=gbk
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx

import math

nodeName = 'meshToSphere'  #节点类型名也是节点名，文件名是插件的名字
nodeId = om.MTypeId(0x00004)  #管理 Maya 对象类型标识符。


class WoDongNode(ompx.MPxDeformerNode):
    @classmethod
    def creatorNode(cls):
        return ompx.asMPxPtr(cls())

    @classmethod
    def nodeInitialize(cls):
        """
        初始化节点
        :return:
        """
        nAttr = om.MFnNumericAttribute()
        outGeo = ompx.cvar.MPxGeometryFilter_outputGeom

        cls.input = nAttr.create('up', 'up', om.MFnNumericData.kFloat, 0.0)
        nAttr.setStorable(True)
        nAttr.setConnectable(True)
        nAttr.setWritable(True)
        nAttr.setKeyable(True)
        cls.addAttribute(cls.input)
        cls.attributeAffects(cls.input, outGeo)

    def __init__(self):
        super(WoDongNode, self).__init__()

    def deform(self, dataBlok, it, mat, multiIndex):
        """
        使用cmds.deformer(type='meshToSphere')来调用变形器效果
        :param dataBlok:包含节点属性存储的数据块
        :param it:MItGeometry类型，可用于遍历模型的点
        :param mat:
        :param multiIndex:
        :return:
        """
        up = dataBlok.inputValue(self.input).asFloat()
        en = dataBlok.inputValue(ompx.cvar.MPxGeometryFilter_envelope).asFloat()
        vec = om.MVector(0, up*en, 0)
        while not it.isDone():
            point = it.position()
            it.setPosition(point+vec)
            it.next()

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
                            ompx.MPxNode.kDeformerNode)  #节点类型名，节点id，创建函数，初始化函数
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
