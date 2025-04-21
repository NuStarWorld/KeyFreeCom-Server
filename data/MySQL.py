import pymysql
import yaml


class MySQL:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.soft = None
        with open('resource/database.yml', 'r') as yml:
            mysql_dict = yaml.safe_load(yml)
            self.mysql_data = mysql_dict["MySQL"]

    """
    连接数据库并返回一个游标
    """

    def connect(self):
        conn = pymysql.connect(
            host=self.mysql_data["host"],
            port=self.mysql_data["port"],
            user=self.mysql_data["user"],
            password=self.mysql_data["passwd"],
            database=self.mysql_data["database"]
        )
        self.conn = conn

        self.cursor = conn.cursor()
        self.soft = self.Soft(self.conn, self.cursor)
        return conn.cursor()

    def register(self, **kwargs):
        return self.soft.register(**kwargs)

    def get_user_info(self, **kwargs) -> dict:
        return self.soft.get_user_info(**kwargs)

    def create_group(self,**kwargs):
        return self.soft.create_group(**kwargs)

    def send_group_message(self,**kwargs):
        return self.soft.send_group_message(**kwargs)

    def get_user_groups(self, **kwargs):
        return self.soft.get_user_groups(**kwargs)

    def get_recent_msg(self, **kwargs):
        return self.soft.get_recent_messages(**kwargs)
    def join_group(self, **kwargs):
        return self.soft.join_group(**kwargs)
    """
    软件接口
    """

    class Soft:
        def __init__(self, conn, cursor):
            self.cursor = cursor
            self.conn = conn

        """用户注册"""
        def register(self, **kwargs):
            sql = ("INSERT INTO `users` (`user_id`, `username`, `phone`, `avatar`, `status`)"
                   " VALUES (NULL, %s, %s, %s, %s)")
            try:
                self.cursor.execute(sql, (
                    "默认名称",
                    kwargs["user_phone"],
                    "example.png",
                    1
                ))
                self.conn.commit()
                print("完成一条来自 " + kwargs["lastIP"] + " 的注册请求")
                return True
            except Exception as ex:
                self.conn.rollback()
                print(ex)
                return False


        """获得用户数据"""

        def get_user_info(self, **kwargs):
            sql = "SELECT * from users where phone=%s"
            try:
                self.cursor.execute(sql, (kwargs["user_phone"],))  # 注意这里需要逗号创建元组
                result = self.cursor.fetchone()

                # 将结果转为字典
                if result:
                    columns = [col[0] for col in self.cursor.description]  # 获取字段名
                    return dict(zip(columns, result))
                return None  # 没有查询到结果时返回 None

            except Exception as ex:
                print(f"获取用户信息失败：{ex}")
                return None  # 异常时返回 None 保持一致性

        """新建群组（同时将创建者加入群成员）"""

        def create_group(self, **kwargs):
            group_number = kwargs["group_number"]
            group_name = kwargs["group_name"]

            sql = """
            INSERT INTO `chat_groups` 
            (`group_number`, `group_name`, `creator_id`) 
            VALUES (%s, %s, %s)
            """
            try:
                self.cursor.execute(sql, (
                    group_number,
                    kwargs["group_name"],
                    kwargs["creator_id"]
                ))
                # 将创建者加入群成员（使用 group_number）
                member_sql = """
                INSERT INTO `group_members` 
                (`group_number`, `user_id`) 
                VALUES (%s, %s)
                """
                self.cursor.execute(member_sql, (group_number, kwargs["creator_id"]))
                self.conn.commit()
                return {
                    "data": {
                        "result": "success",
                        "group_number": group_number,
                        "group_name": group_name
                    },
                    "type": "create_group"
                }
            except Exception as ex:
                self.conn.rollback()
                print(f"创建群组失败：{ex}")
                return {
                    "data": {
                        "result": "failed"
                    },
                    "type": "create_group"
                }

        """用户加入群组"""
        def join_group(self, **kwargs):
            # SQL 插入群成员表
            sql = (
                "INSERT INTO `group_members` (`group_number`, `user_id`) "
                "VALUES (%s, %s)"
            )
            try:
                # 执行插入操作
                self.cursor.execute(sql, (
                    kwargs["group_number"],
                    kwargs["user_id"]
                ))
                self.conn.commit()
                print(f"用户 {kwargs['user_id']} 成功加入群组 {kwargs['group_number']}")
                return {
                    "data": {
                        "result": "success"
                    },
                    "type": "join_group"
                }
            except Exception as ex:
                self.conn.rollback()
                # 根据错误类型细化提示
                if "Duplicate entry" in str(ex):
                    print(f"用户 {kwargs['user_id']} 已在群组 {kwargs['group_number']} 中")
                    return {
                        "data": {
                            "result": "failed",
                            "reason": "用户已加入该群组"
                        },
                        "type": "join_group"
                    }
                else:
                    print(f"加入群组失败：{ex}")
                    return {
                        "data": {
                            "result": "failed",
                            "reason": "加入群组失败"
                        },
                        "type": "join_group"
                    }
        """获取用户加入的所有群组"""
        def get_user_groups(self, **kwargs):
            # SQL 联查群组表和成员表
            sql = """
                SELECT cg.group_number, cg.group_name, cg.creator_id, cg.created_at 
                FROM chat_groups cg
                JOIN group_members gm ON cg.group_number = gm.group_number
                WHERE gm.user_id = %s
                """
            try:
                self.cursor.execute(sql, (kwargs["user_id"],))
                groups = self.cursor.fetchall()

                # 将结果转换为字典列表（可选）
                columns = [col[0] for col in self.cursor.description]
                result = [dict(zip(columns, row)) for row in groups]

                print(f"成功获取用户 {kwargs['user_id']} 的 {len(result)} 个群组")
                user_group = {
                    "data": {
                        "result": "success",
                        "groups": {}
                    },
                    "type": "get_groups"
                }
                index = 0
                for data in result:
                    user_group["data"]["groups"][index] = {
                        "group_number": data["group_number"],
                        "group_name": data["group_name"]
                    }
                    index += 1
                return user_group
            except Exception as ex:
                print(f"查询用户群组失败：{ex}")
                return {
                    "data": {
                        "result": "failed"
                    },
                    "type": "get_groups"
                }

        """向群组发送消息"""
        def send_group_message(self, **kwargs):
            # SQL 插入消息表
            sql = (
                "INSERT INTO `group_messages` "
                "(`group_number`, `sender_id`, `content`) "
                "VALUES (%s, %s, %s)"
            )
            try:
                # 执行插入操作
                self.cursor.execute(sql, (
                    kwargs["group_number"],
                    kwargs["sender_id"],
                    kwargs["content"]
                ))
                self.conn.commit()
                message_id = self.cursor.lastrowid
                print(f"用户 {kwargs['sender_id']} 向群组 {kwargs['group_number']} 发送消息，消息ID：{message_id}")
                return True
            except Exception as ex:
                self.conn.rollback()
                error_msg = f"发送消息失败：{ex}"
                # 细化常见错误类型提示
                if "foreign key constraint" in str(ex).lower():
                    error_msg += "（群组不存在或用户不在群中）"
                elif "Data too long" in str(ex):
                    error_msg += "（消息内容过长）"
                print(error_msg)
                return False

        """获取群组最近的10条聊天记录"""
        def get_recent_messages(self, **kwargs):
            sql = """
                SELECT message_id, sender_id, content, sent_at 
                FROM group_messages 
                WHERE group_number = %s 
                ORDER BY sent_at ASC 
                LIMIT 50
                """
            try:
                self.cursor.execute(sql, (kwargs["group_number"],))
                messages = self.cursor.fetchall()

                # 将结果转为字典列表（字段名映射）
                columns = [col[0] for col in self.cursor.description]
                result = [dict(zip(columns, row)) for row in messages]
                recent_msg = {
                    "data": {
                        "result": "success",
                        "messages": {}
                    },
                    "type": "get_recent_msg"
                }
                index = 0
                for data in result:
                    recent_msg["data"]["messages"][index] = {
                        "message_id": data["message_id"],
                        "sender_id": data["sender_id"],
                        "content": data["content"],
                        "sent_at": data["sent_at"].isoformat()
                    }
                    index += 1
                print(f"获取群组 {kwargs['group_number']} 的 {len(result)} 条最新消息")
                return recent_msg
            except Exception as ex:
                print(f"查询消息失败：{ex}")
                return []