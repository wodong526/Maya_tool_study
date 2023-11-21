#coding=gbk
import socket
import traceback
import json
import time


class ClientBase(object):
    """
    客户端
    """
    PORT = 20201 #端口
    HEADER_SIZE = 10  #缓冲区大小

    def __init__(self, timeout=2):
        self.timeout = timeout#发出信息后的等待时长
        self.port = self.__class__.PORT

        self.discard_count = 0

    def connect(self, port=-1):
        if port >= 0:
            self.port = port
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', self.port))  #连接到端口
            self.client_socket.setblocking(0)#设置为非阻塞模式。调用recv()没有发现任何数据将引发socket.error异常
        except:
            traceback.print_exc()
            return False

        return True

    def disconnect(self):
        try:
            self.client_socket.close()
        except:
            traceback.print_exc()
            return False

        return True

    def send(self, cmd):
        json_cmd = json.dumps(cmd)#字典转json操作
        message = []
        message.append('{}'.format(len(json_cmd.encode())).zfill(ClientBase.HEADER_SIZE))
        message.append(json_cmd)

        try:
            msg_str = ''.join(message)
            self.client_socket.sendall(msg_str.encode())#向端口发送信息
        except:
            traceback.print_exc()
            return None

        return self.recv()

    def recv(self):
        """
        获取数据
        :return:
        """
        total_data = []
        data = ''
        reply_length = 0
        bytes_remaining = ClientBase.HEADER_SIZE

        start_time = time.time()
        while time.time() - start_time < self.timeout:#当在等待时长内
            try:
                data = self.client_socket.recv(bytes_remaining)#读取指定长度的套接字
            except:
                time.sleep(0.01)#没读取到时暂停0.01秒再获取
                continue

            if data:#读取到套接字时
                total_data.append(data)
                bytes_remaining -= len(data)#指定长度减去标头或标身的长度后，在预期内则都为0
                if bytes_remaining <= 0:#
                    for i in range(len(total_data)):#将套接字储存列表内容从字节转为字符串
                        total_data[i] = total_data[i].decode()

                    if reply_length == 0:#为0时为标头
                        header = ''.join(total_data)
                        reply_length = int(header)#标头的整形表示标身的长度
                        bytes_remaining = reply_length#将指定长度指定为标身的长度
                        total_data = []#清空套接字储存列表
                    else:#此时为标身
                        if self.discard_count > 0:#当需要跳过时
                            self.discard_count -= 1
                            return self.recv()#超时时重新监听下一次

                        reply_json = ''.join(total_data)
                        return json.loads(reply_json)

        self.discard_count += 1#当超时时将需要跳过的监听套接字加一，以方便跳过
        raise RuntimeError('等待响应超时')

    def is_valid_reply(self, reply):
        """
        检查返回信息是否符合预期规范
        :param reply: 要检查的信息
        :return: True:符合
                 False:不符合
        """
        if not reply:
            print('[error] 无效答复')
            return False

        if not reply['success']:
            print('[error] {} 失败: {}'.format(reply['cmd'], reply['msg']))
            return

        return True

    def ping(self):
        cmd = {'cmd': 'ping'}

        reply = self.send(cmd)

        if self.is_valid_reply(reply):
            return True
        else:
            return False

class ExampleClient(ClientBase):
    PORT = 20201

    def echo(self, text):
        cmd = {'cmd': 'echo',
               'text': text}
        reply = self.send(cmd)
        if self.is_valid_reply(reply):
            return reply['result']
        else:
            return None

    def set_title(self, title):
        cmd = {'cmd': 'set_title',
               'title': title}

        reply = self.send(cmd)
        if self.is_valid_reply(reply):
            return reply['result']
        else:
            return None

    def sleep(self):
        cmd = {'cmd': 'sleep'}

        reply = self.send(cmd)
        if self.is_valid_reply(reply):
            return reply['result']
        else:
            return None


if __name__ == '__main__':
    client = ExampleClient()
    if client.connect():
        print('链接成功')

        print(client.ping())#测试套接字是否能够ping通
        #print(client.echo('成功了吗'))
        #print(client.set_title(u'这是标题'))
        print(client.sleep())#因为在基类中默认设置了等待服务端回应时间为2秒，而服务端该方法等待了6秒，所以会报错超出等待时间
        if client.disconnect():
            print('断开连接')
    else:
        print('连接失败')
