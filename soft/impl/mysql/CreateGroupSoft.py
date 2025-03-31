from typing import override

from soft.AbsSoft import AbsSoft


class CreateGroupSoft(AbsSoft):

    def __init__(self, tcp):
        self.tcp = tcp

    @override
    def run(self,**kwargs):
        group_number = kwargs["group_number"]
        creator_id = kwargs["creator_id"]
        group_name = kwargs["group_name"]
        return self.tcp.mysql.create_group(group_name=group_name,
                                    group_number=group_number,
                                    creator_id=creator_id)
