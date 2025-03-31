
from data.Client import Client


"""
客户端管理器
key: 字符串IP地址
value: 客户端对象
"""
class ClientManager:
    def __init__(self):
        self.clients_dict = {}

    def add_client(self, key:str, value:Client):
        self.clients_dict[key] = value

    def get_all_client(self):
        return self.clients_dict

    def remove_client(self, key:str):
        self.clients_dict.pop(key)

    def get_client(self, str_ip:str) -> Client | None:
        try:
            return self.clients_dict[str_ip]
        except KeyError:
            return None

    """
    返回所有客户端的共享密钥
    """
    def get_shared_keys(self) -> dict[str, str]:
        client_shared_keys = {}
        for client_tuple in self.clients_dict.items():
            client_shared_key = client_tuple[1].get_client_shared_key()
            client_shared_keys[client_tuple[0]] = client_shared_key

        return client_shared_keys
