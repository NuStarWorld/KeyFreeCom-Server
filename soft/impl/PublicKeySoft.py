from typing import override

from enums.SendMode import SendMode
from utils.ExchangeKeyUtil import Curve,Sm2KeyAgreement
from gmssl.sm3 import sm3_kdf

from soft.AbsSoft import AbsSoft
import utils.ExchangeKeyUtil

class PublicKeySoft(AbsSoft):
    def __init__(self, tcp):
        self.tcp = tcp


    @override
    def run(self,**kwargs):
        user_a_data = kwargs["user_a_data"]
        id_entl_b = utils.ExchangeKeyUtil.calculate_id_and_entl("KeyFreeComServer")
        curve = Curve()
        user_b = Sm2KeyAgreement(curve, id_entl_b[0], id_entl_b[1])
        p_b = user_b.curve.dot_to_bytes(user_b.pre_pub_key)
        r_b = user_b.curve.dot_to_bytes(user_b.tem_pub_key)
        z_b = user_b.id_auth_code
        send_data ={
            "data": {
                "p_b": p_b,
                "r_b": r_b,
                "z_b": z_b,
            },
            "type": "negotiate_key",
            "dst_ip": user_a_data["ip"]
        }
        client_ip = user_a_data["ip"]
        # 发送参数
        self.tcp.send_msg(send_data, self.tcp.get_tcp_client_socket(client_ip), SendMode.UN_ENCRYPT)
        p_a = user_a_data["p_a"]
        r_a = user_a_data["r_a"]
        z_a = user_a_data["z_a"]
        v_x, v_y = user_b.key_adgreement(p_a, r_a)
        k_a = sm3_kdf((v_x + v_y + z_a + z_b).encode(), user_b.klen)
        return k_a