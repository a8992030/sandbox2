from .hostos import HostOS
from .base import run_script
import netifaces

class MacOS(HostOS):
    def pre_exec(self, cconfig) -> bool:
        cmd = 'open -a XQuartz'
        result = run_script(cmd)
        if result[2] != 0:
            print(result[1].decode('utf8'))
            return False

        ip = self.get_ip(cconfig)
        cmd = 'xhost %s' % ip
        result = run_script(cmd)
        if result[2] != 0:
            print(result[1].decode('utf8'))
            return False

    def get_ip(self, cconfig) -> str:
        if cconfig.host.network_intf == 'lo0':
            idx = 1
        else:
            idx = 0
        # 18 is AF_LINK, 2 is AF_INET, 30 is AF_INET6
        return netifaces.ifaddresses(cconfig.host.network_intf)[2][idx]['addr']