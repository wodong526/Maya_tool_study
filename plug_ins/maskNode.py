#coding=utf-8
import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.api.OpenMayaUI as omui

import maya.cmds as mc

import datetime
import os

def maya_useNewAPI():
    pass


class DongShotMaskLocator(omui.MPxLocatorNode):

    NAME = "DongShotMask"
    TYPE_ID = om.MTypeId(0x0007F7FE)

    DRAW_DB_CLASSIFICATION = "drawdb/geometry/zurbriggshotmask"
    DRAW_REGISTRANT_ID = "DongShotMaskLocator"

    TEXT_ATTR = [('topLeftText', 'tlt', u'上左字符'), ('topCenterText', 'tct', u'上中字符'), ('topRightText', 'trt', u'上右字符'),
                 ('bottomLeftText', 'blt', u'下左字符'), ('bottomCenterText', 'bct', u'下中字符'), ('bottomRightText', 'brt', u'下右字符')]

    def postConstructor(self):
        """
        复写函数，将这三个属性在创建时关闭，否则在使用时无法看到场景中的灯光阴影
        :return:
        """
        node_fn = om.MFnDependencyNode(self.thisMObject())
        node_fn.findPlug('castsShadows', False).setBool(False)
        node_fn.findPlug('receiveShadows', False).setBool(False)
        node_fn.findPlug('motionBlur', False).setBool(False)

    @classmethod
    def creator(cls):
        """
        创建节点实例的方法
        :return:
        """
        return DongShotMaskLocator()

    @classmethod
    def initialize(cls):
        """
        初始化节点的方法
        :return:
        """
        numeric_attr = om.MFnNumericAttribute()#数字属性对象
        type_attr = om.MFnTypedAttribute()#字符属性对象
        string_data_fn = om.MFnStringData()#字符串对象，不是属性类型

        #创建绘制遮罩的相机名属性
        dft = string_data_fn.create('')#默认填入的值
        camera_name = type_attr.create('camera', 'cam', om.MFnData.kString, dft)#创建属性
        type_attr.setNiceNameOverride(u'相机')#设置niceName
        cls.update_attr_properties(type_attr)
        cls.addAttribute(camera_name)

        #在遮罩上绘制的字符属性
        for i, inf in enumerate(cls.TEXT_ATTR):
            dft = string_data_fn.create('Position {}'.format(str(i+1).zfill(2)))
            position = type_attr.create(inf[0], inf[1], om.MFnData.kString, dft)
            type_attr.setNiceNameOverride(inf[2])
            cls.update_attr_properties(type_attr)
            cls.addAttribute(position)

        #文本填充属性
        text_padding = numeric_attr.create('textPadding', 'tp', om.MFnNumericData.kShort, 10)
        numeric_attr.setNiceNameOverride(u'字符边距')
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setMin(0)
        numeric_attr.setMax(50)
        cls.addAttribute(text_padding)

        #字符名称
        dft = string_data_fn.create('consolas')
        font_name = type_attr.create('fontName', 'fn', om.MFnData.kString, dft)
        type_attr.setNiceNameOverride(u'字符字体')
        cls.update_attr_properties(type_attr)
        cls.addAttribute(font_name)

        #字符颜色
        font_color = numeric_attr.createColor('fontColor', 'fc')
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setNiceNameOverride(u'字符颜色')
        numeric_attr.default = (1.0, 1.0, 1.0)
        cls.addAttribute(font_color)

        #字符透明度
        font_alpha = numeric_attr.create('fontAlpha', 'fa', om.MFnNumericData.kFloat, 1.0)
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setNiceNameOverride(u'字符透明度')
        numeric_attr.setMin(0.0)
        numeric_attr.setMax(1.0)
        cls.addAttribute((font_alpha))

        #字符大小
        font_scale = numeric_attr.create('fontScale', 'fs', om.MFnNumericData.kFloat, 1.0)
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setNiceNameOverride(u'字符大小')
        numeric_attr.setMin(0.1)
        numeric_attr.setMax(2.0)
        cls.addAttribute(font_scale)

        #分辨率门中上边距
        top_border = numeric_attr.create('topBorder', 'tbd', om.MFnNumericData.kBoolean, True)
        numeric_attr.setNiceNameOverride(u'分辨率门上遮罩')
        cls.update_attr_properties(numeric_attr)
        cls.addAttribute(top_border)

        #分辨率门中下边距
        bottom_border = numeric_attr.create('buttomBorder', 'bbd', om.MFnNumericData.kBoolean, True)
        numeric_attr.setNiceNameOverride(u'分辨率门下遮罩')
        cls.update_attr_properties(numeric_attr)
        cls.addAttribute(bottom_border)

        #边框颜色
        border_color = numeric_attr.createColor('borderColor', 'bc')
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setNiceNameOverride(u'分辨率门遮罩颜色')
        numeric_attr.default = (0.0, 0.0, 0.0)
        cls.addAttribute(border_color)

        #边框透明度
        border_alpha = numeric_attr.create('borderAlpha', 'ba', om.MFnNumericData.kFloat, 1.0)
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setNiceNameOverride(u'分辨率门遮罩透明度')
        numeric_attr.setMin(0.0)
        numeric_attr.setMax(1.0)
        cls.addAttribute(border_alpha)

        #边框缩放
        border_scale = numeric_attr.create('borderScale', 'bs', om.MFnNumericData.kFloat, 1.0)
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setNiceNameOverride(u'分辨率门遮罩缩放')
        numeric_attr.setMin(0.5)
        numeric_attr.setMax(2.0)
        cls.addAttribute(border_scale)

        #计数器填充
        counter_padding = numeric_attr.create('counterPadding', 'cpd', om.MFnNumericData.kShort, 4)
        numeric_attr.setNiceNameOverride(u'帧数填充')
        cls.update_attr_properties(numeric_attr)
        numeric_attr.setMin(1)
        numeric_attr.setMax(6)
        cls.addAttribute(counter_padding)

    @classmethod
    def update_attr_properties(cls, attr):
        attr.writable = True#属性可写
        attr.storable = True#可储存
        if attr.type() == om.MFn.kNumericAttribute:#如果是数字类型属性
            attr.keyable = True #可k帧

    def __init__(self):
        super(DongShotMaskLocator, self).__init__()

    def excludeAsLocator(self):
        return False



class DongShotMaskData(om.MUserData):
    """
    用户数据缓存
    """
    def __init__(self):
        super(DongShotMaskData, self).__init__(False)
        self.parsed_fields = []

        self.current_time = 0
        self.counter_padding = 4

        self.font_name = "Consolas"#字符字体
        self.font_color = om.MColor((1.0, 1.0, 1.0))
        self.font_scale = 1.0
        self.text_padding = 10#左右侧字符距离分辨率门边界的距离

        self.top_border = True
        self.bottom_border = True
        self.border_color = om.MColor((0.0, 0.0, 0.0))
        self.border_scale = 1.0

        self.vp_width = 0#相机整体可视像素，即相机视图的右上角。原点是整个相机视图的原点
        self.vp_height = 0

        self.mask_width = 0#分辨率门遮罩的的像素尺寸。原点是分辨率门的起始渲染原点，而不是整个相机视图的起始原地
        self.mask_height = 0

    def __str__(self):
        output = ''
        output += u'text：{}\n'.format(self.parsed_fields)

        output += u'Current Time：{}\n'.format(self.current_time)
        output += u'Counter Padding：{}\n'.format(self.counter_padding)

        output += u'Font Color：{}\n'.format(self.font_color)
        output += u'Font Scale：{}\n'.format(self.font_scale)
        output += u'Text Padding：{}\n'.format(self.text_padding)

        output += u'Top Border：{}\n'.format(self.top_border)
        output += u'Bottom Border：{}\n'.format(self.bottom_border)
        output += u'Border Color：{}\n'.format(self.border_color)

        return output.encode('unicode_escape').decode()


class DongMaskDrawOverride(omr.MPxDrawOverride):
    """
    MPxDrawOverride定义了自定义的绘制覆盖逻辑
    """
    NAME = "donghotmask_draw_override"

    @staticmethod
    def camera_transform_name(camera_path):
        camera_transform = camera_path.transform()
        if camera_transform:
            return om.MFnTransform(camera_transform).name()
        return ''

    @staticmethod
    def camera_shape_name(camera_path):
        camera_shape = camera_path.node()
        if camera_shape:
            return om.MFnCamera(camera_shape).name()
        return ''

    @staticmethod
    def creator(obj):
        return DongMaskDrawOverride(obj)

    def __init__(self, obj):
        super(DongMaskDrawOverride, self).__init__(obj, None)

        self.parsed_fields = []

    def supportedDrawAPIs(self):
        return (omr.MRenderer.kAllDevices)

    def hasUIDrawables(self):
        return True

    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data):
        """
        绘图准备
        :param obj_path:创建的自定义节点名
        :param camera_path:当前使用的相机shape名
        :param frame_context:包含当前渲染帧的一些全局信息
        :param old_data:用户信息类对象
        :return:
        """
        data = old_data
        if not isinstance(data, DongShotMaskData):
            data = DongShotMaskData()#旧名变新名

        dag_fn = om.MFnDagNode(obj_path)#自定义节点对象
        camera_name = dag_fn.findPlug('camera', False).asString()
        #相机名填入非场景内的相机变换名称或为空都会对所有相机做绘制
        if camera_name and self.camera_exists(camera_name) and not self.is_camera_match(camera_path, camera_name):
            return None#当属性中的旧相机名对象与新相机名对象相同时不做处理

        #向用户信息类中的属性取值，从节点的属性中
        data.current_time = int(mc.currentTime(q=True))
        data.counter_padding = dag_fn.findPlug('counterPadding', False).asInt()
        data.text_padding = dag_fn.findPlug('textPadding', False).asInt()
        data.font_name = dag_fn.findPlug('fontName', False).asString()

        r = dag_fn.findPlug('fontColorR', False).asFloat()
        g = dag_fn.findPlug('fontColorG', False).asFloat()
        b = dag_fn.findPlug('fontColorB', False).asFloat()
        a = dag_fn.findPlug('fontAlpha', False).asFloat()
        data.font_color = om.MColor((r, g, b, a))
        data.font_scale = dag_fn.findPlug('fontScale', False).asFloat()

        r = dag_fn.findPlug('borderColorR', False).asFloat()
        g = dag_fn.findPlug('borderColorG', False).asFloat()
        b = dag_fn.findPlug('borderColorB', False).asFloat()
        a = dag_fn.findPlug('borderAlpha', False).asFloat()
        data.border_color = om.MColor((r, g, b, a))
        data.border_scale = dag_fn.findPlug('borderScale', False).asFloat()

        data.top_border = dag_fn.findPlug('topBorder', False).asBool()
        data.bottom_border = dag_fn.findPlug('buttomBorder', False).asBool()

        #获取相机视图的尺寸，原点在左上角。[0, 0, 宽像素个数, 高像素个数]
        vp_x, vp_y, data.vp_width, data.vp_height = frame_context.getViewportDimensions()
        if not (data.vp_width and data.vp_height):#如果相机尺寸为0
            return None
        data.mask_width, data.mask_height = self.get_mask_width_height(camera_path, data.vp_width, data.vp_height)
        if not (data.mask_width and data.mask_height):
            return None

        data.parsed_fields = []#向字符列表中填入字符，方便绘制字符时取用
        for inf in DongShotMaskLocator.TEXT_ATTR:
            orig_text = dag_fn.findPlug(inf[0], False).asString()#获取节点中该属性的值
            parsed_text = self.parse_text(orig_text, camera_path, data)
            data.parsed_fields.append(parsed_text)

        return data#不同时返回新用户信息

    def get_mask_width_height(self, camera_path, vp_width, vp_height):
        """
        获取遮罩的宽高
        :param camera_path:相机对象
        :param vp_width: #相机视图宽度（像素）
        :param vp_height:#相机视图高度
        :return:分辨率门的最大尺寸在整个相机视图中的像素位置
        """
        camera_fn = om.MFnCamera(camera_path)
        device_aspect_ratio = mc.getAttr('defaultResolution.deviceAspectRatio')#宽高比
        camera_aspect_ratio = camera_fn.aspectRatio()
        vp_aspect_ratio = vp_width/float(vp_height)
        scale = 1.0

        #overscan属性的值是渲染框某边到相机视图框边界的比值，未打开分辨率门时为1，打开时默认为1.3。该属性可以在相机shape的displayOptions中看到
        #camera_fn.filmFit是指相机shape的fitResolutionGate枚举属性。Horizontal：保证宽为overscan的比值；Vertical：保证高为overscan的比值
        if camera_fn.filmFit == om.MFnCamera.kHorizontalFilmFit:#锁宽度值时
            mask_width = vp_width/camera_fn.overscan#打开遮罩后，分辨率门的渲染尺寸
            mask_height = mask_width/device_aspect_ratio
        elif camera_fn.filmFit == om.MFnCamera.kVerticalFilmFit:#锁高度值时
            mask_height = vp_height/camera_fn.overscan
            mask_width = mask_height*device_aspect_ratio
        elif camera_fn.filmFit == om.MFnCamera.kFillFilmFit:#填充，分辨率门可能会直接顶到视图边界
            if vp_aspect_ratio<device_aspect_ratio:
                if camera_aspect_ratio<device_aspect_ratio:
                    scale = camera_aspect_ratio/vp_aspect_ratio
                else:
                    scale = device_aspect_ratio/vp_aspect_ratio
            elif camera_aspect_ratio>device_aspect_ratio:
                scale = device_aspect_ratio/camera_aspect_ratio

            mask_width = vp_width / camera_fn.overscan*scale
            mask_height = mask_width / device_aspect_ratio
        elif camera_fn.filmFit == om.MFnCamera.kOverscanFilmFit:#保持最小边距，分辨率门与视图边界最接近的方向也会保持最小距离
            if vp_aspect_ratio<device_aspect_ratio:
                if camera_aspect_ratio<device_aspect_ratio:
                    scale = camera_aspect_ratio/vp_aspect_ratio
                else:
                    scale = device_aspect_ratio/vp_aspect_ratio
            elif camera_aspect_ratio>device_aspect_ratio:
                scale = device_aspect_ratio/camera_aspect_ratio

            mask_height = vp_height / camera_fn.overscan/scale
            mask_width = mask_height * device_aspect_ratio
        else:
            om.MGlobal.displayError(u'不支持的拟合分辨率门：{}。'.format(camera_fn.filmFit))
            return None, None

        return mask_width, mask_height

    def addUIDrawables(self, obj_path, draw_manager, frame_context, data):
        """
        负责所有绘制操作
        :param obj_path:
        :param draw_manager:
        :param frame_context:
        :param data:
        :return:
        """
        if not (data and isinstance(data, DongShotMaskData)):
            return
        #相机视图的原点(0, 0)在左下角
        vp_half_width = 0.5*data.vp_width#相机视图的一半宽
        vp_half_height = 0.5*data.vp_height#相机视图的一半高

        mask_half_width = 0.5*data.mask_width#分辨率门的一半宽
        mask_x = vp_half_width-mask_half_width#遮罩横向x的起始点

        mask_half_height = 0.5*data.mask_height#分辨率门的一半高
        mask_bottom_y = vp_half_height-mask_half_height#遮罩竖向y的起始点
        mask_top_y = vp_half_height+ mask_half_height#分辨率门最下方的高

        border_height = int(0.05 * data.mask_height*data.border_scale)#分辨率门遮罩的高度
        background_size = (int(data.mask_width), border_height)
        font_size = int(0.85*border_height*data.font_scale)

        draw_manager.beginDrawable()#开始绘
        #绘制分辨率门内的遮罩
        if data.top_border:#下面的遮罩，因为原点在左上角，所以y轴高值在下方。
            #由于要在同一个位置绘制两个内容（这里的遮罩和下面的文字）所以在MPoint中加入的0.1用来让api知道谁在谁的下面。值越小，被绘制内容越靠前；值越大，越在底层
            self.draw_border(draw_manager, om.MPoint(mask_x, mask_top_y-border_height, 0.1), background_size, data.border_color)
        if data.bottom_border:#上方遮罩。
            self.draw_border(draw_manager, om.MPoint(mask_x, mask_bottom_y, 0.1), background_size, data.border_color)

        #绘制分辨率门内遮罩上的字符
        draw_manager.setFontName(data.font_name)
        draw_manager.setFontSize(font_size)

        #绘制视图下方的字符
        self.draw_label(draw_manager, om.MPoint(mask_x+data.text_padding, mask_top_y - border_height, 0.0), data, 0,
                        omr.MUIDrawManager.kLeft, background_size)
        self.draw_label(draw_manager, om.MPoint(vp_half_width, mask_top_y-border_height, 0.0), data, 1,
                        omr.MUIDrawManager.kCenter, background_size)
        self.draw_label(draw_manager, om.MPoint(mask_x +data.mask_width- data.text_padding, mask_top_y - border_height, 0.0), data, 2,
                        omr.MUIDrawManager.kRight, background_size)
        #绘制视图上方的字符
        self.draw_label(draw_manager, om.MPoint(mask_x + data.text_padding, mask_bottom_y, 0.0), data, 3,
                        omr.MUIDrawManager.kLeft, background_size)
        self.draw_label(draw_manager, om.MPoint(vp_half_width, mask_bottom_y, 0.0), data, 4,
                        omr.MUIDrawManager.kCenter, background_size)
        self.draw_label(draw_manager, om.MPoint(mask_x + data.mask_width - data.text_padding, mask_bottom_y, 0.0),
                        data, 5, omr.MUIDrawManager.kRight, background_size)

        draw_manager.endDrawable()#绘制结束

    def draw_border(self, draw_manager, position, background_size, color):
        """
        在分辨率门中绘制遮罩，因为部分显示器会裁切画面，或边缘位置相机对画面有拉伸，或字幕会占用边框一段距离
        :param draw_manager:绘制管理器对象
        :param position: 起始位置
        :param background_size:（绘制宽度，绘制高度）
        :param color: 绘制颜色
        :return:
        """
        #起始位置，文字内容，文字排版位置，背景图尺寸，背景图颜色
        draw_manager.text2d(position, ' ', alignment=omr.MUIDrawManager.kLeft, backgroundSize=background_size, backgroundColor=color)

    def draw_label(self, draw_manager, position, data, data_index, alignment, background_size):
        if data.parsed_fields[data_index]['image_path']:#当绘制内容为图像时
            self.draw_image(draw_manager, position, data, data_index, alignment, background_size)
            return

        text = data.parsed_fields[data_index]['text']
        draw_manager.setColor(data.font_color)
        if text:#绘制字符，字符背景为透明
            draw_manager.text2d(position, text, alignment=alignment, backgroundSize=background_size, backgroundColor=om.MColor((0.0, 0.0, 0.0, 0.0)))

    def draw_image(self, draw_manager, position, data, data_index, alignment, background_size):
        texture_manager = omr.MRenderer.getTextureManager()
        texture = texture_manager.acquireTexture(data.parsed_fields[data_index]['image_path'])#获取图片文件路径
        if not texture:
            om.MGlobal.displayError(u'不支持的文件格式{}'.format(data.parsed_fields[data_index]['image_path']))
            return

        draw_manager.setTexture(texture)
        draw_manager.setTextureSampler(omr.MSamplerState.kMinMagMipLinear, omr.MSamplerState.kTexClamp)
        draw_manager.setTextureMask(omr.MBlendState.kRGBAChannels)
        draw_manager.setColor(om.MColor((1.0, 1.0, 1.0, data.font_color.a)))

        texture_desc = texture.textureDescription()
        scale_y = (0.5*background_size[1]) - 2
        scale_x = scale_y/texture_desc.fHeight*texture_desc.fWidth#通过图片在遮罩中的高度计算出图片应有的宽度

        if alignment == omr.MUIDrawManager.kLeft:
            position = om.MPoint(position.x+scale_x, position.y +int(0.5*background_size[1]), position.z)
        elif alignment == omr.MUIDrawManager.kRight:
            position = om.MPoint(position.x-scale_x, position.y +int(0.5*background_size[1]), position.z)
        else:
            position = om.MPoint(position.x, position.y +int(0.5*background_size[1]), position.z)

        draw_manager.rect2d(position, om.MVector(0.0, 1.0, 0.0), scale_x, scale_y, True)

    def get_scene_name(self):
        scene_name = mc.file(q=True, sn=True, shn=True)
        if scene_name:
            scene_name = os.path.splitext(scene_name)[0]
        else:
            scene_name = u'未知场景'
        return scene_name

    def get_date(self):
        return datetime.date.today().strftime('%Y/%m/%d')

    def get_image(self, image_path):
        image_path = image_path.strip()#移除字符串头尾指定的字符（默认为空格或换行符）或字符序列
        if os.path.exists(image_path):
            return image_path, ''
        return '', u'图像不存在'

    def camera_exists(self, name):
        dg_iter = om.MItDependencyNodes(om.MFn.kCamera)
        while not dg_iter.isDone():
            camera_path = om.MDagPath.getAPathTo(dg_iter.thisNode())
            if self.is_camera_match(camera_path, name):
                return True

            dg_iter.next()
        return False

    def is_camera_match(self, camera_path, name):
        if self.camera_transform_name(camera_path) == name or self.camera_shape_name(camera_path) == name:
            return True
        return False

    def parse_text(self, orig_text, camera_path, data):
        image_path = ''
        text = orig_text#文字输入框中的字符值

        if '{counter}' in text:
            text = text.replace('{counter}', '{0}'.format(str(data.current_time).zfill(data.counter_padding)))
        if '{scene}' in text:
            text = text.replace('{scene}', self.get_scene_name())
        if '{date}' in text:
            text = text.replace('{date}', self.get_date())
        if '{camera}' in text:
            text = text.replace('{camera}', self.camera_transform_name(camera_path))

        stripped_text = text.strip()#移除字符串头尾指定的字符（默认为空格或换行符）或字符序列
        if stripped_text.startswith('{image=') and stripped_text.endswith('}'):
            image_path, text = self.get_image(stripped_text[7:-1])

        return {'text': text, 'image_path':image_path}



def initializePlugin(obj):
    """
    """
    plugin_fn = om.MFnPlugin(obj, "dong", "1.0.0", "Any")

    try:
        plugin_fn.registerNode(DongShotMaskLocator.NAME,
                               DongShotMaskLocator.TYPE_ID,
                               DongShotMaskLocator.creator,
                               DongShotMaskLocator.initialize,
                               om.MPxNode.kLocatorNode,
                               DongShotMaskLocator.DRAW_DB_CLASSIFICATION)
        print(u'插件{}已加载'.format(DongShotMaskLocator.NAME))
    except:
        om.MGlobal.displayError(u"节点注册失败: {0}".format(DongShotMaskLocator.NAME))

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(DongShotMaskLocator.DRAW_DB_CLASSIFICATION,
                                                      DongShotMaskLocator.DRAW_REGISTRANT_ID,
                                                      DongMaskDrawOverride.creator)
    except:
        om.MGlobal.displayError(u"无法注册绘制覆盖: {0}".format(DongMaskDrawOverride.NAME))


def uninitializePlugin(obj):
    """
    """
    plugin_fn = om.MFnPlugin(obj)

    try:
        omr.MDrawRegistry.deregisterDrawOverrideCreator(DongShotMaskLocator.DRAW_DB_CLASSIFICATION, DongShotMaskLocator.DRAW_REGISTRANT_ID)
    except:
        om.MGlobal.displayError(u"无法取消注册绘制覆盖: {0}".format(DongMaskDrawOverride.NAME))

    try:
        plugin_fn.deregisterNode(DongShotMaskLocator.TYPE_ID)
    except:
        om.MGlobal.displayError(u"注销节点失败: {0}".format(DongShotMaskLocator.NAME))


if __name__ == "__main__":

    mc.file(f=True, new=True)

    plugin_name = "maskNode.py.py"
    mc.evalDeferred('if cmds.pluginInfo("{0}", q=True, loaded=True): cmds.unloadPlugin("{0}")'.format(plugin_name))
    mc.evalDeferred('if not cmds.pluginInfo("{0}", q=True, loaded=True): cmds.loadPlugin("{0}")'.format(plugin_name))

    mc.evalDeferred('cmds.createNode("DongShotMask")')
