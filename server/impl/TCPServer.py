import base64
import json
import socket
import struct
import threading
from typing import override

import managers
from data.MySQL import *
from data.Client import Client
from debug.Debug import Debug
from enums.SendMode import SendMode
from managers import SoftManager
from server.Server import Server
from soft import *
from soft.impl.DataHandlingSoft import DataHandlingType

class TCPServer(Server):
    def __init__(self, mysql: MySQL):
        self.client_manager = managers.client_manager
        managers.soft_manager.register(self)
        self.mysql = mysql
        self.debug = Debug()
        with open("resource/serverconfig.yml") as yml:
            server_config = yaml.safe_load(yml)
            self.server_ip = server_config["ip"]
            self.server_port = server_config["port"]
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.bind((self.server_ip, self.server_port))
        self.tcp_server.listen(100)
        threading.Thread(target=self.tcp_accept).start()
        print("TCP服务开启成功")

    @staticmethod
    def get_soft_manager() -> SoftManager:
        return managers.soft_manager

    """根据字符串ip地址获得socket 如果没有就返回None"""
    def get_tcp_client_socket(self, str_ip) -> socket:
        try:
            return self.client_manager.get_client(str_ip).get_client_socket()
        except KeyError:
            return None

    """接收客户端链接请求"""
    def tcp_accept(self):
        while True:
            client_tcp_socket, tcp_address = self.tcp_server.accept()
            tcp_client_str_ip = tcp_address[0] + ":" + str(tcp_address[1])
            print(tcp_client_str_ip, "用户已连接")
            # 将用户的socket暂存
            user_client = Client(self, tcp_address,client_tcp_socket)
            self.client_manager.add_client(tcp_client_str_ip, user_client)
            self.debug.debug_info("新的客户端链接，客户端列表:" + str(self.client_manager.get_all_client()))
            threading.Thread(target=self.receive_msg, args=(client_tcp_socket, tcp_client_str_ip)).start()

    """
    客户端链接后处理客户端发送的消息
    """
    @override
    def receive_msg(self, *args):
        client_socket = args[0]
        client_str_ip = args[1]
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                """
                客户端断开链接时会持续发送空消息
                断开客户端链接
                """
                if not data:
                    self.client_manager.remove_client(client_str_ip)
                    break
                # 获得字典数据
                dict_data = json.loads(data)
                if dict_data["type"] == "negotiate_key":
                    dict_data["data"]["ip"] = client_str_ip
                    self.check_register(dict_data["data"])
                    managers.callback_manager.dispatch(self, dict_data)
                else:
                    decrypt_data = json.loads(run(managers.soft_manager.data_handling_soft,
                                                  untreated_msg=dict_data["data"],
                                                  shared_key=self.client_manager.get_client(client_str_ip).get_client_shared_key(),
                                                  mode=DataHandlingType.DECRYPT_DATA))
                    dict_data["data"] = decrypt_data
                    dict_data["data"]["ip"] = client_str_ip
                    # 调度器执行回调方法
                    managers.callback_manager.dispatch(self, dict_data)

            except ConnectionResetError:
                self.client_manager.remove_client(client_str_ip)
                break

    def check_register(self, dict_data):
        user_phone = dict_data["user_phone"]
        check_result = self.mysql.get_user_info(user_phone=user_phone)
        self.debug.debug_info("检查注册结果:" + str(check_result))
        if check_result is None:
            self.mysql.register(user_phone=user_phone,level=0,lastIP=dict_data["ip"])

    @staticmethod
    def callback_msg(dict_data):
        run(managers.soft_manager.callback_msg_soft, msg=dict_data["msg"],
            src_ip=dict_data["src_ip"])

    @managers.callback_manager.register("send_group_msg")
    def send_group_msg(self, dict_data):
        sender_id = self.mysql.get_user_info(user_phone=dict_data["user_phone"])["user_id"]
        run(managers.soft_manager.send_group_msg_soft, group_number=dict_data["group_number"],
            sender_id=sender_id,
            content=dict_data["content"])

    @managers.callback_manager.register("get_group")
    def get_group(self,dict_data):
        user_id = self.mysql.get_user_info(user_phone=dict_data["user_phone"])["user_id"]
        result = self.mysql.get_user_groups(user_id=user_id)
        result["dst_ip"] = dict_data["ip"]
        result["sender_id"] = user_id
        self.send_msg(result, self.get_tcp_client_socket(dict_data["ip"]), SendMode.ENCRYPT)

    @managers.callback_manager.register("create_group")
    def create_group(self,dict_data):
        user_id = self.mysql.get_user_info(user_phone=dict_data["user_phone"])["user_id"]
        result = run(managers.soft_manager.create_group_soft,
            group_name=dict_data["group_name"],
            group_number=dict_data["group_number"],
            creator_id=user_id)
        result["dst_ip"] = dict_data["ip"]
        self.send_msg(result, self.get_tcp_client_socket(dict_data["ip"]), SendMode.ENCRYPT)

    @managers.callback_manager.register("negotiate_key")
    def negotiate_key(self, dict_data):
        shared_key = run(managers.soft_manager.public_key_soft,user_a_data=dict_data)
        self.client_manager.get_client(dict_data["ip"]).set_client_shared_key(shared_key)
        self.client_manager.get_client(dict_data["ip"]).set_user_phone(dict_data["user_phone"])
        self.debug.debug_info("客户端完成密钥协商" + self.client_manager.get_client(dict_data["ip"]).to_string())

    @managers.callback_manager.register("send_data")
    def send_user_msg(self, dict_data):
        run(managers.soft_manager.chat_soft, data=dict_data)

    @managers.callback_manager.register("encrypt_msg")
    def decrypt_msg(self, dict_data):
        pass

    @override
    def send_msg(self, dict_data, dst_socket, mode):
        match mode:
            case SendMode.ENCRYPT:
                shared_key = managers.client_manager.get_client(dict_data["dst_ip"]).get_client_shared_key()
                encrypt_msg = base64.b64encode(run(managers.soft_manager.data_handling_soft,
                                                   untreated_msg=json.dumps(dict_data["data"], ensure_ascii=False),
                                                   shared_key=shared_key,
                                                   mode=DataHandlingType.ENCRYPT_DATA)).decode('utf-8')
                dict_data["data"] = encrypt_msg
                dict_data.pop("dst_ip")
                send_data = json.dumps(dict_data, ensure_ascii=False).encode("utf-8")
                header = struct.pack(">I", len(send_data))
                dst_socket.sendall(header + send_data)
            case SendMode.UN_ENCRYPT:
                dict_data.pop("dst_ip")
                send_data = json.dumps(dict_data, ensure_ascii=False).encode("utf-8")
                header = struct.pack(">I", len(send_data))
                dst_socket.sendall(header + send_data)

