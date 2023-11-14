#coding=gbk
import socket
import sys

BUFFER_SIZE = 4096 #缓冲区大小，命令或返回都不能超出该大小
prot = 21111

if len(sys.argv) > 1:
    prot = sys.argv[1]

maya_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#STREAM流格式套接字，有序安全；DGRAM无连接套接字，快，不稳定
maya_socket.connect(('localhost', prot))

maya_socket.sendall("stop".encode())#py2下可以直接用字符串，py3下需要在字符串后面加上.encode()
print(maya_socket.recv(BUFFER_SIZE).decode())#py2下可以直接打印，py3下需要加上.decode()

maya_socket.close()
