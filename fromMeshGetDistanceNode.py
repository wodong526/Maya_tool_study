# coding=gbk
import maya.api.OpenMaya as om
import maya.OpenMayaMPx as ompx
import pdb

class GetClosestIntersection(object):
    def __init__(self):
        self._mod = om.MFnMesh()
        self._ray_source = om.MPoint()
        self._ray_vector = om.MFloatVector()
        self._max_param = int()

    def set_fn_mesh(self, fn_mesh):
        self._mod = fn_mesh

    def set_ray_source(self, float_point):
        self._ray_source = float_point

    def set_ray_vector(self, float_vector):
        self._ray_vector = float_vector

    def set_max_param(self, param):
        self._max_param = param

    def get_distance(self):
        """
        返回分别是：命中点，发射点到命中点的距离，命中的面id，命中的三角面id,命中点在三角面上的重心坐标

        命中点在三角面上的重心坐标是一个包含三个浮点数的数组，表示交点在被击中的三角形上的重心坐标。重心坐标是描述一个点在一个三角形内部位置的一种常用方法。
        在一个三角形内，任何一点都可以表示为三个顶点的加权和，这些顶点称为重心坐标系的基础。对于三角形 ABC，重心坐标 (u, v, w) 表示为：
        u：点在 BC 边上的距离与边 AB 的长度之比。
        v：点在 AC 边上的距离与边 BC 的长度之比。
        w：点在 AB 边上的距离与边 AC 的长度之比。
        重心坐标的总和始终为 1，因此 (u, v, w) 位于单位三角形内。这意味着在三角形内，任何一点都可以用这三个值的线性组合来表示，即 P = uA + vB + wC，其中 A、B、C 是三角形的顶点
        :return:
        """
        _, distance, _, _, _, _ = self._mod.closestIntersection(self._ray_source, self._ray_vector,
                                                                om.MSpace.kWorld, self._max_param, False)
        if distance > 0:
            return distance
        else:
            return 0

class WoDongNode(om.MPxNode):
    rayMesh = om.MObject()#模型对象
    sourceArray = om.MObject()#向量源点
    targetArray = om.MObject()#向量终点
    startArray = om.MObject()#发射点
    max_param = om.MObject()#最大距离
    outDistance = om.MObject()  #发射点到模型的距离

    nodeName = 'fromMeshGetDistance'  # 节点类型名也是节点名，文件名是插件的名字
    nodeId = om.MTypeId(0x83002)  # 管理 Maya 对象类型标识符。

    @classmethod
    def update_attr_properties(cls, attr):
        attr.storable = True#可储存
        attr.readable = True#可读
        attr.connectable = True
        if attr.type() == om.MFn.kNumericAttribute:  #如果是数字类型属性
            attr.keyable = True#可k帧

    @classmethod
    def creatorNode(cls):
        return WoDongNode()

    @classmethod
    def nodeInitialize(cls):
        """
        初始化节点
        :return:
        """
        typeAttr = om.MFnTypedAttribute()
        numAttr = om.MFnNumericAttribute()
        mAttr = om.MFnMatrixAttribute()
        compAttr = om.MFnCompoundAttribute()

        WoDongNode.rayMesh = typeAttr.create("inputMesh", "inMesh", om.MFnData.kMesh)
        cls.update_attr_properties(typeAttr)
        om.MPxNode.addAttribute(WoDongNode.rayMesh)

        WoDongNode.sourceArray = mAttr.create("sourceMatrix", "sorMat", om.MFnMatrixAttribute.kDouble)
        om.MPxNode.addAttribute(WoDongNode.sourceArray)#向量起始点

        WoDongNode.targetArray = mAttr.create("targetMatrix", "tagMat", om.MFnMatrixAttribute.kDouble)
        om.MPxNode.addAttribute(WoDongNode.targetArray)#向量终点

        WoDongNode.array = compAttr.create("vector", "vtr")
        cls.update_attr_properties(compAttr)
        compAttr.addChild(WoDongNode.sourceArray)
        compAttr.addChild(WoDongNode.targetArray)
        om.MPxNode.addAttribute(WoDongNode.array)#向量属性

        WoDongNode.startArray = mAttr.create("startMatrix", "starMat", om.MFnMatrixAttribute.kDouble)
        om.MPxNode.addAttribute(WoDongNode.startArray)#发射点

        WoDongNode.max_param = numAttr.create('maxParam', 'mp', om.MFnNumericData.kInt, 9999)
        cls.update_attr_properties(numAttr)
        om.MPxNode.addAttribute(WoDongNode.max_param)

        WoDongNode.outDistance = numAttr.create("Distance", "dis", om.MFnNumericData.kFloat, 0.0)
        numAttr.readable = True
        numAttr.writable = False
        numAttr.storable = True
        numAttr.keyable = False
        om.MPxNode.addAttribute(WoDongNode.outDistance)#长度输出

        om.MPxNode.attributeAffects(WoDongNode.rayMesh, WoDongNode.outDistance)
        om.MPxNode.attributeAffects(WoDongNode.array, WoDongNode.outDistance)
        om.MPxNode.attributeAffects(WoDongNode.startArray, WoDongNode.outDistance)
        om.MPxNode.attributeAffects(WoDongNode.max_param, WoDongNode.outDistance)

    def __init__(self):
        super(WoDongNode, self).__init__()
        self.ray = GetClosestIntersection()

    def compute(self, plug, dataBlok):
        if plug == WoDongNode.outDistance:
            mfn_mesh = self.get_upstream_nod()
            sor_array = om.MTransformationMatrix(dataBlok.inputValue(WoDongNode.sourceArray).asMatrix()).translation(om.MSpace.kWorld)
            tag_array = om.MTransformationMatrix(dataBlok.inputValue(WoDongNode.targetArray).asMatrix()).translation(om.MSpace.kWorld)
            star_array = om.MTransformationMatrix(dataBlok.inputValue(WoDongNode.startArray).asMatrix()).translation(om.MSpace.kWorld)
            max_param = dataBlok.inputValue(WoDongNode.max_param).asInt()
            outputAttr = dataBlok.outputValue(WoDongNode.outDistance)

            if mfn_mesh:
                sor_point = om.MFloatPoint(star_array)
                vector_fVector = om.MFloatVector(tag_array - sor_array).normal()

                self.ray.set_ray_source(sor_point)
                self.ray.set_ray_vector(vector_fVector)
                self.ray.set_max_param(max_param)
                self.ray.set_fn_mesh(mfn_mesh)
                distance = self.ray.get_distance()
                outputAttr.setFloat(distance) if distance else outputAttr.setFloat(0.0)
            else:
                outputAttr.setFloat(0.0)
        return

    def get_upstream_nod(self):
        """
        获取上游mesh节点
        :return:
        """
        dpd_nod = om.MFnDependencyNode(self.thisMObject())
        plug = dpd_nod.findPlug('inputMesh', False)

        mit = om.MItDependencyGraph(plug, om.MFn.kMesh, om.MItDependencyGraph.kUpstream,
                                    om.MItDependencyGraph.kDepthFirst, om.MItDependencyGraph.kNodeLevel)
        mesh_node = None
        while not mit.isDone():
            mesh_node = mit.currentNode()
            break

        if isinstance(mesh_node, om.MObject):
            fn_dag_node = om.MFnDagNode(mesh_node)
            dag_node = fn_dag_node.getPath()
            return om.MFnMesh(dag_node)
        return None

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

def maya_useNewAPI():
    pass

def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, 'woDong', '0.1', 'Any')  #mobject,插进供应商，版本，插件适用的api版本（any为所有）
    try:
        plugin.registerNode(WoDongNode.nodeName, WoDongNode.nodeId, WoDongNode.creatorNode, WoDongNode.nodeInitialize,
                            om.MPxNode.kDependNode)  #节点类型名，节点id，创建函数，初始化函数
        om.MGlobal.displayInfo('加载成功！')
    except Exception as e:
        om.MGlobal.displayError('加载发生错误：{}。'.format(e))


def uninitializePlugin(mobject):
    plugin = om.MFnPlugin(mobject)
    try:
        plugin.deregisterNode(WoDongNode.nodeId)
        om.MGlobal.displayInfo('取消加载成功！')
    except Exception as e:
        om.MGlobal.displayError('取消加载发生错误：{}。'.format(e))
