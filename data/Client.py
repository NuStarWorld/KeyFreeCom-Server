class Client:
    def __init__(self,tcp, client_ip, client_socket):
        self.tcp = tcp
        self.user_phone = ""
        self.client_shared_key = ""
        self.client_str_ip = client_ip[0] + ":" + str(client_ip[1])
        self.client_ip = client_ip
        self.client_socket = client_socket
        self.user_id = ""

    def set_client_shared_key(self,shared_key:str):
        self.client_shared_key = shared_key

    def set_user_phone(self, user_phone:str):
        self.user_phone = user_phone

    def get_client_shared_key(self):
        return self.client_shared_key

    def get_client_str_ip(self):
        return self.client_str_ip

    def get_client_socket(self):
        return self.client_socket

    def get_user_phone(self):
        return self.user_phone

    # 获取用户id
    def get_user_id(self):
        user_id = self.tcp.mysql.get_user_info(user_phone=self.user_phone)["user_id"]
        if self.user_id == "" :
            self.user_id = user_id
        return user_id
    def get_user_groups(self):
        return self.tcp.mysql.get_user_groups(user_id=self.user_id if self.user_id != "" else self.get_user_id())
    def to_string(self):
        return str({
            "user_phone": self.user_phone,
            "client_str_ip": self.client_str_ip,
            "client_shared_key": self.client_shared_key
        })