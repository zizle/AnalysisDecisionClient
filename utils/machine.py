# _*_ coding:utf-8 _*_
# __Author__： zizle
from wmi import WMI
import hashlib


class MachineInfo(object):
    """获取电脑硬件信息"""
    def __init__(self):
        self.c = WMI()

    def main_board(self):
        """主板uuid+serialNumber"""
        board = self.c.Win32_BaseBoard()[0] if len(self.c.Win32_BaseBoard()) else None
        if board:
            uuid = board.qualifiers['UUID'][1:-1]  # 主板UUID
            serial_number = board.SerialNumber             # 主板序列号
            return uuid + serial_number
        else:
            return None

    def disk(self):
        """硬盘序列号"""
        disk = self.c.Win32_DiskDrive()[0] if len(self.c.Win32_DiskDrive()) else None
        if disk:
            return disk.SerialNumber.strip()

    def network_adapter(self):
        """网卡信息"""
        print(len(self.c.Win32_NetworkAdapter()))
        for n in self.c.Win32_NetworkAdapter():
            print(n.MACAddress)

    def cpu_info(self):
        """CPU信息"""
        for cpu in self.c.Win32_Processor():
            print(cpu)


def get_machine_code():
    machine = MachineInfo()
    try:
        md = hashlib.md5()
        main_board = machine.main_board()
        disk = machine.disk()
        md.update(main_board.encode('utf-8'))
        md.update(disk.encode('utf-8'))
    except Exception:
        return ''
    else:
        return md.hexdigest()
