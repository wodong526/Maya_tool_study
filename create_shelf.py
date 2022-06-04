import maya.cmds as mc

class SelfButton(object):
    def __init__(self, name):
        self.shelf_name = name
#        self.iconPath = iconPath
        
        self.labelBackground = (213, 169, 169, 0)
        self.labelColor = (220, 135, 206)
        
        self.cleanOldShalf()
        self.build()
        
    def cleanOldShalf(self):
        if mc.shelfLayout(self.shelf_name, ex = 1):
            if mc.shelfLayout(self.shelf_name, q = 1, ca = 1):
                for each in mc.shelfLayout(self.shelf_name, q = 1, ca = 1):
                    mc.deleteUI(each)
        
        else:
            mc.shelfLayout(self.shelf_name, p = 'ShelfLayout')
    
    def build(self):
        self.addButton('按钮1', command = 'print "1",', icon = 'ss.jpg')
        self.addButton('按钮2', icon = 'ss.jpg')
        p = mc.popupMenu(b = 1)
        self.addMenuItem(p, '菜单1', icon = 'xiao.jpg')
        self.addMenuItem(p, '菜单2', icon = 'xiao.jpg')
        sub = self.addSubMenu(p, '子菜单1', icon = 'xiao.jpg')
        self.addMenuItem(sub, '子菜单1级', icon = 'xiao.jpg')
        sub2 = self.addSubMenu(sub, '子菜单2', icon = 'xiao.jpg')
        self.addMenuItem(sub2, '子菜单2级1', icon = 'xiao.jpg')
        self.addMenuItem(sub2, '子菜单2级2', icon = 'xiao.jpg')
        self.addMenuItem(sub, '子菜单3' , icon = 'xiao.jpg')
        self.addMenuItem(p, '菜单3', icon = 'xiao.jpg')
        self.addButton('按钮2', command = 'print "2",', icon = 'ss.jpg')
    
    def addButton(self, label, icon, command = '', doubleCommand = ''):
        """
        直接在shelf栏中生成按钮，并设置按钮的相关参数
        """
        mc.setParent(self.shelf_name)
        
        if icon:
#            icon = self.iconPath + icon
            mc.shelfButton(w = 37, h = 37, i = icon, l = label, c = command, dcc = doubleCommand, iol = label, olb = self.labelBackground, olc = self.labelColor)
    
    def addMenuItem(self, parent, label, icon, command = ''):
        """
        在按钮被点击时执行生成子菜单，并设置相关参数
        """
        if icon:
#            icon = self.iconPath + icon
            return mc.menuItem(p = parent, l = label, c = command, i = icon)
    
    def addSubMenu(self, parent, label, icon):
        """
        为menuItem添加子菜单，只需要设置其父级即可
        """
        if icon:
#            icon = self.iconPath + icon
            return mc.menuItem(p = parent, l = label, i = icon , sm = 1)

SelfButton('new_shelf')
