# coding=gbk
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx

import math

nodeName = 'dongDong'  #节点类型名也是节点名，文件名是插件的名字
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
        nAttr = om.MFnMatrixAttribute()
        cls.output = nAttr.create('output', 'out', om.MFnMatrixAttribute.kDouble)  #属性长名、短名、值类型、默认值
        nAttr.setStorable(False)  #可储存
        #nAttr.setWritable(False)#可写
        cls.addAttribute(cls.output)

        cls.input = nAttr.create('input', 'in', om.MFnMatrixAttribute.kDouble)  #属性长名、短名、值类型、默认值
        nAttr.setArray(True)
        nAttr.setStorable(True)  #可储存
        nAttr.setConnectable(True)  #可链接
        nAttr.setWritable(True)  #可写
        nAttr.setKeyable(True)  #可k帧
        cls.addAttribute(cls.input)

        #当输入属性发生变化时，只计算指定的输出属性。输出属性不能被设置为可k帧，否则该方法失效。
        # 如果节点初始化没有使用该方法，则不会调用compute函数,即该输入属性发生改变不会刷新compute
        cls.attributeAffects(cls.input, cls.output)

    @classmethod
    def compute_center_matrix(cls, matrix_array):
        """
        计算MMatrixArray的中心点，但旋转与缩放有误，只能计算正确位移
        :param matrix_array:MMatrixArray
        :return:
        """
        num_matrices = matrix_array.length()  #数组长度
        if num_matrices < 2:
            return matrix_array[0]

        total = om.MMatrix()
        for i in range(num_matrices):
            total *= matrix_array[i]

        total = total * (1.0 / num_matrices)
        cls.get_mat(total)  #打印矩阵
        return total

    @staticmethod
    def get_mat(mat):
        """
        打印MMatrix矩阵
        :param mat: 被打印的MMatrix
        :return:
        """
        for row in range(4):
            row_values = []
            for col in range(4):
                element_value = mat(row, col)
                row_values.append(element_value)
            print(row_values)

    def __init__(self):
        super(WoDongNode, self).__init__()

    def compute(self, plug, dataBlok):
        """
        根据节点输入重新计算给定输出。plug代表需要重新计算的数据值，dataBlok保存节点所有属性的存储。
        :param plug:需要重新计算的属性
        :param dataBlok:包含节点属性存储的数据块
        :return:kSuccess计算成功;kFailure计算失败
        """
        if plug == self.output:
            inputValue = dataBlok.inputArrayValue(self.input)
            outHandle = dataBlok.outputValue(self.output)

            mat_arr = om.MMatrixArray()
            for i in range(inputValue.elementCount()):
                inputValue.jumpToElement(i)
                val = inputValue.inputValue().asMatrix()
                mat_arr.append(val)

            center = self.compute_center_matrix(mat_arr)
            outHandle.setMMatrix(center)
            dataBlok.setClean(plug)
            return True
        else:
            return om.kUnknownParameter


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
