from sympy import isprime
from math import ceil, log
import socket
import json
from random import randint
from gmssl.sm3 import sm3_hash

class Curve:
    """
    椭圆曲线类，默认使用SM2手册中推荐的椭圆曲线之一。可以进行椭圆曲线上点的加法和乘法。
    """

    def __init__(self,
                 p=0x8542D69E4C044F18E8B92435BF6FF7DE457283915C45517D722EDB8B08F1DFC3,
                 a=0x787968B4FA32C3FD2417842E73BBFEFF2F3C848B6831D7E0EC65228B3937E498,
                 b=0x63E4C6D3B23B0C849CF84241484BFE48F61D59A5B16BA06E6E12D1DA27C5249A,
                 g_x=0x421DEBD61B62EAB6746434EBC3CC315E32220B3BADD50BDC4C4E6C147FEDD43D,
                 g_y=0x0680512BCBB42C07D47349D2153B70C4E5D7FDFCBFA36EA1A85841B9E46E09A2,
                 n=0x8542D69E4C044F18E8B92435BF6FF7DD297720630485628D5AE74EE7C32E79B7,
                 h=1,
                 ):
        self.p = p
        self.a = a
        self.b = b
        self.g_x = g_x
        self.g_y = g_y
        self.n = n
        self.h = h
        self.bytes_len = ceil(ceil(log(self.p, 2)) / 8) * 2

    def multiply(self, p, k):
        """
        椭圆曲线上的倍点运算，计算 k 倍的点 p，即 [k]p
        :param p: 椭圆曲线上的点，元组类型，形如 (11.0, 12.0)
        :param k: 倍数 k，int类型
        :return: 椭圆曲线上的点，元组类型，形如 (11.0, 12.0)
        """
        return self.__from_jacobian(self.__jacobian_multiply(self.__to_jacobian(p), k))

    def add(self, p, q):
        """
        椭圆曲线上的加法运算，计算点 p + 点 q。即 (x1,y1)+(x2,y2)
        :param p: 椭圆曲线上的点，元组类型，形如 (11.0, 12.0)
        :param q: 椭圆曲线上的点，元组类型，形如 (11.0, 12.0)
        :return: 椭圆曲线上的点，元组类型，形如 (11.0, 12.0)
        """
        return self.__from_jacobian(self.__jacobian_add(self.__to_jacobian(p), self.__to_jacobian(q)))

    @staticmethod
    def __inv(a, n):
        if a == 0:
            return 0
        lm, hm = 1, 0
        low, high = a % n, n
        while low > 1:
            r = high // low
            nm, new = hm - lm * r, high - low * r
            lm, low, hm, high = nm, new, lm, low
        return lm % n

    @staticmethod
    def __to_jacobian(p):
        p_x, p_y = p
        return p_x, p_y, 1

    def __from_jacobian(self, Xp_Yp_Zp):
        p_x, p_y, p_z = Xp_Yp_Zp
        z = self.__inv(p_z, self.p)
        return (p_x * z ** 2) % self.p, (p_y * z ** 3) % self.p

    def __jacobian_double(self, p):
        p_x, p_y, p_z = p
        if not p_y:
            return 0, 0, 0
        ysq = (p_y ** 2) % self.p
        S = (4 * p_x * ysq) % self.p
        M = (3 * p_x ** 2 + self.a * p_z ** 4) % self.p
        nx = (M ** 2 - 2 * S) % self.p
        ny = (M * (S - nx) - 8 * ysq ** 2) % self.p
        nz = (2 * p_y * p_z) % self.p

        return nx, ny, nz

    def __jacobian_add(self, p, q):
        p_x, p_y, p_z = p
        q_x, q_y, q_z = q
        if not p_y:
            return q_x, q_y, q_z
        if not q_y:
            return p_x, p_y, p_z

        U1 = (p_x * q_z ** 2) % self.p
        U2 = (q_x * p_z ** 2) % self.p
        S1 = (p_y * q_z ** 3) % self.p
        S2 = (q_y * p_z ** 3) % self.p
        if U1 == U2:
            if S1 != S2:
                return 0, 0, 1
            return self.__jacobian_double((p_x, p_y, p_z))

        H = U2 - U1
        R = S2 - S1
        H2 = (H * H) % self.p
        H3 = (H * H2) % self.p
        U1H2 = (U1 * H2) % self.p
        nx = (R ** 2 - H3 - 2 * U1H2) % self.p
        ny = (R * (U1H2 - nx) - S1 * H3) % self.p
        nz = (H * p_z * q_z) % self.p
        return nx, ny, nz

    def __jacobian_multiply(self, p, k):
        p_x, p_y, p_z = p

        if p_y == 0 or k == 0:
            return 0, 0, 1
        if k == 1:
            return p_x, p_y, p_z
        if k < 0 or k >= self.n:
            return self.__jacobian_multiply((p_x, p_y, p_z), k % self.n)
        if (k % 2) == 0:
            return self.__jacobian_double(self.__jacobian_multiply((p_x, p_y, p_z), k // 2))
        if (k % 2) == 1:
            return self.__jacobian_add(self.__jacobian_double(self.__jacobian_multiply((p_x, p_y, p_z), k // 2)),
                                       (p_x, p_y, p_z))

    def int_to_bytes(self, x):
        """
        将非负整数 x 转换为长度为 self.klen 的字节串。klen 由椭圆曲线的参数 p 在创建对象时确定。
        :param x: 非负整数 x，int类型
        :return: 长度为 k 的字节串，如果转换后长度小于 self.klen 则高位补 0，str类型
        """
        if x < 0:
            print("只能将非负整数转换为字节串！")
            exit(1)
        else:
            return hex(x)[2:].rjust(self.bytes_len, "0")

    @staticmethod
    def bytes_to_int(x):
        """
        将字节串 x 转换为整数
        :param x: 字节串 x，str类型，形如 ac9469d628349c73
        :return: 整数，int类型
        """
        return int(x, 16)

    @staticmethod
    def bit_to_bytes(x):
        """
        将比特串 x 按八位一组转换为字节串
        :param x: 比特串 x，str类型，形如 000000000000111100000001
        :return: 字节串，str类型，形如 0f1
        """
        result = ""
        i = 0
        while True:
            if i >= len(x):
                break
            else:
                result += hex(int(x[i:i + 8], 2))[2:]
                i += 8

        return result

    @staticmethod
    def bytes_to_bit(x):
        """
        将字节串 x 转换为比特串，每一个字节都能转换为 8 位比特串，高位补 0
        :param x: 字节串 x，str类型，形如 0f1
        :return: 比特串，str类型，例如 00000000 00001111 00000001
        """
        result = ""

        for i in x:
            result += bin(int(i, 16))[2:].rjust(8, "0")

        return result

    def domain_element_to_bytes(self, x):
        """
        将域元素转换为字节串
        :param x: 域元素 x，整数，int类型；也可以为比特串，str类型。
        :return: 字节串，str类型
        """
        if self.p % 2 == 1 and isprime(self.p):
            return self.int_to_bytes(x)
        elif self.p % 2 == 0:
            return self.bit_to_bytes(x)

    def bytes_to_domain_element(self, x):
        """
        将字节串转换为域元素
        :param x: 域元素 x，整数，int类型；也可以为比特串，str类型。
        :return: 域元素。如果为素域上的椭圆曲线群，则返回整数，int类型。如果为 2 的次方上的椭圆曲线群，则返回比特串，str类型。
        """
        if self.p % 2 == 1 and isprime(self.p):
            return self.bytes_to_int(x)
        elif self.p % 2 == 0:
            return self.bytes_to_bit(x)

    def domain_element_to_int(self, x):
        """
        将域元素转换为整数
        :param x: 域元素 x，可以为整数，int类型；也可以为比特串，str类型。
        :return: 整数，int类型
        """
        if self.p % 2 == 1 and isprime(self.p):
            return x
        elif self.p % 2 == 0:
            return self.bytes_to_int(self.bit_to_bytes(x))

    def dot_to_bytes(self, p):
        """
        将椭圆曲线上的点转换为字节串，使用未压缩形式表示。
        :return: 字节串，str类型，必定以 04 开头，形如“04C424”。
        """
        p_x, p_y = p
        bytes_x = self.domain_element_to_bytes(p_x)
        bytes_y = self.domain_element_to_bytes(p_y)
        return "04" + bytes_x + bytes_y

    def bytes_to_dot(self, bytes_string):
        """
        将未压缩形式的字节串转换为椭圆曲线上的点
        :param bytes_string: 未压缩形式的字节串，以 04 开头，str类型
        :return: 横坐标 x，纵坐标 y，均为int类型。
        """
        if bytes_string[:2] != "04":
            print("字节串开头不为04，转换错误！")
            exit(1)
        else:
            bytes_x = bytes_string[2:self.bytes_len + 2]
            bytes_y = bytes_string[self.bytes_len + 2:]
            x = self.bytes_to_domain_element(bytes_x)
            y = self.bytes_to_domain_element(bytes_y)
            return x, y
class Sm2KeyAgreement:
    def __init__(self, curve, id, entl, klen=16):
        """
        创建用于密钥交换的用户
        :param curve: 椭圆曲线对象
        :param id: 用户ID，16进制字节串，str类型
        :param entl: 用户ID的长度，用4位16进制数表示，str类型，形如 0044
        :param klen: 最终协商出密钥的长度，int类型
        """
        self.curve = curve
        self.id = id
        self.entl = entl
        self.tem_pri_key, self.tem_pub_key = self.generate_key_pair()  # 生成临时公钥和私钥
        self.pre_pri_key, self.pre_pub_key = self.generate_key_pair()  # 生成永久公钥和私钥
        self.klen = klen
        self.id_auth_code = sm3_hash([x for x in (
                self.entl + self.id + self.curve.int_to_bytes(self.curve.a) + self.curve.int_to_bytes(
            self.curve.b) + self.curve.int_to_bytes(
            self.curve.g_x) + self.curve.int_to_bytes(
            self.curve.g_y) + self.curve.int_to_bytes(self.pre_pub_key[0]) + self.curve.int_to_bytes(
            self.pre_pub_key[1])).encode()])

    def generate_key_pair(self):
        """
        生成椭圆曲线上的私钥和对应的公钥
        :return: 椭圆曲线上的私钥，椭圆曲线上的公钥，int类型和元组类型，形如216546584, (321563416,2165465)
        """
        # 利用随机数生成私钥
        private_key = randint(1, self.curve.n - 1)

        # 利用私钥和倍点运算生成公钥
        public_key = (self.curve.multiply((self.curve.g_x, self.curve.g_y), private_key))

        return private_key, public_key

    def key_adgreement(self, another_user_permanent_pub_key, another_user_tem_pub_key):
        """
        进行SM2密钥交换
        :param another_user_permanent_pub_key: 另外一个用户的公钥，以04开头的16进制字节串，str类型，形如04654987C5A
        :param another_user_tem_pub_key: 另外一个用户的临时公钥，以04开头的16进制字节串，str类型，形如04654987C5A
        :return: SM2密钥交换中的vx和vy，16进制字节串，str类型，形如2318498AC, 23165AB
        """
        p_b = self.curve.bytes_to_dot(another_user_permanent_pub_key)
        r_b = self.curve.bytes_to_dot(another_user_tem_pub_key)

        d_a = self.pre_pri_key
        r_a = self.tem_pri_key

        x_1 = self.tem_pub_key[0]

        x_2 = r_b[0]
        y_2 = r_b[1]

        w = ceil(ceil(log(self.curve.n, 2)) / 2) - 1
        x1_overline = 2 ** w + (x_1 & (2 ** w - 1))
        t_a = (d_a + x1_overline * r_a) % self.curve.n

        # 判断接收到的用户B的公钥是否在椭圆曲线上
        if (y_2 ** 2) % self.curve.p == (x_2 ** 3 + self.curve.a * x_2 + self.curve.b) % self.curve.p:
            x2_overline = 2 ** w + (x_2 & (2 ** w - 1))

            tem_dot = self.curve.multiply(r_b, x2_overline)

            tem_dot = self.curve.add(p_b, tem_dot)

            v_x, v_y = self.curve.multiply(tem_dot, self.curve.h * t_a)

            v_x = self.curve.int_to_bytes(v_x)
            v_y = self.curve.int_to_bytes(v_y)

            return v_x, v_y


def send_user_a_data_get_user_b_data(p_a, r_a, z_a, user_b_address):
    """
    通过socket传递用户A的公钥、临时会话公钥、身份认证码，并接收用户B的公钥、临时会话公钥、身份认证码
    :param p_a: 用户A的公钥
    :param r_a: 用户A的临时会话公钥
    :param z_a: 用户A的身份认证码
    :return:
    """
    # 创建一个客户端套接字对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接到用户B的 IP 地址和端口号
    s.connect(user_b_address)
    print("成功连接到服务器！")

    # 接收用户B发送过来的数据
    rec_data = s.recv(1024).decode()
    rec_data = json.loads(rec_data)

    # 向用户B发送数据
    send_data = json.dumps({"p_a": p_a, "r_a": r_a, "z_a": z_a})
    s.send(send_data.encode())

    # 关闭套接字
    s.close()

    return rec_data


def send_user_b_data_get_user_a_data(p_b, r_b, z_b, bind_address):
    """
    通过socket传递用户B的公钥、临时会话公钥、身份认证码，并接收用户A的公钥、临时会话公钥、身份认证码
    :param p_b: 用户B的公钥
    :param r_b: 用户B的临时会话公钥
    :param z_b: 用户B的身份认证码
    :return:
    """
    # 创建一个服务端套接字对象
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 绑定一个 IP 地址和端口号
    s.bind(bind_address)

    # 开始 TCP 监听
    s.listen(5)

    # 接受用户A连接
    print("等待客户端连接中......")
    conn, address = s.accept()

    # 向用户A发送数据
    send_data = json.dumps({"p_b": p_b, "r_b": r_b, "z_b": z_b})
    conn.send(send_data.encode())

    # 接收用户A发送回来的数据
    rec_data = conn.recv(1024).decode()
    rec_data = json.loads(rec_data)

    # 关闭套接字
    conn.close()
    s.close()

    return rec_data


def calculate_id_and_entl(user_id: str, encoding: str = "utf-8") -> tuple[str, str]:
    """
    计算 SM2 协议中的用户身份标识 (id_b) 和长度标识 (entl_b)

    :param user_id: 用户身份字符串，例如 "ALICE123@YAHOO.COM"
    :param encoding: 字符串编码方式，默认为 utf-8
    :return: 元组 (id_b_hex, entl_b_hex)
    """
    # 将字符串编码为字节
    id_bytes = user_id.encode(encoding)

    # 计算 entl_b（用户ID的比特长度，高位在前）
    bit_length = len(id_bytes) * 8
    entl_b = bit_length.to_bytes(2, byteorder="big").hex().upper()

    # 转换为十六进制字符串
    id_b_hex = id_bytes.hex().upper()

    return id_b_hex, entl_b