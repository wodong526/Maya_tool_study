#coding=gbk
import traceback
import json
import time
import sys
from PyQt5 import QtCore, QtWidgets, QtNetwork


class ServerBase(QtCore.QObject):
    """
    服务器基类
    """
    PORT = 20201  #端口
    HEADER_SIZE = 10

    def __init__(self, parent):
        super(ServerBase, self).__init__(parent)

        self.port = self.__class__.PORT
        self.initialize()

    def initialize(self):
        """
        创建服务器实例
        :return:
        """
        self.server = QtNetwork.QTcpServer(self)
        self.server.newConnection.connect(self.establish_connection)  #新的客户端连接到服务器时触发

        if self.listen():
            print('[log] 端口：{}创建成功'.format(self.port))
        else:
            print('[error] 链接失败')

    def listen(self):
        """
        检查服务器是否在监听，如果没有则开始监听
        :return: True:已启动监听
                 False:启动监听失败
        """
        if not self.server.isListening():  #服务器当前是否正在侦听传入连接
            #启动TCP服务器，并使其开始监听指定的IP地址和端口
            return self.server.listen(QtNetwork.QHostAddress.LocalHost, self.port)  #地址，端口。true成功回报；否则返回false.

        return True

    def establish_connection(self):
        """
        当有链接请求时建立连接套接字的链接
        :return:
        """
        self.socket = self.server.nextPendingConnection()  #返回下一个挂起的连接QTcpSocket对象
        if self.socket.state() == QtNetwork.QTcpSocket.ConnectedState:  #当套接字状态为已连接状态时
            self.socket.disconnected.connect(self.on_disconnect)  #当套接字与客户端断开链接时触发
            self.socket.readyRead.connect(self.read)  #当套接字接收到新的数据时，就会触发这个信号
            print('[log] 链接成功')

    def on_disconnect(self):
        self.socket.disconnected.disconnect()  #断开信号槽的连接
        self.socket.readyRead.disconnect()

        self.socket.deleteLater()  #删除套接字
        print('[log] 断开链接')

    def read(self):
        """
        读取从客户端发送过来的数据，需要在子类中实现。
        :return:
        """
        bytes_remaining = -1
        json_data = ''

        while self.socket.bytesAvailable():  #获取当前套接字缓冲区中可供读取的字节数
            if bytes_remaining <= 0:  #头部
                bytes_array = self.socket.read(ServerBase.HEADER_SIZE)  #从套接字中读取指定数量的字节数据
                if not isinstance(bytes_array, QtCore.QByteArray):  #在pyqt中返回bytes；在pyside中返回QByteArray
                    #只有QByteArray中才有toInt方法，否则可以用int.from_bytes(bytes_array, byteorder='big')将bytes转为int
                    bytes_array = QtCore.QByteArray(bytes_array)

                bytes_remaining, valid = bytes_array.toInt()  #将内容转为十进制的整数。返回：转换后的值；转换是否成功
                if not valid:  #转换成功说明套接字是预期内的信息，开始读身体部分，失败说明不是需要的信息，则进入判定
                    bytes_remaining = -1
                    self.write_error('无效标头')
                    self.socket.readAll()  #读取套接字缓冲区中的所有可用数据
                    return

            if bytes_remaining > 0:  #身体
                bytes_array = self.socket.read(bytes_remaining)  #这里的字节是发送端发送自己数，由上方标头计算得出
                if not isinstance(bytes_array, QtCore.QByteArray):  #在pyqt中返回bytes；在pyside中返回QByteArray
                    #可以用str来将bytes_array转为可以被len的类型
                    bytes_array = QtCore.QByteArray(bytes_array)

                bytes_remaining -= len(bytes_array)  #获取内容正确时，返回应该是0
                json_data += bytes_array.data().decode()  #获取内容

                if bytes_remaining == 0:
                    bytes_remaining = -1  #当前次读取成功后，将读取状态重新返回为-1，以便继续监听

                    data = json.loads(json_data)  #将字典读取出来
                    self.process_data(data)
                    json_data = ''

    def write(self, reply):
        """
        向客户端写入数据，需要在子类中实现。
        :return:
        """
        json_reply = json.dumps(reply)  #字典转json格式
        if self.socket.state() == QtNetwork.QTcpSocket.ConnectedState:
            header = '{}'.format(len(json_reply.encode())).zfill(ServerBase.HEADER_SIZE)  #套接字标头的信息长度
            data = QtCore.QByteArray('{}{}'.format(header, json_reply).encode())  #将标头与信息本身拼接

            self.socket.write(data)  #将QByteArray转换为int

    def write_error(self, error_msg):
        reply = {'success': False,
                 'msg': error_msg}

        self.write(reply)

    def process_data(self, data):
        """
        配置返回套接字的内容
        :param data:套接字标身字典
        :return:
        """
        reply = {'success': False}#要返回给客户端的套接字字典

        cmd = data['cmd']  #获取字典中的命令内容
        if cmd == 'ping':  #如果是ping链接是否相通，则直接设置返回内容为true
            reply['success'] = True
        else:
            self.process_cmd(cmd, data, reply)
            if not reply['success']:  #如果对接收的信息处理返回为false表示处理失败
                reply['cmd'] = cmd
                if 'msg' not in reply.keys():  #如果不是命令错误
                    reply['msg'] = u'未知错误'

        self.write(reply)

    def process_cmd(self, cmd, data, reply):
        """
        当信息不符合预期时，在这里生成msg信息，方便后续打印出来
        虽然没有返回值，但由于直接修改的reply字典，所以外部字典变量会直接被修改
        :param cmd: 套接字字典中cmd命令的内容
        :param data: 套接字完整字典
        :param reply: 服务器处理套接字是否成功的字典
        :return:
        """
        reply['msg'] = '无效的命令({})'.format(cmd)  #无效命令


class ExampleServer(ServerBase):
    """
    服务器继承类，一般在外部对基类继承使用
    """
    PORT = 20201

    def __init__(self, parent_window):
        """
        运行到该init时自动调用基类的init，开始监听该类提供的端口
        当收到套接字并调用process_cmd方法时，会先调用该类的process_cmd方法
        :param parent_window: 父级窗口对象
        """
        super(ExampleServer, self).__init__(parent_window)

        self.window = parent_window

    def process_cmd(self, cmd, data, reply):
        """
        重写基类的该方法
        :param cmd:套接字字典中cmd命令的内容
        :param data:套接字完整字典
        :param reply:服务器处理套接字是否成功的字典
        :return:
        """
        if cmd == 'echo':
            self.echo(data, reply)
        elif cmd == 'set_title':
            self.set_tite(data, reply)
        elif cmd == 'sleep':
            self.sleep(reply)
        else:  #当接收的信息在预期之外，则继承基类该方法的内容，返回无效命令
            super(ExampleServer, self).process_cmd(cmd, data, reply)

    def echo(self, data, reply):
        reply['result'] = data['text']
        reply['success'] = True

    def set_tite(self, data, reply):
        """
        设置父级窗口的标题（套接字内容调取方法案例）
        :param data: 套接字完整字典
        :param reply: 服务器处理套接字是否成功的字典
        :return:
        """
        self.window.setWindowTitle(data['title'])

        reply['result'] = True
        reply['success'] = True

    def sleep(self, reply):
        """
        暂停对应秒数（套接字内容调取方法案例）
        :param data: 套接字完整字典
        :param reply: 服务器处理套接字是否成功的字典
        :return:
        """
        for i in range(6):
            print('Sleeping {}'.format(i))
            time.sleep(1)

        reply['result'] = True
        reply['success'] = True


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    win = QtWidgets.QDialog()
    win.setWindowTitle('服务器端')
    win.setFixedSize(240, 150)
    QtWidgets.QPlainTextEdit(win)

    server = ExampleServer(win)

    win.show()

    app.exec_()
