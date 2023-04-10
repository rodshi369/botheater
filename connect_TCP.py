import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import const

_connectionTCP = {}


def get_connection(unit: str, host: str, port):
    global _connectionTCP
    _connectionTCP = {**_connectionTCP, str(unit): modbus_tcp.TcpMaster(host, port)}
    _connectionTCP[str(unit)].set_timeout(5.0)

def read_unit(unit, command, adrr, quantity):
    try:
        rez = _connectionTCP[str(unit)].execute(unit, command, adrr, quantity)
        return rez
    except Exception as err:
        return None

def write_unit(unit, command, adrr, value):
    try:
        _connectionTCP[str(unit)].execute(unit, command, adrr, output_value=[value])
        return True
    except Exception as err:
        return False

ip = const.IP
port = const.PORT

get_connection(1,ip, port)