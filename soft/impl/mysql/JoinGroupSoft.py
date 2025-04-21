from typing import override

from soft.AbsSoft import AbsSoft


class JoinGroupSoft(AbsSoft):
    def __init__(self, tcp):
        self.tcp = tcp

    @override
    def run(self, **kwargs):
        group_number = kwargs["group_number"]
        user_id = kwargs["user_id"]
        return self.tcp.mysql.join_group(group_number=group_number, user_id=user_id)