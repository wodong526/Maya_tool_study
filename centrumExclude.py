# *******************************************
# 作者: 我東
# mail:wodong526@dingtalk.com
# time:2022/4/12
# ******************************************

import maya.api.OpenMaya as oma
import maya.cmds as mc

obj_camera = 'persp' #相机名

class Count(object):
    def __init__(self, a, b, c, d):
        self.normal = oma.MVector(a, b, c)
        self.distance = d
    
    def get_gap(self, point_pos):
        return point_pos * self.normal + self.distance > 0

class getObj(object):
    def __init__(self):
        self.get_cameraMatrix(self.get_camera())
    def get_camera(self):
        if mc.nodeType(mc.listRelatives(obj_camera, shapes = True)) == 'camera':
            return self.get_dagPath(obj_camera)
        else:
            oma.MGlobal.displayError('未输入有效相机名。')
            return False
    
    def get_cameraMatrix(self, cam_dagPath):
        cam_mFnCamera = oma.MFnCamera(cam_dagPath)
        print type(cam_dagPath)
        
        cam_world_matx = oma.MFloatMatrix(cam_dagPath.inclusiveMatrixInverse())
        cam_proj_matx  = cam_mFnCamera.projectionMatrix()
        cam_postProj_matx = cam_mFnCamera.postProjectionMatrix()
        
        cam_view_projection = cam_world_matx * cam_proj_matx * cam_postProj_matx
        
        #右侧
        pjct_right = Count(cam_view_projection[3]  - cam_view_projection[0],
                           cam_view_projection[7]  - cam_view_projection[4],
                           cam_view_projection[11] - cam_view_projection[8],
                           cam_view_projection[15] - cam_view_projection[12],)

        # 左侧
        pjct_left = Count(cam_view_projection[3]  + cam_view_projection[0],
                          cam_view_projection[7]  + cam_view_projection[4],
                          cam_view_projection[11] + cam_view_projection[8],
                          cam_view_projection[15] + cam_view_projection[12],)

        # 下侧
        pjct_bottom = Count(cam_view_projection[3]  + cam_view_projection[1],
                            cam_view_projection[7]  + cam_view_projection[5],
                            cam_view_projection[11] + cam_view_projection[9],
                            cam_view_projection[15] + cam_view_projection[13],)

        # 上侧
        pjct_top = Count(cam_view_projection[3]  - cam_view_projection[1],
                         cam_view_projection[7]  - cam_view_projection[5],
                         cam_view_projection[11] - cam_view_projection[9],
                         cam_view_projection[15] - cam_view_projection[13],)

        # 后侧
        pjct_far = Count(cam_view_projection[3]  + cam_view_projection[2],
                         cam_view_projection[7]  + cam_view_projection[6],
                         cam_view_projection[11] + cam_view_projection[10],
                         cam_view_projection[15] + cam_view_projection[14],)

        # 前侧
        pjct_near = Count(cam_view_projection[3]  - cam_view_projection[2],
                          cam_view_projection[7]  - cam_view_projection[6],
                          cam_view_projection[11] - cam_view_projection[10],
                          cam_view_projection[15] - cam_view_projection[14],)
        self.planes = [pjct_right, pjct_left, pjct_bottom, pjct_top, pjct_far, pjct_near]
        self.count_mesh()
    
    def count_mesh(self):
        mc.select(cl = True)
        inside_obj = []
        for inf in mc.ls(typ = 'mesh'):
            obj_dagPath = self.get_dagPath(mc.listRelatives(inf, p = True)[0])
            obj_dagNode = oma.MFnDagNode(obj_dagPath)
            bbox = obj_dagNode.boundingBox
            bbox_itm = [bbox.min, bbox.max]
            
            inside_obj.append(inf)
            for obj_plane in self.planes:
                print obj_plane
                index_x = int(obj_plane.normal.x > 0)
                index_y = int(obj_plane.normal.y > 0)
                index_z = int(obj_plane.normal.z > 0)
                point_pos = oma.MVector(bbox_itm[index_x].x, bbox_itm[index_y].y, bbox_itm[index_z].z)
                
                if obj_plane.get_gap(point_pos) == False:
                    inside_obj.remove(inf)
                    break
                elif obj_plane.get_gap(point_pos) == True:
                    pass
        
        print '相机视野内物体有：{}'.format(inside_obj),
        for insd_obj in inside_obj:
            mc.select(insd_obj, add = 1)
    
    def get_dagPath(self, trs_obj):
        lis_obj = oma.MSelectionList()
        lis_obj.add(trs_obj)
        return lis_obj.getDagPath(0)
        

a = getObj()
a