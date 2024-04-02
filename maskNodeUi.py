#coding:utf-8

from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as mc
import maya.OpenMayaUI as omui


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class DongHeaderWidget(QtWidgets.QWidget):

    def __init__(self, text, parent=None):
        super(DongHeaderWidget, self).__init__(parent)

        self.setAutoFillBackground(True)
        self.set_background_color(None)

        self.text_label = QtWidgets.QLabel()
        self.text_label.setTextFormat(QtCore.Qt.RichText)
        self.text_label.setAlignment(QtCore.Qt.AlignLeft)

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.addWidget(self.text_label)

        self.set_text(text)

    def set_text(self, text):
        self.text_label.setText(text)

    def set_background_color(self, color):
        if not color:
            color = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)

        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, color)
        self.setPalette(palette)


class DongColorButton(QtWidgets.QWidget):
    color_changed = QtCore.Signal()

    def __init__(self, color=(1.0, 1.0, 1.0), parent=None):
        super(DongColorButton, self).__init__(parent)

        self.setObjectName("ZurbriggColorButton")

        self.create_control()

        self.set_size(50, 16)
        self.set_color(color)

    def create_control(self):
        window = mc.window()
        color_slider_name = mc.colorSliderGrp()

        self._color_slider_obj = omui.MQtUtil.findControl(color_slider_name)
        if self._color_slider_obj:
            self._color_slider_widget = wrapInstance(int(self._color_slider_obj), QtWidgets.QWidget)

            main_layout = QtWidgets.QVBoxLayout(self)
            main_layout.setObjectName("main_layout")
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(self._color_slider_widget)

            self._slider_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "slider")
            if self._slider_widget:
                self._slider_widget.hide()

            self._color_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "port")

            mc.colorSliderGrp(self.get_full_name(), e=True, changeCommand=partial(self.on_color_changed))

        mc.deleteUI(window, window=True)

    def get_full_name(self):
        return omui.MQtUtil.fullName(int(self._color_slider_obj))

    def set_size(self, width, height):
        self._color_slider_widget.setFixedWidth(width)
        self._color_widget.setFixedHeight(height)

    def set_color(self, color):
        mc.colorSliderGrp(self.get_full_name(), e=True, rgbValue=(color[0], color[1], color[2]))
        self.on_color_changed()

    def get_color(self):
        return mc.colorSliderGrp(self.get_full_name(), q=True, rgbValue=True)

    def on_color_changed(self, *args):
        self.color_changed.emit()  # pylint: disable=E1101


class MyComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(MyComboBox, self).__init__(parent)

    def showPopup(self):
        self.clear()
        camera_lis = mc.listCameras()
        camera_lis.insert(0, 'all')
        self.addItems(camera_lis)
        super(MyComboBox, self).showPopup()


class DongShotMaskUi(QtWidgets.QDialog):
    WINDOW_TITLE = u"遮罩创建工具"

    PLUG_IN_NAME = "maskNode"
    NODE_TYPE = "DongShotMask"

    TRANSFORM_NAME = "DongShotMask"
    SHAPE_NAME = "DongShotMaskShape"

    TEXT_LABELS = [u"上左", u"上中", u"上右", u"下左", u"下中", u"下右"]
    TEXT_ATTRIBUTES = ["topLeftText", "topCenterText", "topRightText", "bottomLeftText", "bottomCenterText",
                       "bottomRightText"]

    OPT_VAR_CAMERA = 'Dong_Camera'  #自定义全局变量名
    OPT_VAR_TEXT = "Dong_Text"
    OPT_VAR_FONT = "Dong_Font"
    OPT_VAR_FONT_COLOR = "Dong_FontColor"
    OPT_VAR_FONT_SCALE = "Dong_FontScale"
    OPT_VAR_BORDER_VISIBLE = "Dong_BorderVisible"
    OPT_VAR_BORDER_COLOR = "Dong_BorderColor"
    OPT_VAR_BORDER_SCALE = "Dong_BorderScale"
    OPT_VAR_COUNTER_PADDING = "Dong_CounterPadding"

    def __init__(self, parent=maya_main_window()):
        super(DongShotMaskUi, self).__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        if mc.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif mc.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.setMinimumWidth(320)

        self._camera_select_dialog = None

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        button_width = 60
        button_height = 18
        spin_box_width = 50

        self.camera_le = QtWidgets.QLineEdit()
        self.camera_comb = MyComboBox()
        self.camera_comb.addItem('all')

        self.text_line_edits = []
        for i in range(len(DongShotMaskUi.TEXT_LABELS)):  # pylint: disable=W0612
            self.text_line_edits.append(QtWidgets.QLineEdit())

        self.font_le = QtWidgets.QLineEdit()
        self.font_le.setEnabled(False)

        self.font_select_btn = QtWidgets.QPushButton(u"字号选择")
        self.font_select_btn.setFixedSize(button_width, button_height)

        self.font_color_btn = DongColorButton()

        self.font_alpha_dsb = QtWidgets.QDoubleSpinBox()
        self.font_alpha_dsb.setMinimumWidth(spin_box_width)
        self.font_alpha_dsb.setSingleStep(0.05)
        self.font_alpha_dsb.setMinimum(0.0)
        self.font_alpha_dsb.setMaximum(1.0)
        self.font_alpha_dsb.setValue(1.0)
        self.font_alpha_dsb.setDecimals(3)
        self.font_alpha_dsb.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)

        self.font_scale_dsb = QtWidgets.QDoubleSpinBox()
        self.font_scale_dsb.setMinimumWidth(spin_box_width)
        self.font_scale_dsb.setSingleStep(0.05)
        self.font_scale_dsb.setMinimum(0.1)
        self.font_scale_dsb.setMaximum(2.0)
        self.font_scale_dsb.setValue(1.0)
        self.font_scale_dsb.setDecimals(3)
        self.font_scale_dsb.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)

        self.top_border_cb = QtWidgets.QCheckBox(u"上方")
        self.top_border_cb.setChecked(True)
        self.bottom_border_cb = QtWidgets.QCheckBox(u"下方")
        self.bottom_border_cb.setChecked(True)

        self.border_color_btn = DongColorButton()

        self.border_transparency_dsb = QtWidgets.QDoubleSpinBox()
        self.border_transparency_dsb.setMinimumWidth(spin_box_width)
        self.border_transparency_dsb.setSingleStep(0.05)
        self.border_transparency_dsb.setMinimum(0.0)
        self.border_transparency_dsb.setMaximum(1.0)
        self.border_transparency_dsb.setValue(1.0)
        self.border_transparency_dsb.setDecimals(3)
        self.border_transparency_dsb.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)

        self.border_scale_dsb = QtWidgets.QDoubleSpinBox()
        self.border_scale_dsb.setMinimumWidth(spin_box_width)
        self.border_scale_dsb.setSingleStep(0.05)
        self.border_scale_dsb.setMinimum(0.5)
        self.border_scale_dsb.setMaximum(2.0)
        self.border_scale_dsb.setValue(1.0)
        self.border_scale_dsb.setDecimals(3)
        self.border_scale_dsb.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)

        self.counter_padding_sb = QtWidgets.QSpinBox()
        self.counter_padding_sb.setMinimumWidth(spin_box_width)
        self.counter_padding_sb.setSingleStep(1)
        self.counter_padding_sb.setMinimum(1)
        self.counter_padding_sb.setMaximum(6)
        self.counter_padding_sb.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)

        self.create_btn = QtWidgets.QPushButton(u"创建")
        self.delete_btn = QtWidgets.QPushButton(u"删除")

        self.refresh_ui()

    def create_layout(self):
        camera_layout = QtWidgets.QHBoxLayout()
        camera_layout.setSpacing(4)
        camera_layout.addWidget(self.camera_le)
        camera_layout.addWidget(self.camera_comb)

        camera_form_layout = QtWidgets.QFormLayout()
        camera_form_layout.setSpacing(2)
        camera_form_layout.addRow(u"相机", camera_layout)
        camera_form_layout.addRow(self.spacing_widget(), None)

        text_form_layout = QtWidgets.QFormLayout()
        text_form_layout.setSpacing(2)
        for i in range(len(self.text_line_edits)):
            text_form_layout.addRow(DongShotMaskUi.TEXT_LABELS[i], self.text_line_edits[i])
        text_form_layout.addRow(self.spacing_widget(), None)

        font_layout = QtWidgets.QHBoxLayout()
        font_layout.setSpacing(2)
        font_layout.addWidget(self.font_le)
        font_layout.addWidget(self.font_select_btn)

        text_color_layout = QtWidgets.QHBoxLayout()
        text_color_layout.addWidget(self.font_color_btn)
        text_color_layout.addSpacing(4)
        text_color_layout.addWidget(QtWidgets.QLabel(u"透明度"))
        text_color_layout.addWidget(self.font_alpha_dsb)
        text_color_layout.addSpacing(4)
        text_color_layout.addWidget(QtWidgets.QLabel(u"缩放"))
        text_color_layout.addWidget(self.font_scale_dsb)
        text_color_layout.addStretch()

        font_form_layout = QtWidgets.QFormLayout()
        font_form_layout.setSpacing(4)
        font_form_layout.addRow(u"字号", font_layout)
        font_form_layout.addRow(u"颜色", text_color_layout)
        font_form_layout.addRow(self.spacing_widget(), None)

        border_visibility_layout = QtWidgets.QHBoxLayout()
        border_visibility_layout.addWidget(self.top_border_cb)
        border_visibility_layout.addWidget(self.bottom_border_cb)
        border_visibility_layout.addStretch()

        border_color_layout = QtWidgets.QHBoxLayout()
        border_color_layout.addWidget(self.border_color_btn)
        border_color_layout.addSpacing(4)
        border_color_layout.addWidget(QtWidgets.QLabel(u"透明度"))
        border_color_layout.addWidget(self.border_transparency_dsb)
        border_color_layout.addSpacing(4)
        border_color_layout.addWidget(QtWidgets.QLabel(u"缩放"))
        border_color_layout.addWidget(self.border_scale_dsb)
        border_color_layout.addStretch()

        borders_form_layout = QtWidgets.QFormLayout()
        borders_form_layout.setSpacing(2)
        borders_form_layout.addRow(u"方位:", border_visibility_layout)
        borders_form_layout.addRow(u"颜色", border_color_layout)
        borders_form_layout.addRow(self.spacing_widget(), None)

        counter_padding_layout = QtWidgets.QHBoxLayout()
        counter_padding_layout.addWidget(self.counter_padding_sb)
        counter_padding_layout.addStretch()

        counter_form_layout = QtWidgets.QFormLayout()
        counter_form_layout.setSpacing(4)
        counter_form_layout.addRow(u"帧数填充", counter_padding_layout)
        counter_form_layout.addRow(self.spacing_widget(), None)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)
        button_layout.addStretch()
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.delete_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.addSpacing(6)
        main_layout.addLayout(camera_form_layout)
        main_layout.addWidget(DongHeaderWidget(u"文本"))
        main_layout.addLayout(text_form_layout)
        main_layout.addWidget(DongHeaderWidget(u"字符"))
        main_layout.addLayout(font_form_layout)
        main_layout.addWidget(DongHeaderWidget(u"遮罩"))
        main_layout.addLayout(borders_form_layout)
        main_layout.addWidget(DongHeaderWidget(u"填充"))
        main_layout.addLayout(counter_form_layout)
        main_layout.addLayout(button_layout)

    def spacing_widget(self):
        widget = QtWidgets.QWidget()
        widget.setFixedWidth(86)
        widget.setFixedHeight(0)
        return widget

    def create_connections(self):
        self.camera_le.editingFinished.connect(self.update_mask)
        self.camera_comb.activated.connect(self.set_camera_name)

        for text_le in self.text_line_edits:
            text_le.editingFinished.connect(self.update_mask)

        self.font_select_btn.clicked.connect(self.show_font_select_dialog)
        self.font_color_btn.color_changed.connect(self.update_mask)  # pylint: disable=E1101
        self.font_alpha_dsb.valueChanged.connect(self.update_mask)
        self.font_scale_dsb.valueChanged.connect(self.update_mask)

        self.top_border_cb.toggled.connect(self.update_mask)
        self.bottom_border_cb.toggled.connect(self.update_mask)
        self.border_color_btn.color_changed.connect(self.update_mask)  # pylint: disable=E1101
        self.border_transparency_dsb.valueChanged.connect(self.update_mask)
        self.border_scale_dsb.valueChanged.connect(self.update_mask)

        self.counter_padding_sb.valueChanged.connect(self.update_mask)

        self.create_btn.clicked.connect(self.create_mask)
        self.delete_btn.clicked.connect(self.delete_mask)

    def load_plugin(self):
        if not self.is_plugin_loaded():
            try:
                mc.loadPlugin(DongShotMaskUi.PLUG_IN_NAME)
            except:
                mc.error('找不到插件{}'.format(DongShotMaskUi.PLUG_IN_NAME))
                return False
        return True

    def is_plugin_loaded(self):
        return mc.pluginInfo(DongShotMaskUi.PLUG_IN_NAME, q=True, l=True)

    def get_mask(self):
        """
        获取场景内所有遮罩节点的shape名
        :return:
        """
        if self.is_plugin_loaded():
            nodes = mc.ls(typ=DongShotMaskUi.NODE_TYPE)
            if len(nodes) > 0:
                return nodes[0]
        return None

    def create_mask(self):
        if not self.load_plugin():
            return

        if not self.get_mask():
            selection = mc.ls(sl=True)

            transform_node = mc.createNode('transform', n=DongShotMaskUi.TRANSFORM_NAME)
            mc.createNode(DongShotMaskUi.NODE_TYPE, n=DongShotMaskUi.SHAPE_NAME, p=transform_node)

            mc.select(selection, r=True)
        self.update_mask()

    def delete_mask(self):
        mask = self.get_mask()
        if mask:
            transform = mc.listRelatives(mask, f=True, p=True)
            if transform:
                mc.delete(transform)
            else:
                mc.delete(mask)

    def update_mask(self):
        mc.optionVar(sv=[DongShotMaskUi.OPT_VAR_CAMERA, self.camera_le.text()])  #生成一个自定义全局变量名，值为输入框内容

        mc.optionVar(sv=[DongShotMaskUi.OPT_VAR_TEXT, self.text_line_edits[0].text()])
        for i in range(1, len(self.text_line_edits)):
            mc.optionVar(sva=[DongShotMaskUi.OPT_VAR_TEXT, self.text_line_edits[i].text()])

        mc.optionVar(sv=[DongShotMaskUi.OPT_VAR_FONT, self.font_le.text()])

        font_color = self.font_color_btn.get_color()
        font_alpha = self.font_alpha_dsb.value()
        mc.optionVar(fv=[DongShotMaskUi.OPT_VAR_FONT_COLOR, font_color[0]])
        mc.optionVar(fva=[DongShotMaskUi.OPT_VAR_FONT_COLOR, font_color[1]])
        mc.optionVar(fva=[DongShotMaskUi.OPT_VAR_FONT_COLOR, font_color[2]])
        mc.optionVar(fva=[DongShotMaskUi.OPT_VAR_FONT_COLOR, font_alpha])

        mc.optionVar(fv=[DongShotMaskUi.OPT_VAR_FONT_SCALE, self.font_scale_dsb.value()])

        mc.optionVar(iv=[DongShotMaskUi.OPT_VAR_BORDER_VISIBLE, self.top_border_cb.isChecked()])
        mc.optionVar(iva=[DongShotMaskUi.OPT_VAR_BORDER_VISIBLE, self.bottom_border_cb.isChecked()])

        border_color = self.border_color_btn.get_color()
        border_alpha = self.border_transparency_dsb.value()
        mc.optionVar(fv=[DongShotMaskUi.OPT_VAR_BORDER_COLOR, border_color[0]])
        mc.optionVar(fva=[DongShotMaskUi.OPT_VAR_BORDER_COLOR, border_color[1]])
        mc.optionVar(fva=[DongShotMaskUi.OPT_VAR_BORDER_COLOR, border_color[2]])
        mc.optionVar(fva=[DongShotMaskUi.OPT_VAR_BORDER_COLOR, border_alpha])

        mc.optionVar(fv=[DongShotMaskUi.OPT_VAR_BORDER_SCALE, self.border_scale_dsb.value()])

        mc.optionVar(iv=[DongShotMaskUi.OPT_VAR_COUNTER_PADDING, self.counter_padding_sb.value()])

        self.refresh_mask()

    def refresh_mask(self):
        mask = self.get_mask()
        if not mask:
            return
        mc.setAttr('{}.camera'.format(mask), self.get_camera_name(), typ='string')
        text_lis = self.get_text_list()
        for i, attr in enumerate(DongShotMaskUi.TEXT_ATTRIBUTES):
            mc.setAttr('{}.{}'.format(mask, attr), text_lis[i], typ='string')
        mc.setAttr("{0}.fontName".format(mask), self.get_font(), type="string")

        font_color = self.get_font_color()
        mc.setAttr("{0}.fontColor".format(mask), font_color[0], font_color[1], font_color[2], type="double3")
        mc.setAttr("{0}.fontAlpha".format(mask), font_color[3])
        mc.setAttr("{0}.fontScale".format(mask), self.get_font_scale())

        border_vis = self.get_border_visibility()
        mc.setAttr("{0}.topBorder".format(mask), border_vis[0])
        mc.setAttr("{0}.bottomBorder".format(mask), border_vis[1])

        border_color = self.get_border_color()
        mc.setAttr("{0}.borderColor".format(mask), border_color[0], border_color[1], border_color[2], type="double3")
        mc.setAttr("{0}.borderAlpha".format(mask), border_color[3])
        mc.setAttr("{0}.borderScale".format(mask), self.get_border_scale())

        mc.setAttr("{0}.counterPadding".format(mask), self.get_counter_padding())

    def refresh_ui(self):
        self.camera_le.setText(self.get_camera_name())
        text_list = self.get_text_list()
        for i in range(len(self.text_line_edits)):
            self.text_line_edits[i].setText(text_list[i])

        self.font_le.setText(self.get_font())
        font_color = self.get_font_color()
        self.font_color_btn.set_color(font_color)
        self.font_alpha_dsb.setValue(font_color[3])
        self.font_scale_dsb.setValue(self.get_font_scale())

        border_visibility = self.get_border_visibility()
        self.top_border_cb.setChecked(border_visibility[0])
        self.bottom_border_cb.setChecked(border_visibility[1])

        border_color = self.get_border_color()
        self.border_color_btn.set_color(border_color)
        self.border_transparency_dsb.setValue(border_color[3])
        self.border_scale_dsb.setValue(self.get_border_scale())

        self.counter_padding_sb.setValue(self.get_counter_padding())

    def get_camera_name(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_CAMERA):  #检查自定义全局变量名是否存在
            return mc.optionVar(q=DongShotMaskUi.OPT_VAR_CAMERA)  #返回自定义变量的值

        return 'all'

    def get_font(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_FONT):
            font = mc.optionVar(q=DongShotMaskUi.OPT_VAR_FONT)
            if font:
                return font
        return "Times New Roman"

    def get_font_color(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_FONT_COLOR):
            return mc.optionVar(q=DongShotMaskUi.OPT_VAR_FONT_COLOR)
        return [1.0, 1.0, 1.0, 1.0]

    def get_font_scale(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_FONT_SCALE):
            font_scale = mc.optionVar(q=DongShotMaskUi.OPT_VAR_FONT_SCALE)
            if font_scale:
                return font_scale
        return 1.0

    def get_border_visibility(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_BORDER_VISIBLE):
            border_visibility = mc.optionVar(q=DongShotMaskUi.OPT_VAR_BORDER_VISIBLE)
            try:
                if len(border_visibility) == 2:
                    return border_visibility
            except:
                pass
        return [1, 1]

    def get_border_color(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_BORDER_COLOR):
            return mc.optionVar(q=DongShotMaskUi.OPT_VAR_BORDER_COLOR)

        return [0.0, 0.0, 0.0, 1.0]

    def get_border_scale(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_BORDER_SCALE):
            border_scale = mc.optionVar(q=DongShotMaskUi.OPT_VAR_BORDER_SCALE)
            if border_scale:
                return border_scale

        return 1.0

    def get_counter_padding(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_COUNTER_PADDING):
            counter_padding = mc.optionVar(q=DongShotMaskUi.OPT_VAR_COUNTER_PADDING)
            if counter_padding >= 1 and counter_padding <= 6:
                return counter_padding

        return 4

    def set_camera_name(self, *args):
        cam = self.camera_le.text()
        self.camera_le.setText('all' if args[0] == 0 else self.camera_comb.itemText(args[0]))
        if self.camera_le.text() != cam:
            self.update_mask()

    def get_text_list(self):
        if mc.optionVar(ex=DongShotMaskUi.OPT_VAR_TEXT):
            return mc.optionVar(q=DongShotMaskUi.OPT_VAR_TEXT)
        return ['', '{scene}', '', '{camera}', '', '{counter}']

    def on_camera_select_accepted(self):
        selected = self._camera_select_dialog.get_selected()
        if selected:
            self.camera_le.setText(selected[0])

            self.update_mask()

    def show_font_select_dialog(self):
        current_font = QtGui.QFont(self.font_le.text())

        font = QtWidgets.QFontDialog.getFont(current_font, self)
        if type(font[0]) == bool:
            ok = font[0]
            family = font[1].family()
        else:
            family = font[0].family()
            ok = font[1]

        if ok:
            self.font_le.setText(family)

            self.update_mask()


if __name__ == "__main__":

    try:
        dong_mask_ui.close()  # pylint: disable=E0601
        dong_mask_ui.deleteLater()
    except:
        pass

    dong_mask_ui = DongShotMaskUi()
    dong_mask_ui.show()