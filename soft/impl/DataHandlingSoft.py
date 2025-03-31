import base64
import os
from typing import override
from gmssl import sm4
from enum import Enum


from soft.AbsSoft import AbsSoft

class DataHandlingType(Enum):
    ENCRYPT_DATA = 0
    DECRYPT_DATA = 1

'''加解密消息'''
class DataHandlingSoft(AbsSoft):

    """
    解密字符串
    """
    @staticmethod
    def _decrypt_data(untreated_msg:str, shared_key:str) -> str:
        decode_untreated_msg = base64.b64decode(untreated_msg)
        iv = decode_untreated_msg[:16]
        untreated_msg = decode_untreated_msg[16:]
        cipher = sm4.CryptSM4()
        cipher.set_key(shared_key.encode('utf-8'),sm4.SM4_DECRYPT)
        plaintext = cipher.crypt_cbc(iv, untreated_msg)
        return plaintext.decode('utf-8')

    """
    加密字符串数据
    iv:初始化向量 用于随机化加密和增加安全性
    """
    @staticmethod
    def _encrypt_data(untreated_msg:str, shared_key:str) -> str:
        iv = os.urandom(16)
        plaintext = untreated_msg.encode('utf-8')
        cipher = sm4.CryptSM4()
        cipher.set_key(shared_key.encode('utf-8'),sm4.SM4_ENCRYPT)
        return iv+cipher.crypt_cbc(iv, plaintext)

    @override
    def run(self,**kwargs):
        untreated_msg = kwargs["untreated_msg"]
        shared_key = kwargs["shared_key"]
        mode = kwargs["mode"]
        match mode:
            case DataHandlingType.DECRYPT_DATA:
                return self._decrypt_data(untreated_msg, shared_key)
            case DataHandlingType.ENCRYPT_DATA:
                return self._encrypt_data(untreated_msg, shared_key)


