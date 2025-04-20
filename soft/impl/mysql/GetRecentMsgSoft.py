from typing import override

from soft.AbsSoft import AbsSoft


class GetRecentMsgSoft(AbsSoft):

    def __init__(self, tcp):
        self.tcp = tcp

    @override
    def run(self, **kwargs):
        group_number = kwargs["group_number"]

        return self.tcp.mysql.get_recent_msg(group_number=group_number)