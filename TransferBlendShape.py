# coding=gbk
#作者：woDong
#QQ: 1915367400
#Github: https://github.com/wodong526
#Bilibili: https://space.bilibili.com/381417672
#时间：2024/9/16, 上午3:45
#文件：TransferBlendShape

import os
import json

import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from maya.app.renderSetup.views.lightEditor.enterScope import EnterLightScope
from shiboken2 import wrapInstance

class TransferError(Exception):
    pass

##########文件IO工具类############
class CoreFile(object):
    @classmethod
    def save_json_data(cls, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

##########Maya工具类############
class CoreMaya(object):
    @classmethod
    def _from_bs_get_tag_info(cls, bs):
        nam_lis = mc.aliasAttr(bs, q=True)[::2]
        con_lis = []
        for tag in nam_lis:
            plug = mc.listConnections('{}.{}'.format(bs, tag), d=False, p=True)
            con_lis.append(plug[0] if plug else None)

        return nam_lis, mc.aliasAttr(bs, q=True)[1::2], con_lis

    @classmethod
    def get_target_translate_info(cls, bs, i):
        # type: (str, int) -> tuple[list[str], list[tuple[int, int, int, int]]]
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
    def get_all_blend_shape(self):
        # type: () -> {str: {str: {str: list}}}
        """
        获取场景中所有blendShape的信息
        :return: {模型transform名: {bs节点名: {'nice_nam': nam_lis, 'root_nam': rot_lis, 'conn_lis': con_lis}}}
        """
        ret_dir = {}
        for bs in mc.ls(typ='blendShape'):
            _shape = mc.blendShape(bs, q=True, g=True)
            trs = mc.listRelatives(_shape, p=True)[0]

            nam_lis, rot_lis, con_lis = self._from_bs_get_tag_info(bs)
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
        shape_lis = []
        for trs in mc.ls(sl=True, typ='transform'):
            _shape = mc.listRelatives(trs, s=True)
            if _shape:
                shape_lis.append(_shape[0])
        if not shape_lis:
            raise TransferError('选择列表中没有模型对象')

        ret_dir = {}
        for shape in shape_lis:
            for bs in mc.ls(mc.listHistory(shape), typ='blendShape'):
                _shape = mc.blendShape(bs, q=True, g=True)
                trs = mc.listRelatives(_shape, p=True)[0]

                nam_lis, rot_lis, con_lis = self._from_bs_get_tag_info(bs)
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
            painter.drawImage((self.width()-self._width)//2, (self.height()-self._height)//2, self._image)
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

    def clear(self):
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child is not None:
                if child.widget() is not None:
                    child.widget().deleteLater()

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
        self.chk_switch.stateChanged.connect(self._check_state_change)
        self.but_icon.clicked.connect(self._select_mod)
        self.but_nam.clicked.connect(self._show_list_widget)
        self.but_rename.clicked.connect(self._rename_dialog)

    def _check_state_change(self, state):
        if state == 2:
            pass
        elif state == 0:
            pass

    def _select_mod(self):
        CoreMaya.select_obj(self._tag_trs)

    def _show_list_widget(self):
        """
        显示blendShape列表
        :return:
        """
        self.lis_bs.hide() if self.lis_bs.isVisible() else self.lis_bs.show()

    def _rename_dialog(self):
        txt, ok = QInputDialog.getText(self, '输入要给定模型名', '{} --> '.format(self._trs), text=self._tag_trs)
        if ok and txt:
            self._tag_trs = txt
            self.but_nam.setText('{} --> {}'.format(self._trs, self._tag_trs))

    def _refresh_list(self):
        pass


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

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.but_input_data)
        main_layout.addWidget(self.lis_trs)

    def create_connects(self):
        self.but_input_data.clicked.connect(self._input_json)

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
                self.lis_trs.add_item(item)
        else:
            raise TransferError('没有找到blendShape数据')

class ExportTargetItem(QWidget):
    def __init__(self, bs, nise_nam, root_nam, conn_plug, parent=None):
        super(ExportTargetItem, self).__init__(parent)

        self.bs = bs
        self.nise_nam = nise_nam
        self.root_nam = root_nam
        self.conn_plug = conn_plug

        self._id_lis = []
        self._translate_lis = []

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
        self._id_lis = id_lis
        self._translate_lis = translate_lis

    def get_nice_name(self):
        # type: () -> str
        return self.nise_nam

    def get_translate_info(self):
        # type: () -> dict[str: dict[str: list[int, int, int, int]], str: str:None]
        """
        获取目标体的id列表和平移列表
        :return:{translate: {点id: [x, y, z, 1(切线)]}, 'conn': 上游连接属性名|None}
        """
        trans_dir = {point: translate for point, translate in zip(self._id_lis, self._translate_lis)}
        return {'translate': trans_dir, 'conn': self.conn_plug}

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
        # type: () -> dict[str: dict[str: dict[str: list[int, int, int, int]], str: str|None]]
        """
        获取该blendShape节点下勾选的目标体的信息
        :return: {bs节点名：{目标体名: {点id名：[x, y, z, 1(切线)]}， conn：上游连接属性名|None}}
        """
        ret_dir = {}
        for i in range(self.lis_bs.count()):
            wgt = self.lis_bs.item(i)
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
        for i in range(self.lis_bs.count()):
            if not self.lis_bs.item(i).is_checked():
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

        self.lis_target = ListWidget()

    def create_layout(self):
        layout_lab = QHBoxLayout()
        layout_lab.setSpacing(2)
        layout_lab.addWidget(self.but_icon)
        layout_lab.addWidget(self.but_nam)
        layout_lab.addWidget(self.lab_bs_num)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout_lab)
        main_layout.addWidget(self.lis_target)

    def create_connects(self):
        self.but_icon.clicked.connect(self._select_mod)
        self.but_nam.clicked.connect(self._show_list_widget)

    def get_blend_shape_info(self):
        # type: () -> dict[str: dict[str: dict[str: dict[str: list[int, int, int, int]], str: str|None]]]
        """
        获取该transform节点下勾选的blendShape节点的信息
        :return: {trs节点名：{bs节点名：{目标体名: {点id名：[x, y, z, 1(切线)]}， conn：上游连接属性名|None}}}
        """
        ret_dir = {}
        for i in range(self.lis_bs.count()):
            wgt = self.lis_bs.item(i)
            info = wgt.get_target_info()
            if info:
                if self._trs not in ret_dir.keys():
                    ret_dir[self._trs] = {}
                ret_dir[self._trs] = info

        return ret_dir

    def _refresh_list(self):
        self.lis_target.clear()
        for bs, bs_info in self._bs_info.items():
            bs_widget = ExportBlendShapeWidget(bs, bs_info, self)
            self.lis_target.add_item(bs_widget)

    def _select_mod(self):
        CoreMaya.select_obj(self._trs)

    def _show_list_widget(self):
        self.lis_target.hide() if self.lis_target.isVisible() else self.lis_target.show()


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

        self.cek_box = QCheckBox('记录上游连接')
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
        for i in range(self.lis_trs.count()):
            wgt = self.lis_trs.item(i)
            target_info.update(wgt.get_blend_shape_info())# 将模型信息字典中的所有元素添加到target_info字典

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
        # type: (list[dict[str: dict[str: dict[str: dict[str: list[int, int, int, int]], str: str|None]]]]) -> None
        """
        若未勾选记录上游连接，将上游连接过滤
        列表和字典均为可变类型，所以直接操作参数即可，无需返回
        :param data: [{trs节点名：{bs节点名：{目标体名: {点id名：[x, y, z, 1(切线)]}， conn：上游连接属性名|None}}}]
        """
        if not self.cek_box.isChecked():
            for _info in data:
                for trs, bs_info in _info.items():
                    for bs, target_info in bs_info.items():
                        for target, info in target_info.items():# info为{'translate': trans_dir, 'conn': conn_plug}
                            info['conn'] = None

    def _refresh_list(self, bs_info):
        self.lis_trs.clear()
        for trs, bs_info in bs_info.items():
            trs_widget = ExportTransformWidget(trs, bs_info, self)
            self.lis_trs.add_item(trs_widget)


class TransferWindow(QMainWindow):
    def __init__(self):
        super(TransferWindow, self).__init__(wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget))
        self.setWindowTitle('Transfer BlendShape')
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



transfer_tool = TransferWindow()
transfer_tool.show()
