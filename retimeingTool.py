#coding=gbk
import maya.cmds as mc
import maya.mel as mm

from functools import partial

class RetimingUtils(object):
    @classmethod
    def set_current_time(cls, time):
        """
        将时间滑块设置到某一帧上
        :param time: 要设置的帧的值
        :return:
        """
        mc.currentTime(time)

    @classmethod
    def get_select_range(cls):
        """
        返回在时间轴上拖选的帧范围
        :return:(起始帧, 结束帧)
        """
        playback_slider = mm.eval('$tempVar = $gPlayBackSlider')
        selected_range = mc.timeControl(playback_slider, q=True, rangeArray=True)

        return selected_range

    @classmethod
    def find_keyframe(cls, which, time=None):
        """
        获取选中对象的上、下、最前、最后的帧的值
        :param which:返回当前选中对象的k帧中，以时间滑块为准的什么位置的帧的值
        next：当前时间滑块的下一个k帧的值 |previous：上一个帧 |first：最前面的帧 |last：最后面的帧
        :param time:当使用上一帧或下一针时，可以指定一个时间，返回将为该时间的上一帧或下一帧。如果没有限定，返回时间滑块的上下一帧
        :return:选中对象的对应帧的值
        """
        kwargs = {'which': which}
        if which in ['next', 'previous']:
            kwargs['time'] = (time, time)

        return mc.findKeyframe(**kwargs)

    @classmethod
    def change_keyframe_time(cls, current_time, new_time):
        """
        移动某帧到另一个位置
        :param current_time:被移动的帧
        :param new_time: 移动到的帧
        :return:
        """
        mc.keyframe(e=True, t=(current_time, current_time), tc=new_time)

    @classmethod
    def get_start_keyframe_time(cls, range_start_time):
        """
        获取某拖动范围内的起始帧，当范围内没有帧时，获取范围在整个时间轴上的上一帧
        :param range_start_time: 指定的拖动范围
        :return: 上一帧的值
        """
        start_times = mc.keyframe(q=True, t=(range_start_time, range_start_time))
        if start_times:
            return start_times[0]
        else:
            return cls.find_keyframe('previous', range_start_time)

    @classmethod
    def get_last_keyframe_time(cls):
        """
        获取结尾帧的值
        :return:
        """
        return cls.find_keyframe('last')

    @classmethod
    def retime_keys(cls, retime_vlue, incremental, move_to_next):
        range_start_time, range_end_time = cls.get_select_range()#获取拖选范围
        start_keyframe_time = cls.get_start_keyframe_time(range_start_time)#获取第一帧
        last_keyframe_time = cls.get_last_keyframe_time()#获取最后一帧
        current_time = start_keyframe_time

        new_keyframe_times = [start_keyframe_time]
        current_keyfrmae_values = [start_keyframe_time]#直接=列表是浅拷贝，这样分开用列表写可以得到两块内存
        while current_time != last_keyframe_time:
            next_keyframe_time = cls.find_keyframe('next', current_time)#获取当前帧的下一帧
            time_diff = 0
            if incremental:#当增加的距离要加上已有距离时
                time_diff = next_keyframe_time - current_time#下一帧与当前帧的差
                if current_time < range_end_time:#当当前帧小于给定范围结尾帧
                    time_diff += retime_vlue#在差值上递增要移动的距离
                    if time_diff < 1:#当移动距离小于1，则不移动或想后移动时
                        time_diff = 1
            else:
                if current_time < range_end_time:  #当当前帧小于给定范围结尾帧
                    time_diff = retime_vlue  #在差值上递增要移动的距离
                else:
                    time_diff = next_keyframe_time - current_time

            new_keyframe_times.append(new_keyframe_times[-1] + time_diff)#从第一帧开始向后增加差值的帧
            current_time = next_keyframe_time#将当前帧设置为已处理的帧，为下一帧计算做准备
            current_keyfrmae_values.append(current_time)#将被处理的帧放入处理后的帧列表

        if len(new_keyframe_times) > 1:
            cls.retime_keys_recursive(start_keyframe_time, 0, new_keyframe_times)

        first_keyframe_time = cls.find_keyframe('first')
        if move_to_next and range_start_time >= first_keyframe_time:
            next_keyframe_time = cls.find_keyframe('next', start_keyframe_time)
            cls.set_current_time(next_keyframe_time)
        elif range_end_time > first_keyframe_time:
            cls.set_current_time(start_keyframe_time)
        else:
            cls.set_current_time(range_start_time)

    @classmethod
    def retime_keys_recursive(cls, current_time, index, new_keyframe_times):
        if index >= len(new_keyframe_times):
            return

        updated_keyframe_time = new_keyframe_times[index]
        next_keyframe_time = cls.find_keyframe('next', current_time)
        if  updated_keyframe_time < next_keyframe_time:
            cls.change_keyframe_time(current_time, updated_keyframe_time)
            cls.retime_keys_recursive(next_keyframe_time, index+1, new_keyframe_times)
        else:
            cls.retime_keys_recursive(next_keyframe_time, index+1, new_keyframe_times)
            cls.change_keyframe_time(current_time, updated_keyframe_time)

class RetimeingUi(object):
    WINDOW_NAME = '東'
    WINDOW_TITLE = '帧移动工具'

    @classmethod
    def display(cls, development=False):
        if mc.window(cls.WINDOW_NAME, exists=True):
            mc.deleteUI(cls.WINDOW_NAME, wnd=True)

        if development and mc.windowPref(cls.WINDOW_NAME, ex=True):
            mc.windowPref(cls.WINDOW_NAME, r=True)

        main_window = mc.window(cls.WINDOW_NAME, t=cls.WINDOW_TITLE, s=False, mnb=False, mxb=False)
        main_layout = mc.formLayout(p=main_window)
        absolute_retiming_layout = mc.rowLayout(p=main_layout, nc=6)
        mc.formLayout(main_layout, e=True, af=(absolute_retiming_layout, 'top', 2))
        mc.formLayout(main_layout, e=True, af=(absolute_retiming_layout, 'left', 2))
        mc.formLayout(main_layout, e=True, af=(absolute_retiming_layout, 'right', 2))
        for i in range(1, 7):
            label = '{}'.format(i)
            cmd = partial(cls.retime, i, False)
            mc.button(p=absolute_retiming_layout, l=label, width=70, c=cmd)

        shift_left_layout = mc.rowLayout(p=main_layout, nc=2)
        mc.formLayout(main_layout, e=True, ac=(shift_left_layout, 'top', 2, absolute_retiming_layout))
        mc.formLayout(main_layout, e=True, af=(shift_left_layout, 'left', 2))
        mc.button(p=shift_left_layout, l='-2f', w=70, c=partial(cls.retime, -2, True))
        mc.button(p=shift_left_layout, l='-1f', w=70, c=partial(cls.retime, -1, True))

        shift_right_layout = mc.rowLayout(p=main_layout, nc=2)
        mc.formLayout(main_layout, e=True, ac=(shift_right_layout, 'top', 2, absolute_retiming_layout))
        mc.formLayout(main_layout, e=True, ac=(shift_right_layout, 'left', 28, shift_left_layout))
        mc.button(p=shift_right_layout, l='+1f', w=70, c=partial(cls.retime, 1, True))
        mc.button(p=shift_right_layout, l='+2f', w=70, c=partial(cls.retime, 2, True))

        move_to_next_cb = mc.checkBox(p=main_layout, l='move to next frame', v=False)
        mc.formLayout(main_layout, e=True, ac=(move_to_next_cb, 'top', 4, shift_left_layout))
        mc.formLayout(main_layout, e=True, af=(move_to_next_cb, 'left', 2))

        mc.showWindow()

    @classmethod
    def retime(cls, value, incremental, *args):
        move_to_next = False

        mc.undoInfo(ock=True)
        RetimingUtils.retime_keys(value, incremental, move_to_next)
        mc.undoInfo(cck=True)


if __name__ == "__main__":
    RetimeingUi.display()
