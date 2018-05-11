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

        ip = netifaces.ifaddresses(cconfig.host.network_intf)[2][0]['addr']
        cmd = 'xhost %s' % ip
        result = run_script(cmd)
        if result[2] != 0:
            print(result[1].decode('utf8'))
            return False