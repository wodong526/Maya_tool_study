import unreal as un

import os
import sys
import json

from PyQt5 import QtWidgets


def tool_function_called_in_a_button(asset_obj, file_nam):
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    file_path = un.SystemLibrary.get_system_path(asset_obj)
    if os.path.exists(file_path):
        path = os.path.dirname(file_path)  #获取当前文件所在路径
    else:
        path = ''

    window = QtWidgets.QWidget()  # 没有应用程序行崩溃
    file_path = QtWidgets.QFileDialog.getSaveFileName(window, '选择要导出控制器信息的json文件地址：',
                                                      '{}/{}'.format(path, file_nam), '(*.json)')
    window.show()

    return file_path


def exportCtrlsAnimToMaya():
    sel_asset = un.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()

    if type(sel_asset) == un.LevelSequence:
        keys_range = sel_asset.get_playback_range()
    else:
        un.log_error('打开的文件类型不对。\n应为{},实际为{}。'.format(un.LevelSequence, type(sel_asset)))
        return None

    world = un.get_editor_subsystem(un.UnrealEditorSubsystem).get_editor_world()
    sequencer_obj_lis_temp = un.SequencerTools.get_bound_objects(world, sel_asset, sel_asset.get_bindings(), keys_range)

    sequencer_obj_lis = []  #对象列表
    for obj in sequencer_obj_lis_temp:
        bound_obj = obj.bound_objects
        if len(bound_obj) > 0:
            if type(bound_obj[0]) == un.SkeletalMeshActor:
                sequencer_obj_lis.append(bound_obj[0])

    editor_asset_nam = un.EditorAssetLibrary.get_path_name_for_loaded_asset(sel_asset).split('.')[-1]

    skeletalMeshActor = sequencer_obj_lis[0]
    bp_possessable = sel_asset.add_possessable(skeletalMeshActor)
    child_possessable_list = bp_possessable.get_child_possessables()

    face_possessable = ''
    for current_child in child_possessable_list:
        if 'Face' in current_child.get_name():
            face_possessable = current_child

    if face_possessable:
        faceCtrls_anim = {}
        ctrls_nam_lis = []

        face_ctrl_track = face_possessable.get_tracks()[0]
        face_ctrl_channel_lis = face_ctrl_track.get_sections()[0].get_all_channels()

        for channel in face_ctrl_channel_lis:
            channel_nam = channel.get_name()
            ctrls_nam_lis.append(channel_nam.rsplit('_', 1)[0])

        for i in range(len(face_ctrl_channel_lis)):
            keys_total = face_ctrl_channel_lis[i].get_num_keys()
            keys_vals = face_ctrl_channel_lis[i].get_keys()

            key_lis = []
            for key in range(keys_total):
                key_val = keys_vals[key].get_value()
                key_time = keys_vals[key].get_time(time_unit=un.SequenceTimeUnit.DISPLAY_RATE).frame_number.value
                key_lis.append((key_time, key_val))
            faceCtrls_anim[ctrls_nam_lis[i]] = key_lis

        if faceCtrls_anim:
            faceCtrls_anim['dictType'] = 'metaHuman_FaceCtrlsAnim'

            file_path = tool_function_called_in_a_button(sel_asset, editor_asset_nam)
            if file_path[0]:
                un.log('要导出的文件对象为{}。'.format(editor_asset_nam))
                with open(file_path[0], 'w') as f:
                    json.dump(faceCtrls_anim, f, indent=4)
                un.log(
                    '已导出控制器动画文件到：{}\n'
                    '           动画时长：{}帧\n'
                    '           帧速率：30帧每秒\n'
                    '           控制器数量：{}个\n'
                    '           字典类型：metaHuman_FaceCtrlsAnim'.format(file_path[0], key, i))
            else:
                un.log_error('没有选择有效导出文件。')
        else:
            un.log_error('没有获取有效帧范围。')
    else:
        un.log_error('该文件中没有Face对象。')


exportCtrlsAnimToMaya()
