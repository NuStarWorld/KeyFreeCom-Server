
from data.MySQL import MySQL
from server.impl.TCPServer import TCPServer

from server.impl.UDPServer import UDPServer


if __name__ == '__main__':
    mysql = MySQL()
    cursor = mysql.connect()
    cursor.execute('select version()')
    result = cursor.fetchall()
    tcp_server = TCPServer(mysql)
    udp_server = UDPServer(mysql)
