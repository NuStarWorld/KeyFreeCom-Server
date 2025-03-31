import json
from typing import override

from enums.SendMode import SendMode
from soft.AbsSoft import AbsSoft


class ChatSoft(AbsSoft):
    def __init__(self, tcp):
        self.tcp = tcp


    @override
    def run(self,**kwargs):
        data = kwargs["data"]
        user_phone = data["user_phone"]
        dst_ip = data["destination_ip"]
        msg = data["msg"]
        send_data = {
            "data": {
                "user_phone": user_phone,
                "msg": msg
            },
            "dst_ip": dst_ip,
            "type": "user_msg"
        }
        dst_socket = self.tcp.client_manager.get_client(dst_ip).get_client_socket()
        self.tcp.send_msg(send_data, dst_socket,SendMode.ENCRYPT)
        pass