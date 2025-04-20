from soft.impl.CallbackMsgSoft import CallbackMsgSoft
from soft.impl.ChatSoft import ChatSoft
from soft.impl.mysql.CreateGroupSoft import CreateGroupSoft
from soft.impl.DataHandlingSoft import DataHandlingSoft
from soft.impl.PublicKeySoft import PublicKeySoft
from soft.impl.mysql.GetRecentMsgSoft import GetRecentMsgSoft
from soft.impl.mysql.SendGroupMsgSoft import SendGroupMsgSoft

'''
软件管理器
'''
class SoftManager:
    def __init__(self):
        self.chat_soft = None
        self.data_handling_soft = DataHandlingSoft()
        self.public_key_soft = None
        self.create_group_soft = None
        self.callback_msg_soft = None
        self.send_group_msg_soft = None
        self.get_recent_msg_soft = None

    def register(self,tcp):
        self.chat_soft = ChatSoft(tcp)
        self.public_key_soft = PublicKeySoft(tcp)
        self.create_group_soft = CreateGroupSoft(tcp)
        self.callback_msg_soft = CallbackMsgSoft(tcp)
        self.send_group_msg_soft = SendGroupMsgSoft(tcp)
        self.get_recent_msg_soft = GetRecentMsgSoft(tcp)
