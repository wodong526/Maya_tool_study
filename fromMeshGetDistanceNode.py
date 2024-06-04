# coding=gbk
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import pdb

nodeName = 'fromMeshGetDistance'  #节点类型名也是节点名，文件名是插件的名字
nodeId = om.MTypeId(0x00004)  #管理 Maya 对象类型标识符。


def feedback(txt, info=False, warning=False, error=False, block=True):
    """
    根据提供的类型显示反馈消息。
    Parameters:
    txt (str): 要显示的消息。
    info (bool): 如果为 True，则显示为普通消息。
    warning (bool): 如果为 True，则显示为警告消息。
    error (bool): 如果为 True，则显示为错误消息。
    time (int): 显示消息的时间（以毫秒为单位）。
    block (bool): 如果为 True，引发错误时阻断程序。

    Returns:
    None
    """

    if not info and not warning and not error:
        info = True
    if info:
        om.MGlobal.displayInfo('{}'.format(txt))
    elif warning:
        om.MGlobal.displayWarning('{}'.format(txt))
    elif error:
        om.MGlobal.displayError(txt)


class MeshRay(object):
    @classmethod
    def is_float_lis(cls, lis):
        """
        检查嵌套列表中的所有元素是否都是浮点数或整数。
        Args:
        lis (list): 要检查的嵌套列表。
        Returns:
        bool: 如果所有元素都是浮点数或整数，则为 True，否则为 False。
        """
        for inf in lis:
            if isinstance(inf, list) or isinstance(inf, tuple):
                cls.is_float_lis(inf)
            elif not isinstance(inf, float) and not isinstance(inf, int):
                feedback('参数{}不属于列表或数字'.format(inf), error=True)
                return False
        return True

    @classmethod
    def get_mesh_mfn(cls, transform_name):
        """
        获取指定变换节点的shape节点的MFnMesh类型对象。
        Args:
            transform_name （str）：要获取其 MFnMesh 对象的转换节点的名称。
        Returns:
            om.MFnMesh: 与转换节点关联的 MFnMesh 对象。
        """
        sel_list = om.MSelectionList()
        sel_list.add(transform_name)
        dag = om.MDagPath()
        sel_list.getDagPath(0, dag)

        dag.extendToShape()
        fn_mesh = om.MFnMesh(dag)

        return fn_mesh

    def __init__(self, ray_vector, ray_source=None, space=om.MSpace.kWorld, max_param=99999, both_directions=False,
                 mod=None):
        """
        OpenMaya.Api1.0的射线函数类。
        Args:
        ray_vector (OpenMaya.MFloatVector): 射线向量。
        ray_source (list, OpenMaya.MFloatPoint): 射线的起点。如果未提供，则使用射线向量的第一个点。
        space (OpenMaya.MSpace, optional): 击中点坐标的计算空间。默认值为om.MSpace.kWorld。
        max_param (float, optional): 射线发射的最大参数值。默认值为 99999.
        both_directions (bool, optional): 如果为 True，则射线从源点的正负两个方向投射。默认值为 False。
        mod (str, optional): 如果指定则只检测指定的模型，否则检测场景里所有模型。默认值为 None。
        """
        self._ray_vector = om.MFloatVector()
        self._ray_source = om.MFloatPoint()
        self._space = space
        self._max_param = max_param
        self._both_directions = both_directions

        self.set_ray_vector(ray_vector)
        if ray_source:
            self.set_ray_source(ray_source)
        else:
            self._ray_source = om.MFloatPoint(ray_vector[0][0], ray_vector[0][1], ray_vector[0][2])
        self.set_mod(mod)

        self._info_dir = {}

    def set_ray_vector(self, val):
        """
        根据输入值设置射线向量。
        Args:
            val: 包含两个列表的列表，每个列表包含三个浮点数，或者一个 OpenMaya.MFloatVector 或一个 OpenMaya.MVector。
        Returns:
            None
        """
        if isinstance(val, om.MFloatVector):
            val.normalize()
            self._ray_vector = val
        elif isinstance(val, om.MVector):
            self._ray_vector = om.MFloatVector(val)
        elif len(val) == 2 and len(val[0]) == 3 and len(val[1]) == 3 and MeshRay.is_float_lis(val):
            self._ray_vector = om.MFloatVector(val[1][0] - val[0][0],
                                               val[1][1] - val[0][1],
                                               val[1][2] - val[0][2])
        else:
            feedback('参数{}类型应为[[float, float, float], [float, float, float]]或OpenMaya.MFloatVector或OpenMaya.MVector\n'
                     '实际为{}'.format(val, [list(map(type, sublist)) for sublist in val]), error=True)

    def get_ray_vector(self):
        """
        获取射线向量属性。
        Returns:
        Vector: 射线向量。
        """
        feedback(self._ray_vector)
        return self._ray_vector

    def set_ray_source(self, val):
        """
        根据输入值设置射线源点。
        Args:
        val: 要设置为射线源的值。应该是三个浮点数的列表，一个 OpenMaya.MPoint，或 OpenMaya.MFloatPoint。
        """
        if isinstance(val, om.MFloatPoint):
            self._ray_source = val
        elif isinstance(val, om.MPoint):
            self._ray_source = om.MFloatPoint(val)
        elif len(val) == 3 and MeshRay.is_float_lis(val):
            self._ray_source = om.MFloatPoint(val[0], val[1], val[2])
        else:
            feedback('参数{}类型应为[float, float, float]或OpenMaya.MFloatPoint或OpenMaya.MPoint\n'
                     '实际为{}'.format(val, [list(map(type, sublist)) for sublist in val]), error=True)

    def get_ray_source(self):
        """
        用于访问射线源点的 Getter 方法。
        """
        feedback(self._ray_source)
        return self._ray_source

    def set_space(self, val):
        """
        使用提供的值设置space属性。
        Parameters:
        val (om.MSpace): 要将 space 属性设置为的值。
        """
        if isinstance(val, om.MSpace):
            self._space = val
        else:
            feedback('参数{}类型应为OpenMaya.MSpace，实际为{}'.format(val, type(val)), warning=True)

    def get_space(self):
        """
        space 属性的 Getter 方法。
        Returns:
        int: 获取到的space 属性的值。
        """
        feedback(self._space)
        return self._space

    def set_max_param(self, val):
        """
        设置最大检测距离。
        Args:
        val (int): 要设置距离的值。
        """
        if isinstance(val, int):
            self._max_param = val
        else:
            feedback('参数{}类型应为int，实际为{}'.format(val, type(val)), warning=True)

    def get_max_param(self):
        """
        最大检测距离的 Getter 方法.
        Returns:
            int: 最大检测距离的值。
        """
        feedback(self._max_param)
        return self._max_param

    def set_both_directions(self, val):
        """
        设置是否检测向量的正反方向。
        Args:
            val (bool): 为both_directions设置的布尔值。
        """
        if isinstance(val, bool):
            self._both_directions = val
        else:
            feedback('参数{}bool，实际为{}'.format(val, type(val)), warning=True)

    def get_both_directions(self):
        """
        获取both_directions的值。
        Returns:
        bool: both_directions的值。
        """
        feedback(self._both_directions)
        return self._both_directions

    def set_mod(self, val):
        """
        设置指定的检测模型。
        如果 val 是 om.MFnMesh，将修饰符设置为 val。
        如果 val 是表示模型的transform节点的名称，自动转换模型的shape为 MFnMesh。
        如果 val 不满足上述条件，则将修饰符设置为 None，且不对具体模型做检测，而是检测所有模型。
        Args:
        - val: 可以是 OpenMaya.MFnMesh 或模型的transform节点的名称。
        """
        if isinstance(val, om.MFnMesh):
            self._mod = val
        else:
            #feedback('{}不存在或不为模型的transform节点或不是模型对象的名称'.format(val), error=True)
            self._mod = None

    def get_mod(self):
        """
        mod 属性的 getter 方法。

        Returns:
        int: mod 属性的值。
        """
        feedback(self._mod)
        return self._mod

    def __shooting_core(self, fn_mesh):
        """
        执行射线检测操作以查找给定网格上最近的交点。
        Parameters:
        fn_mesh (om.MFnMesh): 要对其执行交集操作的OpenMaya.MFnMesh对象。
        Returns:
        tuple: 包含命中点的世界坐标的元组，命中点与射线源的距离，
               命中点所属面的ID，命中点所属三角面的ID。
        """
        hit_point = om.MFloatPoint()  # 击中点的世界坐标

        hitDistance = om.MScriptUtil(0.0)
        hit_ray_param = hitDistance.asFloatPtr()  # 击中点离发射点的距离

        hitFace = om.MScriptUtil()
        hit_face_ptr = hitFace.asIntPtr()  # 击中点的面的id
        hitTriangle = om.MScriptUtil()
        hit_triangle_ptr = hitTriangle.asIntPtr()  # 击中点的面的三角形id
        fn_mesh.closestIntersection(self._ray_source, self._ray_vector, None, None, False, self._space, self._max_param,
                                    self._both_directions, None, hit_point, hit_ray_param, hit_face_ptr,
                                    hit_triangle_ptr, None, None)

        if om.MScriptUtil().getInt(hit_face_ptr):
            return hit_point, hit_ray_param, hit_face_ptr, hit_triangle_ptr
        else:
            return None

    def get_hit_mod(self):
        """
        此函数计算 mod 对象的命中信息。
        如果设置了 mod 对象，它会根据 mod 的几何形状计算命中信息。
        如果未设置 mod 对象，它会遍历场景以查找网格对象并计算每个对象的命中信息。
        Returns:
        None
        """
        self._info_dir.clear()
        if self._mod:
            ret = self.__shooting_core(self._mod)
            if not ret:
                return None
            self._info_dir[om.MFnDependencyNode(self._mod.object()).name()] = {'pos': ret[0], 'distance': ret[1],
                                                                               'face_id': ret[2],
                                                                               'triangular_id': ret[3]}
        # else:
        #     it = om.MItDag(om.MItDag.kBreadthFirst, om.MFn.kMesh)
        #     while not it.isDone():
        #         current_obj = it.currentItem()
        #         if current_obj.hasFn(om.MFn.kMesh):
        #             dag_path = om.MDagPath()
        #             it.getPath(dag_path)
        #             #如果不使用dag_path构造MFnMesh，调用closestIntersection时报错Must have a DAG path to do world space transforms
        #             fn_mesh = om.MFnMesh(dag_path)
        #             ret = self.__shooting_core(fn_mesh)
        #             if not ret:
        #                 continue
        #             self._info_dir[om.MFnDependencyNode(current_obj).name()] = {'pos': ret[0], 'distance': ret[1],
        #                                                                         'face_id': ret[2],
        #                                                                         'triangular_id': ret[3]}
        #
        #         it.next()

    def decorator_hit(fun):
        """
        这是一个装饰器函数，它调用“get_hit_mod”，然后调用输入函数“fun”。
        Args:
        - fun: 要装饰的函数。
        Returns:
        - 函数返回。
        """
        def wrapper(self, *args, **kwargs):
            self.get_hit_mod()
            return fun(self, *args, **kwargs)
        return wrapper

    @decorator_hit
    def get_all_info(self):
        """
        获取所有射线检索到的信息。
        Returns:
        str: 所有射线检索到的信息的字典。
        """
        return self._info_dir

    @decorator_hit
    def get_pos(self):
        """
        获取每个被击中模型的坐标信息。
        Returns:
        dict: 包含模型名称为键，击中点坐标位置信息（OpenMaya.MFloatPoint类型）作为值的字典。
        """
        ret_dir = {}
        for mod, val in self._info_dir.items():
            return val['pos']

        return ret_dir

    @decorator_hit
    def get_distance(self):
        """
       获取每个被击中模型距离发射源的距离。
       Returns:
           dict: 包含模型名称为键，击中点到发射源的距离（float *类型）作为值的字典。
       """
        ret_dir = {}
        for mod, val in self._info_dir.items():
            return val['distance']

        return None
        #return ret_dir

    @decorator_hit
    def get_face_id(self):
        """
        获取每个被击中模型的面的id。
        Returns:
            dict: 包含模型名称为键，被击中面的id（int *类型）作为值的字典。
        """
        ret_dir = {}
        for mod, val in self._info_dir.items():
            ret_dir[mod] = val['face_id']

        return ret_dir

    @decorator_hit
    def get_triangle_id(self):
        """
        获取每个被击中模型的面的三角面的id。
        Returns:
            dict: 包含模型名称为键，被击中三角面的id（int *类型）作为值的字典。
        """
        ret_dir = {}
        for mod, val in self._info_dir.items():
            ret_dir[mod] = val['triangular_id']

        return ret_dir

    def __repr__(self):
        """
        以字符串返回当前实例的各参数的值和被检测到的信息。
        Returns:
        str: 各参数的值和被检测到的信息。
        """
        ret = 'vay_vector : {};vay_source : {};space : {};max_param : {};both_directions : {};mod : {}'.format(
            self._ray_vector, self._ray_source, self._space, self._max_param, self._both_directions, self._mod)
        return ret + '\n' + str(self._info_dir)



class WoDongNode(ompx.MPxNode):
    rayMesh = om.MObject()#模型对象
    sourceArray = om.MObject()#向量源点
    targetArray = om.MObject()#向量终点
    startArray = om.MObject()#发射点
    outDistance = om.MObject()  #发射点到模型的距离



    @classmethod
    def update_attr_properties(cls, attr):
        attr.setWritable(True)#属性可写
        attr.setStorable(True)#可储存
        attr.setReadable(True)#可读
        attr.setConnectable(True)
        if attr.type() == om.MFn.kNumericAttribute:  #如果是数字类型属性
            attr.setKeyable(True)#可k帧

    @classmethod
    def creatorNode(cls):
        return ompx.asMPxPtr(cls())

    @classmethod
    def nodeInitialize(cls):
        """
        初始化节点
        :return:
        """
        typeAttr = om.MFnTypedAttribute()
        numAttr = om.MFnNumericAttribute()
        compAttr = om.MFnCompoundAttribute()

        WoDongNode.rayMesh = typeAttr.create("inputMesh", "inMesh", om.MFnData.kMesh)
        cls.update_attr_properties(typeAttr)
        WoDongNode.addAttribute(WoDongNode.rayMesh)

        WoDongNode.sourceArray_x = numAttr.create("sourceArray_x", "sorArry_x", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.sourceArray_x)

        WoDongNode.sourceArray_y = numAttr.create("sourceArray_y", "sorArry_y", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.sourceArray_y)

        WoDongNode.sourceArray_z = numAttr.create("sourceArray_z", "sorArry_z", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.sourceArray_z)

        WoDongNode.sourceArray = numAttr.create("sourceArray", "sorArry", WoDongNode.sourceArray_x,
                                                WoDongNode.sourceArray_y, WoDongNode.sourceArray_z)
        WoDongNode.addAttribute(WoDongNode.sourceArray)#向量起始点

        WoDongNode.targetArray_x = numAttr.create("targetArray_x", "tagArry_x", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.targetArray_x)

        WoDongNode.targetArray_y = numAttr.create("targetArray_y", "tagArry_y", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.targetArray_y)

        WoDongNode.targetArray_z = numAttr.create("targetArray_z", "tagArry_z", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.targetArray_z)

        WoDongNode.targetArray = numAttr.create("targetArray", "tagArry", WoDongNode.targetArray_x,
                                                WoDongNode.targetArray_y, WoDongNode.targetArray_z)
        WoDongNode.addAttribute(WoDongNode.targetArray)#向量终点

        WoDongNode.array = compAttr.create("array", "arry")
        cls.update_attr_properties(compAttr)
        compAttr.addChild(WoDongNode.sourceArray)
        compAttr.addChild(WoDongNode.targetArray)
        WoDongNode.addAttribute(WoDongNode.array)#向量属性

        WoDongNode.startArray_x = numAttr.create("startArray_x", "starArry_x", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.startArray_x)

        WoDongNode.startArray_y = numAttr.create("startArray_y", "starArry_y", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.startArray_y)

        WoDongNode.startArray_z = numAttr.create("startArray_z", "starArry_z", om.MFnNumericData.kFloat, 0.0)
        WoDongNode.addAttribute(WoDongNode.startArray_z)

        WoDongNode.startArray = numAttr.create("startArray", "starArry", WoDongNode.startArray_x,
                                                WoDongNode.startArray_y, WoDongNode.startArray_z)

        cls.update_attr_properties(numAttr)
        WoDongNode.addAttribute(WoDongNode.startArray)#发射点

        WoDongNode.outDistance = numAttr.create("Distance", "dis", om.MFnNumericData.kFloat, 0.0)
        numAttr.setReadable(True)
        numAttr.setWritable(False)
        numAttr.setStorable(True)
        numAttr.setKeyable(False)
        WoDongNode.addAttribute(WoDongNode.outDistance)#长度输出

        WoDongNode.attributeAffects(WoDongNode.rayMesh, WoDongNode.outDistance)
        WoDongNode.attributeAffects(WoDongNode.array, WoDongNode.outDistance)
        WoDongNode.attributeAffects(WoDongNode.startArray, WoDongNode.outDistance)

    def __init__(self):
        super(WoDongNode, self).__init__()
        self.ray = MeshRay([[0, 0, 0], [0, 0, 0]], [0, 0, 0], both_directions=True)

    def compute(self, plug, dataBlok):
        if plug == WoDongNode.outDistance:
            #mfn_mesh = dataBlok.inputValue(WoDongNode.rayMesh).asMesh()
            mfn_mesh = self.get_upstream_nod()
            sor_array = dataBlok.inputValue(WoDongNode.sourceArray).asFloat3()
            tag_array = dataBlok.inputValue(WoDongNode.targetArray).asFloat3()
            star_array = dataBlok.inputValue(WoDongNode.startArray).asFloat3()
            outputAttr = dataBlok.outputValue(WoDongNode.outDistance)

            lis_array = list(map(lambda x, y:y-x, sor_array, tag_array))
            lis_start = list(map(lambda x:round(x, 5), star_array))
            if mfn_mesh:
                vector_fVector = om.MFloatVector(lis_array[0], lis_array[1], lis_array[2])
                start_fPoint = om.MFloatPoint(lis_start[0], lis_start[1], lis_start[2])
                self.ray.set_ray_vector(vector_fVector)
                self.ray.set_ray_source(lis_start)
                self.ray.set_mod(mfn_mesh)
                if self.ray.get_distance():
                    distance = om.MScriptUtil().getFloat(self.ray.get_distance())
                    # pos = self.ray.get_pos()
                    # print(pos.x, pos.y, pos.z)
                    # print(distance)
                    outputAttr.setFloat(distance)
                else:
                    outputAttr.setFloat(0.0)
            else:
                outputAttr.setFloat(0.0)
        return om.kUnknownParameter

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
            mesh_node = mit.thisNode()
            break

        if isinstance(mesh_node, om.MObject):
            fn_dag_node = om.MFnDagNode(mesh_node)
            dag_node = om.MDagPath()
            fn_dag_node.getPath(dag_node)
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
