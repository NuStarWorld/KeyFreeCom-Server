from typing import override

from enums.SendMode import SendMode
from soft.AbsSoft import AbsSoft


class CallbackMsgSoft(AbsSoft):
    def __init__(self, tcp):
        self.tcp = tcp

    @override
    def run(self,**kwargs):
        msg = kwargs["msg"]
        src_ip = kwargs["src_ip"]
        send_data = {
            "data": {
                "msg": msg
            },
            "type": "callback_msg"
        }
        dst_socket = self.tcp.client_manager.get_client(src_ip).get_client_socket()
        self.tcp.send_msg(send_data, dst_socket, SendMode.ENCRYPT)