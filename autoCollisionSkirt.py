# -*- coding:GBK -*-
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om
import maya.OpenMayaUI as omui


def maya_main_window():
    return wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)


class AutoCollisionSkirtWindow(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(AutoCollisionSkirtWindow, self).__init__(parent)

        self.setWindowTitle(u'裙子绑定工具')
        if mc.about(ntOS=True):  #判断系统类型
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)  #删除窗口上的帮助按钮
        elif mc.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.lin_name = QtWidgets.QLineEdit()
        self.lin_name.setText('skirt')
        self.spin_jntNum = QtWidgets.QSpinBox()
        self.spin_jntNum.setValue(12)
        self.spin_jntNum.setMinimum(4)
        self.but_appJnt = QtWidgets.QPushButton(u'加载碰撞关节->>')
        self.lin_jnts = QtWidgets.QLineEdit()
        self.but_cratCrv = QtWidgets.QPushButton(u'生成定位曲线')
        self.but_run = QtWidgets.QPushButton(u'运行')

    def create_layout(self):
        layout_row = QtWidgets.QFormLayout()
        layout_row.addRow(u'名称:', self.lin_name)
        layout_row.addRow(u'被碰撞关节数量:', self.spin_jntNum)

        layout_collisionJnt = QtWidgets.QHBoxLayout()
        layout_collisionJnt.addWidget(self.but_appJnt)
        layout_collisionJnt.addWidget(self.lin_jnts)

        layout_main = QtWidgets.QVBoxLayout(self)
        layout_main.addLayout(layout_row)
        layout_main.addLayout(layout_collisionJnt)
        layout_main.addWidget(self.but_cratCrv)
        layout_main.addWidget(self.but_run)
        layout_main.setContentsMargins(3, 3, 3, 3)
        layout_main.setSpacing(2)

    def create_connections(self):
        self.but_appJnt.clicked.connect(self.get_collision_joints)
        self.but_cratCrv.clicked.connect(self.create_curve)
        self.but_run.clicked.connect(self.create_collision_system)

    def get_collision_joints(self):
        """
        获取用于驱动的关节
        :return:
        """
        sel_lis = mc.ls(sl=True)
        if sel_lis and mc.objectType(sel_lis[0]) == 'joint' and mc.listRelatives(sel_lis[0]):
            self.lin_jnts.setText(sel_lis[0])
        else:
            om.MGlobal.displayError('选择的碰撞关节对象不合适。应该选中一个关节，且该关节有一个子级对象。')

    def create_curve(self):
        """
        生成用于定义裙子上下的曲线，曲线的ep点即生成的蒙皮关节数量与位置
        :return:
        """
        if not self.lin_name.text():
            mc.error('没有指定碰撞系统名称。')
        if not self.lin_jnts.text() and not mc.objExists(self.lin_jnts.text()):
            mc.error('没有指定碰撞关节或者指定的对象无效。')
        self.colJnt_rot = self.lin_jnts.text()
        self.colJnt_end = mc.listRelatives(self.colJnt_rot)[0]
        self.col_name = self.lin_name.text()
        jnt_num = self.spin_jntNum.value()

        jnt_rot_pos = mc.xform(self.colJnt_rot, q=True, t=True, ws=True)
        jnt_end_pos = mc.xform(self.colJnt_end, q=True, t=True, ws=True)
        normal_aix = mc.xform(self.colJnt_end, q=True, t=True, os=True)#当驱动关节的子级不在正上方或正下方时用于定位曲线的朝向

        self.crv_up = mc.circle(c=jnt_rot_pos, r=1, s=jnt_num, nr=normal_aix)[0]
        self.crv_down = mc.circle(c=jnt_end_pos, r=2, s=jnt_num, nr=normal_aix)[0]

    def create_collision_system(self):
        #生成一个总的组
        self.root_grp = mc.group(n='grp_collision_001', em=True, w=True)
        #生成裙子上的蒙皮关节
        skinJnt_lis, ctrlGrp_lis = self.create_joints()
        #生成曲线上的定位器与蒙皮关节处的定位器等
        loc_hand, loc_crv, loc_aim, dis_lis = self.create_locInfo(skinJnt_lis)
        #生成用于计算角度的相关关节与ik、目标约束等
        jnt_rot = self.create_aimInfo(loc_hand, loc_crv, loc_aim)
        #生成计算触发相关的节点
        self.create_nodeInfo(loc_aim, jnt_rot, dis_lis, skinJnt_lis, ctrlGrp_lis)

    def create_joints(self):
        """
        根据上下两条曲线上对应的ep点位置生成关节，并生成控制器与对应父级组，将控制器父级某轴指向驱动关节
        :return:蒙皮关节名列表，控制器父级的偏移父级组
        """
        jnt_lis = []
        conn_lis = []
        grp_jnt = mc.group(n='grp_{}_skinJnt_001'.format(self.col_name), w=True, em=True)
        grp_ctrl = mc.group(n='grp_{}_ctl_001'.format(self.col_name), w=True, em=True)
        for i in range(mc.ls('{}.ep[*]'.format(self.crv_up), fl=True).__len__()):
            jnt_up = mc.createNode('joint', n='jnt_{}_{:03d}'.format(self.col_name, i + 1))
            jnt_down = mc.createNode('joint', n='{}_end_{:03d}'.format(jnt_up.rsplit('_', 1)[0], i + 1))
            ctrl = mc.circle(n='ctl_{}_{:03d}'.format(self.col_name, i + 1), nr=[1, 0, 0], r=0.5)[0]
            mm.eval('DeleteHistory;')
            grp_offset = mc.group(n='offset_{}_{:03d}'.format(self.col_name, i + 1), w=True)
            grp = mc.group(n='grp_{}_{:03d}'.format(self.col_name, i + 1), w=True)
            mc.parentConstraint(ctrl, jnt_up, mo=False)

            up_ep_pos = mc.xform('{}.ep[{}]'.format(self.crv_up, i), q=True, ws=True, t=True)
            down_ep_pos = mc.xform('{}.ep[{}]'.format(self.crv_down, i), q=True, ws=True, t=True)
            mc.xform(grp, t=up_ep_pos, ws=True)
            mc.xform(jnt_down, t=down_ep_pos, ws=True)

            link = mc.aimConstraint(jnt_down, grp, o=(0, 0, 0), aim=(1, 0, 0), u=(0, 1, 0), wut='object',
                                    mo=False, wuo=self.colJnt_rot)
            mc.xform(jnt_down, ro=mc.xform(grp, q=True, ro=True, ws=True), ws=True)

            mc.delete(link)
            mc.makeIdentity(jnt_down, a=True, r=True, n=False, pn=True)
            mc.parent(jnt_down, jnt_up)
            mc.parent(jnt_up, grp_jnt)
            mc.parent(grp, grp_ctrl)

            jnt_lis.append(jnt_up)
            conn_lis.append(grp_offset)
        mc.parent(grp_jnt, grp_ctrl, self.root_grp)
        return jnt_lis, conn_lis

    def create_locInfo(self, skin_jnts):
        """
        在蒙皮关节处放置定位器
        在驱动关节子级处放置用于定位旋转ik方向的定位器和驱动ik手柄的定位器
        :param skin_jnts:蒙皮关节名列表
        :return:驱动ik手柄的定位器名，曲线上的用于测距的定位器名，定位ik基向量的定位器名，测距节点的shape名
        """
        grp_other = mc.group(n='grp_{}_other_001'.format(self.col_name), p=self.root_grp, em=True)
        grp_dis = mc.group(n='grp_{}_dis_001'.format(self.col_name), p=self.root_grp, em=True)

        loc_hand = mc.spaceLocator(n='loc_{}_hand'.format(self.col_name))[0]
        loc_crv = mc.spaceLocator(n='loc_{}_crv'.format(self.col_name))[0]
        loc_aim = mc.spaceLocator(n='loc_{}_aim'.format(self.col_name))[0]
        pntOnCvr = mc.createNode('nearestPointOnCurve', n='pntOnCrv_{}_001'.format(self.col_name))

        mc.connectAttr('{}.worldSpace[0]'.format(mc.listRelatives(self.crv_down, s=True)[0]),
                       '{}.inputCurve'.format(pntOnCvr))
        mc.connectAttr('{}.worldPosition[0]'.format(mc.listRelatives(loc_hand, s=True)[0]),
                       '{}.inPosition'.format(pntOnCvr))
        mc.connectAttr('{}.position'.format(pntOnCvr), '{}.translate'.format(loc_crv))

        mc.xform(loc_hand, t=mc.xform(self.colJnt_end, ws=True, t=True, q=True), ws=True)
        mc.parent(loc_hand, loc_crv, loc_aim, grp_other)
        mc.parentConstraint(self.colJnt_end, loc_hand, mo=False)
        mc.xform(loc_aim, t=mc.xform(self.colJnt_end, ws=True, t=True, q=True), ws=True)
        if mc.listRelatives(self.colJnt_rot, p=True):
            mc.parentConstraint(mc.listRelatives(self.colJnt_rot, p=True)[0], loc_aim, mo=False)

        dis_lis = []
        for jnt in skin_jnts:
            loc = mc.spaceLocator(n='{}'.format(jnt.replace('jnt', 'loc')))[0]
            dis = mc.createNode('distanceDimShape', n='{}Shape'.format(jnt.replace('jnt', 'dis')))
            dis_lis.append(dis)

            mc.xform(loc, ws=True, t=mc.xform(jnt, ws=True, t=True, q=True))
            mc.parent(loc, mc.listRelatives(dis, p=True)[0], grp_dis)
            mc.connectAttr('{}.worldPosition[0]'.format(loc), '{}.startPoint'.format(dis))
            mc.connectAttr('{}.worldPosition[0]'.format(loc_crv), '{}.endPoint'.format(dis))

        return loc_hand, loc_crv, loc_aim, dis_lis

    def create_aimInfo(self, loc_hand, loc_crv, loc_aim):
        """
        通过驱动关节驱动hand定位器输出曲线上离它最近位置，然后使用目标约束将关节对准曲线上定位器，计算目标约束关节与指向关节间的距离
        为负数时为未超过，即没有碰撞到，超过后为整数，可以用于出发对应蒙皮关节的旋转
        :param loc_hand: 驱动关节驱动的定位器
        :param loc_crv: 曲线上的定位器
        :param loc_aim: 驱动关节子级位置的定位器
        :return:目标约束的用于计算旋转角度的关节
        """
        mc.select(cl=True)
        jnt_aim = mc.joint(n='jnt_{}_aim_001'.format(self.col_name),
                           p=mc.xform(self.colJnt_rot, q=True, ws=True, t=True))#ik父关节
        jnt_aim_end = mc.joint(n='jnt_{}_aim_end_001'.format(self.col_name),
                               p=mc.xform(loc_crv, q=True, ws=True, t=True))#ik子关节，关节位置在曲线定位器处
        mc.select(cl=True)
        jnt_rot = mc.joint(n='jnt_{}_rot_001'.format(self.col_name),
                           p=mc.xform(self.colJnt_rot, q=True, ws=True, t=True))#旋转父关节
        mc.joint(n='jnt_{}_rot_end_001'.format(self.col_name), p=mc.xform(self.colJnt_end, q=True, ws=True, t=True))#旋转子关节
        mc.parent(jnt_rot, jnt_aim)
        mc.joint(jnt_aim, e=True, oj='xyz', sao='yup', ch=True, zso=True)#对ik父关节做关节定向，使z轴朝向子级

        #由于ik子关节为ik关节的第一个子物体，所以ik关节是指向子关节
        # 旋转关节与ik关节出现一个旋转值，由于使用的是关节定向，所以旋转值被放在jointOrient中，将其拿出来到变换中用于计算
        rot = mc.getAttr('{}.jointOrientZ'.format(jnt_rot))
        mc.setAttr('{}.jointOrientZ'.format(jnt_rot), 0)
        mc.setAttr('{}.rotateZ'.format(jnt_rot), rot)

        #驱动关节约束的定位器对旋转关节做目标约束，使用对象旋转指定向上方向，使旋转关节的轴向与ik关节的轴向一致，避免方向不一致导致旋转数值出现在多个轴
        mc.aimConstraint(loc_hand, jnt_rot, o=(0, 0, 0), aim=(1, 0, 0), u=(0, 0, 1), wut='objectrotation', wu=(0, 0, 1),
                         wuo=jnt_aim)
        #对ik关节做ikRPsolver,只能使用这个类型ik，因为ikSCsolver无法做基向量约束，而我们需要使旋转只出现在一个轴上
        aim_hadl = mc.ikHandle(sj=jnt_aim, ee=jnt_aim_end, sol='ikRPsolver')[0]
        mc.parent(aim_hadl, loc_crv)
        mc.setAttr('{}.v'.format(aim_hadl), 0)
        #将ik做基向量约束，这里可能会出现将y或者z轴当做极向量方向，后面有代码做判定
        mc.poleVectorConstraint(loc_aim, aim_hadl)

        grp_jnt = mc.group(n='grp_{}_jnt_001'.format(self.col_name), p=self.root_grp, em=True)
        mc.parent(jnt_aim, grp_jnt)
        mc.setAttr('{}.v'.format(grp_jnt), 0)

        return jnt_rot

    def create_nodeInfo(self, loc_aim, jnt_rot, dis_lis, jnt_lis, grp_lis):
        """
        制作出发逻辑和参数影响
        :param loc_aim: 驱动关节名
        :param jnt_rot:旋转关节名
        :param dis_lis:测距节点列表
        :param jnt_lis:蒙皮关节列表
        :param grp_lis:控制器父级的偏移组
        :return:
        """
        mc.addAttr(loc_aim, ln='offset', at='double', min=0, dv=0, k=True)#添加偏移属性，用于控制碰撞距离
        mc.addAttr(loc_aim, ln='range', at='double', min=0, max=1, dv=0.2, k=True)#添加范围属性，控制驱动范围距离
        rvs_range = mc.createNode('reverse', n='rvs_{}_range_001'.format(self.col_name))#用于将驱动范围属性的值反向，方便人的惯性思维
        add_offset = mc.createNode('addDoubleLinear', n='add_{}_offset_001'.format(self.col_name))#用于将碰撞距离与偏移属性相加，增加启动碰撞距离
        clp_offset = mc.createNode('clamp', n='clp_{}_offset_001'.format(self.col_name))#用于限制碰撞距离，即蒙皮关节旋转只能在0到180度之间
        mc.setAttr('{}.maxR'.format(clp_offset), 180)

        mc.connectAttr(loc_aim + '.offset', add_offset + '.input1')
        mc.connectAttr(add_offset + '.output', clp_offset + '.inputR')
        mc.connectAttr(loc_aim + '.range', rvs_range + '.inputX')

        mult = 1
        aix_dir = {1: 'X', 2: 'Y', 3: 'Z'}
        mult_ratio = mc.createNode('multiplyDivide', n='mult_{}_ratio_001'.format(self.col_name))#生成第一个用于计算最短距离与当前距离比例的节点
        mult_itplat = mc.createNode('multiplyDivide', n='mult_{}_itplat_001'.format(self.col_name))#生成触发旋转的乘除节点，只有当旋转关节输出旋转值为正值时才会有大于1的值输出
        mult_rot = mc.createNode('multiplyDivide', n='mult_{}_rotate_001'.format(self.col_name))#生成旋转反向节点，将旋转值反向才能使蒙皮关节向外旋转
        for dis, jnt, grp in zip(dis_lis, jnt_lis, grp_lis):
            suffix = dis.rsplit('_', 1)[1].replace('Shape', '')
            if mult == 4:#为节省节点，将乘除计算放在一个节点内，当槽使用完时生成新的节点用于计算
                mult = 1
                mult_ratio = mc.createNode('multiplyDivide', n='mult_{}_ratio_{}'.format(self.col_name, suffix))
                mult_itplat = mc.createNode('multiplyDivide', n='mult_{}_itplat_{}'.format(self.col_name, suffix))
                mult_rot = mc.createNode('multiplyDivide', n='mult_{}_rotate_{}'.format(self.col_name, suffix))

            #写入距离蒙皮关节最近的裙摆曲线上的位置距离，该点是距离对应旋转关节最近的点
            # 不能使用上下曲线上对应的ep点，否则当下摆曲线为椭圆时可能出现对应ep点不是距离旋转关节最近的点
            mc.setAttr('{}.input1{}'.format(mult_ratio, aix_dir[mult]), self.get_distance(jnt))
            mc.setAttr('{}.operation'.format(mult_ratio), 2)
            mc.connectAttr('{}.distance'.format(dis), '{}.input2{}'.format(mult_ratio, aix_dir[mult]))

            #生成映射节点，将范围属性连接到inputMin可以控制驱动旋转的力度
            rmap_nod = mc.createNode('remapValue', n='rmap_{}_range_{}'.format(self.col_name, suffix))
            mc.connectAttr('{}.output{}'.format(mult_ratio, aix_dir[mult]), '{}.inputValue'.format(rmap_nod))
            mc.connectAttr(rvs_range + '.outputX', '{}.inputMin'.format(rmap_nod))

            mc.connectAttr('{}.outValue'.format(rmap_nod), '{}.input1{}'.format(mult_itplat, aix_dir[mult]))
            mc.connectAttr('{}.outputR'.format(clp_offset), '{}.input2{}'.format(mult_itplat, aix_dir[mult]))

            if mc.getAttr(jnt_rot+'.rotateY'):#当为常规情况时，旋转关节的旋转值在y轴上
                if not mc.listConnections('jnt_skirt_rot_001.rotateY', s=0, scn=1):
                    mc.connectAttr(jnt_rot + '.rotateY', add_offset + '.input2')

                mc.connectAttr('{}.output{}'.format(mult_itplat, aix_dir[mult]),
                               '{}.input1{}'.format(mult_rot, aix_dir[mult]))
                mc.connectAttr('{}.output{}'.format(mult_rot, aix_dir[mult]), '{}.rotateZ'.format(grp))
                mc.setAttr('{}.input2{}'.format(mult_rot, aix_dir[mult]), -1)
            else:#当有时旋转值在z轴上时
                mc.delete(mult_rot)
                if not mc.listConnections('jnt_skirt_rot_001.rotateZ', s=0, scn=1):
                    mc.connectAttr(jnt_rot + '.rotateZ', add_offset + '.input2')
                mc.connectAttr('{}.output{}'.format(mult_itplat, aix_dir[mult]), '{}.rotateZ'.format(grp))

            mult += 1

    def get_distance(self, jnt):
        """
        通过distanceBetween节点获取蒙皮关节在下摆曲线上最近的点到蒙皮关节的最短距离
        :param jnt: 要计算的蒙皮关节
        :return: 最短距离的值
        """
        dis = mc.createNode('distanceBetween')
        npc = mc.createNode('nearestPointOnCurve')

        jnt_pos = mc.xform(jnt, q=True, ws=True, t=True)
        [mc.setAttr(npc + '.inPosition{}'.format(aix), v) for aix, v in zip(['X', 'Y', 'Z'], jnt_pos)]
        [mc.setAttr(dis + '.point1{}'.format(aix), v) for aix, v in zip(['X', 'Y', 'Z'], jnt_pos)]
        mc.connectAttr(mc.listRelatives(self.crv_down, s=True)[0]+'.worldSpace[0]', npc+'.inputCurve')
        [mc.setAttr(dis + '.point2{}'.format(aix), v) for aix, v in zip(['X', 'Y', 'Z'], mc.getAttr(npc+'.position')[0])]
        val = mc.getAttr(dis+'.distance')
        mc.delete(dis, npc)

        return val




if __name__ == '__main__':
    try:
        skirt_window.close()
        skirt_window.deleteLater()
    except:
        pass
    finally:
        skirt_window = AutoCollisionSkirtWindow()
        skirt_window.show()
