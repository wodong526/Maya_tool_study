#coding=gbk
import socket

BUFFER_SIZE = 4096
PORT = 21111

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(('localhost', PORT))#绑定电脑ip地址
    sock.listen()#开始监听，当有传参时，参数表示服务端同时处理几个用户端，多余的用户端会排队

    while True:
        connection, address = sock.accept()#返回[ip套接字， （主机地址， 端口）]，端口每次返回不一样
        with connection:
            print('链接：{}'.format(address))

            while True:
                data = connection.recv(BUFFER_SIZE)#接收套接字
                if not data:
                    break

                if data.decode().strip() == 'stop':#当客户端返回的是关闭信息时。去掉收尾空格
                    connection.sendall('gg'.encode())#向客户端传输套接字
                    connection.shutdown(1)#关闭socket的读写功能，0关闭读、1关闭写、2都关闭
                    connection.close()#释放Socket占用的所有资源，并且关闭该连接
                    exit()

                connection.sendall(data)#向客户端传输套接字
