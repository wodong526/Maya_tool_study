# coding=gbk
#作者：woDong
#QQ: 1915367400
#Github: https://github.com/wodong526
#Bilibili: https://space.bilibili.com/381417672
#Gitee: https://gitee.com/woDong_study
#时间：2024/9/16, 上午3:45
#文件：TransferBlendShape

import os
import json
from fnmatch import translate

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance

_version = '1.1.1'


class TransferError(Exception):
    pass


def _from_target_data_get_nice_info(data):
    """
    将整体目标体信息重组为建议的目标体信息
    :param data:
    :return: {bs节点名: {目标体名: {点id名: [...]}, 'conn': ...}}
    """
    bs_nam = list(data.keys())[0]
    tag_dir = {}
    for tag in data.values():
        for tag_nam, tag_val in tag.items():
            if tag_nam not in tag_dir.keys():
                tag_dir[tag_nam] = tag_val
            else:
                tag_dir['{}_dup'.format(tag_nam)] = tag_val
    return bs_nam, tag_dir


##########文件IO工具类############
class CoreFile(object):
    @classmethod
    def save_json_data(cls, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)


##########Maya工具类############
class CoreMaya(object):
    @staticmethod
    def _from_bs_get_tag_info(bs):
        nam_lis = mc.aliasAttr(bs, q=True)[::2]
        con_lis = []
        for tag in nam_lis:
            plug = mc.listConnections('{}.{}'.format(bs, tag), d=False, p=True)
            con_lis.append(plug[0] if plug else None)

        return nam_lis, mc.aliasAttr(bs, q=True)[1::2], con_lis

    @staticmethod
    def _from_mod_get_blend_shape(mod, bs_nam):
        # type: (str, str) -> str
        """
        获取模型上的bs节点名，如果没有则创建为指定的bs名
        :param mod: 要获取的bs节点的模型名
        :param bs_nam: 需要被创建的bs节点名
        :return: 获取到mod模型的bs节点名
        """
        bs = mc.ls(mc.listHistory(mod), typ='blendShape')
        if not bs:
            bs = mc.blendShape(mod, n='{}_blendShape'.format(mod) if mc.objExists(bs_nam) else bs_nam, at=True)
        return bs[0]

    @staticmethod
    def _do_blend_shape_add_target(bs, tag_nam):
        # type: (str, str) -> int
        """
        向指定bs节点添加一个指定名称的目标体
        :param bs: 指定的bs节点名
        :param tag_nam: 要添加的目标体简名
        :return: 添加的目标体的序号
        """
        tag_index = mm.eval('string $duplicateTargets[];'
                            'doBlendShapeAddTarget("{}", 1, 2, "", 0, 0, $duplicateTargets);'.format(bs))[0]
        tag_lis = mc.listAttr('{}.w'.format(bs), k=True, m=True)
        if tag_lis[tag_index][0] != tag_nam and tag_nam not in tag_lis:
            mm.eval('blendShapeRenameTargetAlias {} {} {};'.format(bs, tag_index, tag_nam))

        mc.setAttr('{}.w[{}]'.format(bs, tag_index), 0)
        mm.eval('updateBlendShapeEditHUD;')
        return tag_index

    @classmethod
    def get_select_mod(cls):
        # type: () -> [str]
        """
        获取选中列表中所有的模型
        :return:
        """
        trs_lis = []
        for trs in mc.ls(sl=True, typ='transform'):
            shape = mc.listRelatives(trs, s=True)
            if shape and mc.objectType(shape[0]) == 'mesh':
                trs_lis.append(trs)

        if trs_lis:
            return trs_lis
        else:
            raise TransferError('选择对象中没有模型对象', 'error')

    @classmethod
    def get_target_translate_info(cls, bs, i):
        # type: (str, int) -> tuple[[str], [tuple[int, int, int, int]]]
        """
        通过bs节点与目标体序号获取目标体操作的点与点的位移信息
        :param bs: bs节点
        :param i: 目标体序号
        :return: (点id列表， 变换信息列表)
        """
        components = mc.getAttr('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[6000].inputComponentsTarget'
                                .format(bs, i))  # 获取移动了的点的id
        translate = mc.getAttr('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[6000].inputPointsTarget'
                               .format(bs, i))  # 获取每个要移动的点移动的位移，格式为[x, y, z, 1(切线)]
        return components, translate

    @classmethod
    def set_target_translate_info(cls, bs, index, components, translate):
        # type: (str, int, list, list) -> None
        """
        通过bs节点与目标体序号获取目标体操作的点与点的位移信息
        :param bs: bs节点
        :param index: 要设置的目标体的序号
        :param components: 目标体的点id列表
        :param translate: 目标体各点的位移列表
        :return: (点id列表， 变换信息列表)
        """
        mc.setAttr('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[6000].inputComponentsTarget'
                   .format(bs, index), components.__len__(), *components, typ='componentList')  # 获取移动了的点的id
        mc.setAttr('{}.inputTarget[0].inputTargetGroup[{}].inputTargetItem[6000].inputPointsTarget'
                   .format(bs, index), translate.__len__(), *translate,
                   typ='pointArray')  # 获取每个要移动的点移动的位移，格式为[x, y, z, 1(切线)]

    @classmethod
    def get_all_blend_shape(cls):
        # type: () -> {str: {str: {str: list}}}
        """
        获取场景中所有blendShape的信息
        :return: {模型transform名: {bs节点名: {'nice_nam': nam_lis, 'root_nam': rot_lis, 'conn_lis': con_lis}}}
        """
        ret_dir = {}
        for bs in mc.ls(typ='blendShape'):
            _shape = mc.blendShape(bs, q=True, g=True)
            trs = mc.listRelatives(_shape, p=True)[0]

            nam_lis, rot_lis, con_lis = cls._from_bs_get_tag_info(bs)
            if trs not in ret_dir.keys():
                ret_dir[trs] = {}
            ret_dir[trs][bs] = {'nice_nam': nam_lis, 'root_nam': rot_lis, 'conn_lis': con_lis}

        return ret_dir

    @classmethod
    def get_select_blend_shape(cls):
        # type: () -> {str: {str: {str: list}}}
        """
        获取选中模型的所有blendShape信息
        :return: {模型transform名: {bs节点名: {'nice_nam': nam_lis, 'root_nam': rot_lis, 'conn_lis': con_lis}}}
        """
        ret_dir = {}
        for shape in cls.get_select_mod():
            for bs in mc.ls(mc.listHistory(shape), typ='blendShape'):
                _shape = mc.blendShape(bs, q=True, g=True)
                trs = mc.listRelatives(_shape, p=True)[0]

                nam_lis, rot_lis, con_lis = cls._from_bs_get_tag_info(bs)
                if trs not in ret_dir.keys():
                    ret_dir[trs] = {}
                ret_dir[trs][bs] = {'nice_nam': nam_lis, 'root_nam': rot_lis, 'conn_lis': con_lis}

        return ret_dir

    @classmethod
    def select_obj(cls, trs):
        if mc.objExists(trs):
            mc.select(trs)
        else:
            cls.output_info('对象{}不存在'.format(trs), 'error')

    @classmethod
    def get_scene_path(cls):
        return mc.file(q=True, exn=True)

    @classmethod
    def output_info(cls, info, typ='info'):
        if typ == 'info':
            om.MGlobal.displayInfo(info)
        elif typ == 'warning':
            om.MGlobal.displayWarning(info)
        elif typ == 'error':
            mc.error(info)

    @classmethod
    def set_blend_shape(cls, mod, tag_info, is_connect):
        # type: (str, dict, bool) -> None
        """
        向指定模型添加目标体
        :param mod: 模型名
        :param tag_info: 目标体信息
        :param is_connect: 是否链接上下游
        :return:
        """
        sor_bs_name, bs_info = _from_target_data_get_nice_info(tag_info)
        new_bs_nam = CoreMaya._from_mod_get_blend_shape(mod, sor_bs_name)
        for tag, tag_val in bs_info.items():
            index = cls._do_blend_shape_add_target(new_bs_nam, tag)
            components = tag_val['components']
            translate = tag_val['translates']

            cls.set_target_translate_info(new_bs_nam, index, components, translate)
            if is_connect and tag_val['conn']:
                plug_nam = mc.listAttr('{}.w'.format(new_bs_nam), k=True, m=True)[index]
                if mc.objExists(tag_val['conn']):
                    mc.connectAttr(tag_val['conn'], '{}.{}'.format(new_bs_nam, plug_nam))
                else:
                    cls.output_info('源目标体{}的现目标体{}的驱动属性{}不存在'.format(tag, plug_nam, tag_val['conn']),
                                    'warning')

    @classmethod
    def undo_info(cls, typ):
        # type: (str) -> None
        """
        创建撤销块
        :param typ:生成撤销还是关闭撤销
        :return:
        """
        if typ == 'open':
            mc.undoInfo(ock=True)
        elif typ == 'close':
            mc.undoInfo(cck=True)
        else:
            cls.output_info('无效的参数：{}'.format(typ), 'error')


##########UI类############
class _IconLabel(QLabel):
    def __init__(self, icon, parent=None):
        super(_IconLabel, self).__init__(parent)
        self._image = QImage(icon)
        self._width = self._image.width()
        self._height = self._image.height()

    def paintEvent(self, e):
        super(_IconLabel, self).paintEvent(e)
        painter = QPainter(self)
        if self.width() > self._width or self.height() > self._height:
            painter.drawImage((self.width() - self._width) // 2, (self.height() - self._height) // 2, self._image)
        else:
            painter.drawImage(0, 0, self._image)


class ListWidget(QScrollArea):
    def __init__(self, parent=None):
        QScrollArea.__init__(self, parent)
        self.setWidgetResizable(True)

        self.create_widget()
        self.create_layout()

    def create_widget(self):
        self.main_widget = QWidget(self)
        self.main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setWidget(self.main_widget)

    def create_layout(self):
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(3, 3, 3, 3)
        self.main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

    def add_item(self, item):
        self.main_layout.addWidget(item)

    def count(self):
        # type: () -> int
        """
        获取空间中项的数量
        :return:
        """
        return self.main_layout.count()

    def item(self, i):
        # type: (int) -> QWidget
        """
        通过索引获取子项
        :param i: 要获取的项的索引
        :return: 控件
        """
        return self.main_layout.itemAt(i).widget()

    def items(self):
        # type: () -> list[QWidget]
        """
        获取所有子项
        :return: [控件1, 控件2, ...]
        """
        return [self.main_layout.itemAt(i).widget() for i in range(self.main_layout.count())]

    def clear(self):
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child is not None:
                if child.widget() is not None:
                    child.widget().deleteLater()


class ImportTargetWidget(QWidget):
    checked = Signal()

    def __init__(self, target, components_lis, translates_lis, dic_conn, parent=None):
        # type: (str, list, list, str, QWidget|None) -> None
        super(ImportTargetWidget, self).__init__(parent)
        self._tag = target
        self._translates = translates_lis
        self._components = components_lis
        self._conn = dic_conn
        self._parent = parent

        self.create_widgets()
        self.create_layout()
        self.create_connects()

    def create_widgets(self):
        self.chk_switch = QCheckBox()
        self.chk_switch.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lab_icon = _IconLabel(':/target.png')
        self.lab_icon.setFixedSize(22, 17)
        self.lab_nam = QLabel(self._tag)
        self.lab_nam.setFixedHeight(24)
        self.lab_nam.setStyleSheet('background-color:#5D5D5D')
        self.lab_nam.setAlignment(Qt.AlignCenter)
        self.lab_nam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.but_ipt = QPushButton()
        self.but_ipt.setToolTip(self._conn if self._conn else 'None')
        self.but_ipt.setIcon(QIcon(':/input.png'))

    def create_layout(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.chk_switch)
        main_layout.addWidget(self.lab_icon)
        main_layout.addWidget(self.lab_nam)
        main_layout.addWidget(self.but_ipt)

    def create_connects(self):
        self.chk_switch.clicked.connect(self.checked.emit)
        self.but_ipt.clicked.connect(self._select_plug_node)

    def is_checked(self):
        return self.chk_switch.isChecked()

    def set_checked(self, check):
        # type: (bool) -> None
        self.chk_switch.setChecked(check)

    def get_target_nam(self):
        return self._tag

    def get_translate_info(self):
        # type: () -> (list, list)
        return self._components, self._translates

    def get_conn_plug(self):
        return self._conn

    def _select_plug_node(self):
        if self._conn:
            CoreMaya.select_obj(self._conn.split('.')[0])
        else:
            raise TransferError('目标体{}.{}没有上游连接节点'.format(self._parent.get_blend_shape_name(), self._tag))


class ImportBlendShapeWidget(QWidget):
    checked = Signal()

    def __init__(self, bs, data, parent=None):
        # type: (str, dict[str: dict[str: [str], str: [int, int, int, int], str: str|None]], QWidget|None) -> None
        """
        生成bs控件
        :param bs: bs节点名
        :param data: bs节点的信息；{目标体名：{components': ['vtx[id]'], 'translates': [x, y, z, 1(切线)], 'conn': 上游连接属性名|None}}
        :param parent: 父级控件
        """
        super(ImportBlendShapeWidget, self).__init__(parent)

        self._bs = bs
        self._data = data

        self.create_widgets()
        self.create_layout()
        self.create_connects()
        self._refresh_list()

    def create_widgets(self):
        self.chk_switch = QCheckBox()
        self.lab_icon = QLabel()
        self.lab_icon.setFixedSize(QSize(22, 22))
        pixmap = QPixmap(':/blendShape.png')
        scaled_pixmap = pixmap.scaled(self.lab_icon.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lab_icon.setPixmap(scaled_pixmap)
        self.but_nam = QPushButton(self._bs)
        self.but_nam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lab_tag_num = QLabel('{}个目标体'.format(self._data.__len__()))

        self.lis_target = ListWidget()
        self.lis_target.hide()

    def create_layout(self):
        layout_lab = QHBoxLayout()
        layout_lab.setSpacing(2)
        layout_lab.addWidget(self.chk_switch)
        layout_lab.addWidget(self.lab_icon)
        layout_lab.addWidget(self.but_nam)
        layout_lab.addWidget(self.lab_tag_num)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout_lab)
        main_layout.addWidget(self.lis_target)

    def create_connects(self):
        self.chk_switch.stateChanged.connect(lambda _: self.checked.emit())
        self.chk_switch.clicked.connect(self.set_bs_state)
        self.but_nam.clicked.connect(self.show_list_widget)

    def is_checked(self):
        return self.chk_switch.isChecked()

    def set_bs_state(self, state):
        self._set_target_state(state)

    def set_all_state(self, state):
        self.chk_switch.setChecked(state)
        self._set_target_state(state)

    def get_blend_shape_name(self):
        return self._bs

    def get_target_info(self):
        # type: () -> dict[str: dict[str: dict[str: [str], str: list[float, float, float, int], str: str|None]]]
        """
        获取该bs项下所有目标体信息
        :return: {bs节点名: {目标体名: {'components': ['vtx[id]'], 'translates': [x, y, z, 1(切线)], 'conn': 上游连接属性名|None}}}
        """
        bs_dir = {self._bs: {}}
        for i in range(self.lis_target.count()):
            wgt = self.lis_target.item(i)
            if not wgt.is_checked():
                continue

            components, translates = wgt.get_translate_info()
            tag_dir = {
                wgt.get_target_nam(): {'components': components, 'translates': translates, 'conn': wgt.get_conn_plug()}}
            bs_dir[self._bs].update(tag_dir)
        return bs_dir

    def _set_target_state(self, state):
        for i in range(self.lis_target.count()):
            wgt = self.lis_target.item(i)
            wgt.set_checked(state)

    def _set_check_state(self):
        for i in range(self.lis_target.count()):
            wgt = self.lis_target.item(i)
            if wgt.is_checked():
                self.chk_switch.setChecked(True)
                break
        else:
            self.chk_switch.setChecked(False)

    def show_list_widget(self):
        self.lis_target.hide() if self.lis_target.isVisible() else self.lis_target.show()

    def _refresh_list(self):
        """
        刷新目标体列表
        :return:
        """
        self.lis_target.clear()
        for tag, info in self._data.items():
            item = ImportTargetWidget(tag, info['components'], info['translates'], info['conn'], self)
            item.checked.connect(self._set_check_state)
            self.lis_target.add_item(item)


class ImportTransformWidget(QWidget):
    def __init__(self, trs, data, parent=None):
        super(ImportTransformWidget, self).__init__(parent)
        self._trs = trs
        self._data = data
        self._tag_trs = self._trs

        self.create_widgets()
        self.create_layout()
        self.create_connects()
        self._refresh_list()

    def create_widgets(self):
        self.chk_switch = QCheckBox()
        self.but_icon = QPushButton()
        self.but_icon.setIcon(QIcon(':/mesh.svg'))
        self.but_icon.setIconSize(QSize(14, 14))
        self.but_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.but_nam = QPushButton('{} --> {}'.format(self._trs, self._tag_trs))
        self.but_nam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.but_rename = QPushButton()
        self.but_rename.setIcon(QIcon(':/renamePreset.png'))
        self.lab_bs_num = QLabel('{}个bs'.format(self._data.__len__()))
        self.lab_bs_num.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.lis_bs = ListWidget()

    def create_layout(self):
        layout_lab = QHBoxLayout()
        layout_lab.setSpacing(2)
        layout_lab.addWidget(self.chk_switch)
        layout_lab.addWidget(self.but_icon)
        layout_lab.addWidget(self.but_nam)
        layout_lab.addWidget(self.but_rename)
        layout_lab.addWidget(self.lab_bs_num)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout_lab)
        main_layout.addWidget(self.lis_bs)

    def create_connects(self):
        self.chk_switch.clicked.connect(self.check_state_change)
        self.but_icon.clicked.connect(self._select_mod)
        self.but_nam.clicked.connect(self._show_list_widget)
        self.but_rename.clicked.connect(self._rename_dialog)

    def check_state_change(self, state):
        for i in range(self.lis_bs.count()):
            wgt = self.lis_bs.item(i)
            wgt.set_all_state(state)

    def is_input(self):
        return self.chk_switch.isChecked()

    def get_transform_name(self):
        """
        获取该模型项的目标模型名
        :return:
        """
        return self._tag_trs

    def get_blend_shape_info(self):
        # type: () -> dict[str: dict[str: dict[str: dict[str: [str], str: list[float, float, float, int], str: str|None]]]]
        """
        获取该模型项的所有启用的blendShape的信息
        :return:{目标模型名：{bs节点名：{目标体名: {'components': ['vtx[id]'], 'translates': [x, y, z, 1(切线)], 'conn': 上游连接属性名|None}}}}
        """
        bs_dir = {}
        for i in range(self.lis_bs.count()):
            wgt = self.lis_bs.item(i)
            if not wgt.is_checked():
                continue
            bs_dir.update(wgt.get_target_info())

        return {self._tag_trs: bs_dir}

    def _select_mod(self):
        CoreMaya.select_obj(self._tag_trs)

    def _show_list_widget(self):
        """
        显示blendShape列表
        :return:
        """
        self.lis_bs.hide() if self.lis_bs.isVisible() else self.lis_bs.show()

    def _rename_dialog(self):
        """
        生成字符串输入对话框，修改接受bs数据的模型名
        :return:
        """
        txt, ok = QInputDialog.getText(self, '输入要给定模型名', '{} --> '.format(self._trs), text=self._tag_trs)
        if ok and txt:
            self._tag_trs = txt
            self.but_nam.setText('{} --> {}'.format(self._trs, self._tag_trs))

    def _set_check_state(self):
        for i in range(self.lis_bs.count()):
            wgt = self.lis_bs.item(i)
            if wgt.is_checked():
                self.chk_switch.setChecked(True)
                break
        else:
            self.chk_switch.setChecked(False)

    def _refresh_list(self):
        self.lis_bs.clear()
        for bs, bs_info in self._data.items():
            bs_widget = ImportBlendShapeWidget(bs, bs_info, self)
            bs_widget.checked.connect(self._set_check_state)
            self.lis_bs.add_item(bs_widget)


class ImportWidget(QWidget):
    def __init__(self, parent=None):
        super(ImportWidget, self).__init__(parent)

        self._data_lis = []

        self.create_widgets()
        self.create_layout()
        self.create_connects()

    def create_widgets(self):
        self.but_input_data = QPushButton('导入blendShape数据')
        self.lis_trs = ListWidget(self)

        self.chk_conn = QCheckBox('链接目标体驱动')
        self.but_input_all = QPushButton('按名称导入')
        self.but_input_select = QPushButton('全部导入到选中模型')

    def create_layout(self):
        layout_input = QHBoxLayout()
        layout_input.addWidget(self.but_input_all)
        layout_input.addWidget(self.but_input_select)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.but_input_data)
        main_layout.addWidget(self.lis_trs)
        main_layout.addWidget(self.chk_conn)
        main_layout.addLayout(layout_input)

    def create_connects(self):
        self.but_input_data.clicked.connect(self._input_json)
        self.but_input_all.clicked.connect(self._input_all)
        self.but_input_select.clicked.connect(self._input_select)

    def _input_json(self):
        file_path = QFileDialog.getOpenFileName(self, '选择blendShape文件', CoreMaya.get_scene_path(), '(*.json)')
        if file_path[0]:
            with open(file_path[0], "r") as f:
                self._data = json.load(f)
                self._refresh_bs_list()
        else:
            CoreMaya.output_info('没有选择有效文件', 'warning')

    def _refresh_bs_list(self):
        self.lis_trs.clear()
        if self._data:
            for trs, info in self._data.items():
                item = ImportTransformWidget(trs, info)
                item.check_state_change(True)
                self.lis_trs.add_item(item)
        else:
            raise TransferError('没有找到blendShape数据')

    def get_select_target_info(fun):
        """
        在类里面用于装饰同一个类里函数的装饰器
        :return:
        """

        def _warp(self, *args, **kwargs):
            """
            获取选中的所有目标体信息，并传递给fun
            :return:
            """
            info_dir = {}
            for wgt in self.lis_trs.items():
                if not wgt.is_input():
                    continue
                info_dir.update(wgt.get_blend_shape_info())

            try:
                CoreMaya.undo_info('open')
                fun(self, info_dir)
            finally:
                CoreMaya.undo_info('close')

        return _warp

    @get_select_target_info
    def _input_all(self, bs_info):
        for mod, bs_data in bs_info.items():
            CoreMaya.set_blend_shape(mod, bs_data, self.chk_conn.isChecked())

    @get_select_target_info
    def _input_select(self, bs_info):
        mod = CoreMaya.get_select_mod()[0]
        for _, bs_data in bs_info.items():
            CoreMaya.set_blend_shape(mod, bs_data, self.chk_conn.isChecked())


class ExportTargetItem(QWidget):
    def __init__(self, bs, nise_nam, root_nam, conn_plug, parent=None):
        super(ExportTargetItem, self).__init__(parent)

        self.bs = bs
        self.nise_nam = nise_nam
        self.root_nam = root_nam
        self.conn_plug = conn_plug

        self._comps = []
        self._translates = []

        self.create_widgets()
        self.create_layout()
        self.create_connects()

    def create_widgets(self):
        self.chk_switch = QCheckBox()
        self.chk_switch.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lab_icon = _IconLabel(':/target.png')
        self.lab_icon.setFixedSize(22, 17)
        self.lab_nam = QLabel(self.nise_nam)
        self.lab_nam.setFixedHeight(24)
        self.lab_nam.setStyleSheet('background-color:#5D5D5D')
        self.lab_nam.setAlignment(Qt.AlignCenter)
        self.lab_nam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.but_ipt = QPushButton()
        self.but_ipt.setToolTip(self.conn_plug if self.conn_plug else 'None')
        self.but_ipt.setIcon(QIcon(':/input.png'))

    def create_layout(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.chk_switch)
        main_layout.addWidget(self.lab_icon)
        main_layout.addWidget(self.lab_nam)
        main_layout.addWidget(self.but_ipt)

    def create_connects(self):
        self.but_ipt.clicked.connect(self._select_plug_node)

    def _select_plug_node(self):
        if self.conn_plug:
            CoreMaya.select_obj(self.conn_plug.split('.')[0])
        else:
            raise TransferError('目标体{}.{}没有上游连接节点'.format(self.bs, self.nise_nam))

    def set_checked(self, state):
        # type: (Qt.CheckState) -> None
        """
        设置复选框状态
        :param state: 状态属性
        :return:
        """
        self.chk_switch.setCheckState(state)

    def is_checked(self):
        # type: () -> bool
        """
        获取复选框是否被选中
        :return:
        """
        return self.chk_switch.isChecked()

    def set_translate_info(self, id_lis, translate_lis):
        # type: (list, list) -> None
        """
        设置目标体的id列表和平移列表
        :param id_lis: 目标体的id列表
        :param translate_lis: 目标体的平移列表
        :return:
        """
        self._comps = id_lis
        self._translates = translate_lis

    def get_nice_name(self):
        # type: () -> str
        return self.nise_nam

    def get_translate_info(self):
        # type: () -> dict[str: [str], str: [int, int, int, int], str: str:None]
        """
        获取目标体的id列表和平移列表
        :return:{'components': ['vtx[id]', ...], 'translates': [x, y, z, 1(切线)], 'conn': 上游连接属性名|None}
        """
        return {'components': self._comps, 'translates': self._translates, 'conn': self.conn_plug}


class ExportBlendShapeWidget(QWidget):
    def __init__(self, bs, tag_info, parent=None):
        super(ExportBlendShapeWidget, self).__init__(parent)

        self._bs = bs
        self._tag_info = tag_info

        self.create_widgets()
        self.create_layout()
        self.create_connects()
        self._refresh_list()

    def create_widgets(self):
        self.but_icon = QPushButton()
        self.but_icon.setIcon(QIcon(':/blendShape.png'))
        self.but_icon.setIconSize(QSize(14, 14))
        self.but_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.but_nam = QPushButton(self._bs)
        self.but_nam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.but_select = QPushButton('ALL')
        self.lab_tag_num = QLabel('{}个目标体'.format(self._tag_info['root_nam'].__len__()))
        self.lab_tag_num.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.lis_target = ListWidget()
        self.lis_target.hide()

    def create_layout(self):
        layout_lab = QHBoxLayout()
        layout_lab.setSpacing(2)
        layout_lab.addWidget(self.but_icon)
        layout_lab.addWidget(self.but_nam)
        layout_lab.addWidget(self.but_select)
        layout_lab.addWidget(self.lab_tag_num)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout_lab)
        main_layout.addWidget(self.lis_target)

    def create_connects(self):
        self.but_icon.clicked.connect(self._select_bs)
        self.but_nam.clicked.connect(self._show_list_widget)
        self.but_select.clicked.connect(self._set_all_target_slate)

    def get_target_info(self):
        # type: () -> dict[str: dict[str: dict[str: [str], str: [int, int, int, int], str: str:None]]]
        """
        获取该blendShape节点下勾选的目标体的信息
        :return: {bs节点名：{目标体名: {'components': ['vtx[id]', ...], 'translates': [x, y, z, 1(切线)], 'conn': 上游连接属性名|None}}}
        """
        ret_dir = {}
        for i in range(self.lis_target.count()):
            wgt = self.lis_target.item(i)
            if wgt.is_checked():
                if self._bs not in ret_dir.keys():
                    ret_dir[self._bs] = {}
                ret_dir[self._bs][wgt.get_nice_name()] = wgt.get_translate_info()

        return ret_dir

    def _set_all_target_slate(self):
        """
        设置子项是否全选
        :return:
        """
        is_slate = not self._get_all_target_slate()
        for i in range(self.lis_target.count()):
            self.lis_target.item(i).set_checked(Qt.Checked if is_slate else Qt.Unchecked)

    def _get_all_target_slate(self):
        # type: () -> bool
        """
        判断子项是否全选
        :return: bool
        """
        for i in range(self.lis_target.count()):
            if not self.lis_target.item(i).is_checked():
                return False
        else:
            return True

    def _refresh_list(self):
        """
        刷新目标体列表
        :return:
        """
        self.lis_target.clear()
        index = 0
        for nic, rot, plug in zip(self._tag_info['nice_nam'], self._tag_info['root_nam'], self._tag_info['conn_lis']):
            item = ExportTargetItem(self._bs, nic, rot, plug, self)
            item.set_translate_info(*CoreMaya.get_target_translate_info(self._bs, index))
            item.set_checked(Qt.Checked)
            self.lis_target.add_item(item)
            index += 1

    def _select_bs(self):
        """
        选中blendShape节点
        :return:
        """
        CoreMaya.select_obj(self._bs)

    def _show_list_widget(self):
        """
        显示目标体列表
        :return:
        """
        self.lis_target.hide() if self.lis_target.isVisible() else self.lis_target.show()


class ExportTransformWidget(QWidget):
    def __init__(self, trs, bs_info, parent=None):
        super(ExportTransformWidget, self).__init__(parent)
        self._trs = trs
        self._bs_info = bs_info

        self.create_widgets()
        self.create_layout()
        self.create_connects()
        self._refresh_list()

    def create_widgets(self):
        self.but_icon = QPushButton()
        self.but_icon.setIcon(QIcon(':/mesh.svg'))
        self.but_icon.setIconSize(QSize(14, 14))
        self.but_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.but_nam = QPushButton(self._trs)
        self.but_nam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lab_bs_num = QLabel('{}个bs'.format(self._bs_info.__len__()))
        self.lab_bs_num.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.lis_bs = ListWidget()

    def create_layout(self):
        layout_lab = QHBoxLayout()
        layout_lab.setSpacing(2)
        layout_lab.addWidget(self.but_icon)
        layout_lab.addWidget(self.but_nam)
        layout_lab.addWidget(self.lab_bs_num)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout_lab)
        main_layout.addWidget(self.lis_bs)

    def create_connects(self):
        self.but_icon.clicked.connect(self._select_mod)
        self.but_nam.clicked.connect(self._show_list_widget)

    def get_blend_shape_info(self):
        # type: () -> dict[str: dict[str: dict[str: dict[str: [str], str: [int, int, int, int], str: str|None]]]]
        """
        获取该transform节点下勾选的blendShape节点的信息
        :return: {trs节点名：{bs节点名：{目标体名: {'components': ['vtx[id]'], 'translates': [x, y, z, 1(切线)], 'conn': 上游连接属性名|None}}}}
        """
        ret_dir = {}
        for i in range(self.lis_bs.count()):
            wgt = self.lis_bs.item(i)
            info = wgt.get_target_info()
            if info:
                if self._trs not in ret_dir.keys():
                    ret_dir[self._trs] = {}
                ret_dir[self._trs].update(info)

        return ret_dir

    def _refresh_list(self):
        self.lis_bs.clear()
        for bs, bs_info in self._bs_info.items():
            bs_widget = ExportBlendShapeWidget(bs, bs_info, self)
            self.lis_bs.add_item(bs_widget)

    def _select_mod(self):
        CoreMaya.select_obj(self._trs)

    def _show_list_widget(self):
        self.lis_bs.hide() if self.lis_bs.isVisible() else self.lis_bs.show()


class ExportWidget(QWidget):
    def __init__(self, parent=None):
        super(ExportWidget, self).__init__(parent)

        self.create_widgets()
        self.create_layout()
        self.create_connects()

    def create_widgets(self):
        self.but_get_all = QPushButton('获取场景中所有的BlendShape')
        self.but_get_ls = QPushButton('获取选中对象的BlendShape')

        self.lis_trs = ListWidget(self)

        self.cek_box = QCheckBox('记录目标体驱动')
        self.but_export = QPushButton('导出选中的目标体')

    def create_layout(self):
        layout_but = QHBoxLayout()
        layout_but.addWidget(self.but_get_all)
        layout_but.addWidget(self.but_get_ls)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(layout_but)
        main_layout.addWidget(self.lis_trs)
        main_layout.addWidget(self.cek_box)
        main_layout.addWidget(self.but_export)

    def create_connects(self):
        self.but_get_all.clicked.connect(self._get_all_bs)
        self.but_get_ls.clicked.connect(self._get_ls_bs)

        self.but_export.clicked.connect(self._export_target)

    def _get_all_bs(self):
        bs_info = CoreMaya.get_all_blend_shape()
        self._refresh_list(bs_info)

    def _get_ls_bs(self):
        bs_info = CoreMaya.get_select_blend_shape()
        self._refresh_list(bs_info)

    def _export_target(self):
        # type: () -> None
        """
        导出指定的目标体的信息到json文件
        :return:
        """
        target_info = {}
        for wgt in self.lis_trs.items():
            target_info.update(wgt.get_blend_shape_info())  # 将模型信息字典中的所有元素添加到target_info字典

        if target_info:
            self._filtration_plug(target_info)
            file_path = QFileDialog.getSaveFileName(self, '选择导出目标体的文件路径',
                                                    os.path.dirname(CoreMaya.get_scene_path()), '(*.json)')
            if file_path[0]:
                CoreFile.save_json_data(file_path[0], target_info)
            else:
                CoreMaya.output_info('没有选择有效路径', 'warning')
        else:
            raise RuntimeError('没有选中任何目标体')

    def _filtration_plug(self, data):
        # type: (dict[str: dict[str: dict[str: dict[str: [str], str: list[int, int, int, int], str: str|None]]]]) -> None
        """
        若未勾选记录上游连接，将上游连接过滤
        列表和字典均为可变类型，所以直接操作参数即可，无需返回
        :param data: {trs节点名：{bs节点名：{目标体名: {'components': ['vtx[id]'], 'translates'：[x, y, z, 1(切线)]， 'conn'：上游连接属性名|None}}}}
        """
        if not self.cek_box.isChecked():
            for trs, bs_info in data.items():
                for bs, target_info in bs_info.items():
                    for target, info in target_info.items():  # info为{'translate': trans_dir, 'conn': conn_plug}
                        info['conn'] = None

    def _refresh_list(self, bs_info):
        self.lis_trs.clear()
        for trs, bs_info in bs_info.items():
            trs_widget = ExportTransformWidget(trs, bs_info, self)
            self.lis_trs.add_item(trs_widget)


class TransferWindow(QMainWindow):
    def __init__(self):
        super(TransferWindow, self).__init__(wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget))
        self.setWindowTitle('传递blendShape工具 {}'.format(_version))
        self.resize(500, 500)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.wgt_export = ExportWidget(self)
        self.wgt_inport = ImportWidget(self)

        self.tab_wgt = QTabWidget()
        self.tab_wgt.addTab(self.wgt_export, '导出')
        self.tab_wgt.addTab(self.wgt_inport, '导入')

    def create_layout(self):
        self.setCentralWidget(self.tab_wgt)


try:
    transfer_tool.close()
except:
    pass
finally:
    transfer_tool = TransferWindow()
    transfer_tool.show()
