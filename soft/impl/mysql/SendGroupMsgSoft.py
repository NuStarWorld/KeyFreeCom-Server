from typing import override

from enums.SendMode import SendMode
from soft.AbsSoft import AbsSoft


class SendGroupMsgSoft(AbsSoft):
    def __init__(self,tcp):
        self.tcp = tcp

    @override
    def run(self,**kwargs):
        group_number = kwargs["group_number"]
        content = kwargs["content"]
        sender_id = kwargs["sender_id"]
        # 将收到的消息保存到数据库中
        result = self.tcp.mysql.send_group_message(
            group_number=group_number,
            content=content,
            sender_id=sender_id
        )
        # 如果消息保存成功 则向所有用户发送消息
        if result:
            for client in self.tcp.client_manager.clients_dict.values():
                groups = client.get_user_groups()["data"]["groups"]
                for key in groups:
                    if str(group_number) == str(groups[key]["group_number"]):
                        self.tcp.send_msg(
                            dict_data={
                                "data": {
                                    "group_number": group_number,
                                    "content": content,
                                    "sender_id": sender_id,
                                    "result": "success"
                                },
                                "dst_ip": client.get_client_str_ip(),
                                "type": "send_group_msg"
                            },
                            dst_socket=client.get_client_socket(),
                            mode=SendMode.ENCRYPT
                        )