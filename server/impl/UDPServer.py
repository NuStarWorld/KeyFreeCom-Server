import json
import socket
import threading
from data.MySQL import *
import yaml

from soft.impl.PublicKeySoft import PublicKeySoft
from soft.AbsSoft import AbsSoft

"""
聊天服务器
"""


class UDPServer:
    def __init__(self, mysql: MySQL):
        self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with open("resource/serverconfig.yml") as yml:
            server_config = yaml.safe_load(yml)
            self.server_ip = server_config["ip"]
            self.server_port = server_config["port"]
        self.udp_server.bind((self.server_ip, self.server_port))
        self.mysql = mysql
        threading.Thread(target=self.recv_msg).start()
        print("UDP服务开启成功")

    def send_msg(self, msg, ip):
        self.udp_server.sendto(msg.encode("gbk"),ip)

    def recv_msg(self):
        while True:
            data, addr = self.udp_server.recvfrom(2048)
            msg = json.loads(data.decode("utf-8"))
            match msg:
                case {"method": "negotiate_key"}:
                    print(run(PublicKeySoft(self,addr, msg)))



def run(soft:AbsSoft):
    return soft.run()