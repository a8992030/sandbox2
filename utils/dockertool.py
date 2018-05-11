#!/usr/bin/env python3
import argparse
import netifaces
import os
import socket
import sys
import time
from ruamel.yaml import YAML
from ruamel.yaml import comments
from models.containconfig import ContainerConfig
from models.hostos import HostOS
from models.base import run_script


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def gen_script_file(bash_cmd) -> str:
    f_name = '.bash_cmd.tmp'
    f = open(f_name, 'w')
    f.write(bash_cmd + '\n')
    f.close()
    os.chmod(f_name, 0o755)
    return f_name


def replace_date(cconfig: ContainerConfig, value: str) -> str:
    return value.replace('%DATE', time.strftime('%Y%m%d_%H%M%S'), 1)


def replace_home(cconfig: ContainerConfig, value: str) -> str:
    return value.replace('%HOME', os.getenv('HOME'), 1)


def replace_ip(cconfig: ContainerConfig, value: str) -> str:
    # print(replace_ip.__name__)
    # 18 is AF_LINK, 2 is AF_INET, 30 is AF_INET6
    ip = netifaces.ifaddresses(cconfig.host.network_intf)[2][0]['addr']
    return value.replace('%IP', ip, 1)


def replace_hostname(cconfig:ContainerConfig, value: str) -> str:
    return value.replace('%HOSTNAME', socket.gethostname(), 1)

SPECIAL_VAL = {'%DATE': replace_date,
               '%HOME': replace_home,
               '%IP': replace_ip,
               '%HOSTNAME': replace_hostname
               }


def convert_val(cconfig, value):
    if type(value) is not str:
        return value

    for special_key in SPECIAL_VAL.keys():
        if special_key in value:
            return SPECIAL_VAL[special_key](cconfig, value)
    return value

script_docker_images = \
"""
image_num=$(($(docker images | wc -l) - 1))
images=$(docker images | tail -n$image_num | awk 'BEGIN { FS = " *" } { print $1":"$2}')
echo $images
"""

script_docker_ps = \
"""
docker ps -a
"""

script_container_list = \
"""
image_num=$(($(docker ps -a | wc -l) - 1))
docker ps -a|tail -n$image_num|awk 'BEGIN { FS = " *" } { printf "%-20s %-20s %s\\n", $1, $NF, $2}'
"""


def select_image(cconfig:ContainerConfig) -> str:
    i = 1
    images = run_script(script_docker_images)[0]
    images_list = images.decode('utf8').rstrip('\n').split(' ')
    print(BColors.OKBLUE + 'Image List:' + BColors.ENDC)
    for image in images_list:
        print('%2d) %s' %(i, image))
        i += 1

    try:
        selected_num = int(input(
            BColors.OKBLUE +
            'Please choose an image from above list as container\'s image. [1 - %d]' % (i - 1)
            + BColors.ENDC))
    except ValueError:
        print(BColors.FAIL + 'Please select the number from 1 to %d' % (i - 1) + BColors.ENDC)
        return None
    return images_list[selected_num - 1]


def select_container(cconfig:ContainerConfig) -> str:
    result = run_script(script_container_list)
    i = 1
    if result[2] != 0:
        print(result[1].decode('utf8'))
        return False

    container_list = result[0].decode('utf8').rstrip('\n').split('\n')
    print("   %-20s %-20s %s" % ('CONTAINER ID', 'NAME', 'IMAGE'))
    for con in container_list:
        print('%d) %s' %(i, con))
        i += 1
    try:
        selected_num = int(input(
            BColors.OKBLUE +
            'Please choose a container from above list. [1 - %d]' % (i - 1)
            + BColors.ENDC))
    except ValueError:
        print(BColors.FAIL + 'Please select the number from 1 to %d' % (i - 1) + BColors.ENDC)
        return None
    return container_list[selected_num - 1].split()[0]


def docker_run(cconfig: ContainerConfig) -> bool:
    image=select_image(cconfig)
    if image == None:
        return False
    cmd = 'docker run' + cconfig.container.run_parameters + " %s " % image + cconfig.container.cmd
    result = run_script(cmd)
    if result[2] != 0:
        print(result[1].decode('utf8'))
        return False
    else:
        print(BColors.OKBLUE + 'Run container successfully. The following is container list:' + BColors.ENDC)
        print(run_script(script_docker_ps)[0].decode('utf8'))
        return True


def docker_kill(cconfig: ContainerConfig) -> bool:
    sel_container = select_container(cconfig)
    if sel_container == None:
        return False

    cmd = 'docker rm -f ' + sel_container
    result = run_script(cmd)
    if result[2] != 0:
        print(result[1].decode('utf8'))
        return False
    else:
        print(BColors.OKBLUE + 'Killed container successfully. The following is container list:' + BColors.ENDC)
        print("%-20s %-20s %s" % ('CONTAINER ID', 'NAME', 'IMAGE'))
        print(run_script(script_container_list)[0].decode('utf8'))
        return True


def pre_exec(cconfig: ContainerConfig) -> bool:
    host_os = HostOS.factory(cconfig)
    host_os.pre_exec(cconfig)


def post_exec(cconfig: ContainerConfig) -> bool:
    host_os = HostOS.factory(cconfig)
    host_os.post_exec(cconfig)


def docker_exec(cconfig: ContainerConfig) -> bool:
    sel_container = select_container(cconfig)
    if sel_container == None:
        return False

    pre_exec(cconfig)

    cmd = 'docker start ' + sel_container
    result = run_script(cmd)
    if result[2] != 0:
        print(result[1].decode('utf8'))
        return False

    bash_cmd = 'docker exec' + cconfig.container.exec_parameters + ' ' + sel_container + ' ' + cconfig.container.cmd
    gen_script_file(bash_cmd)

    post_exec(cconfig)

    return True


def docker_list(cconfig: ContainerConfig) -> bool:
    print(run_script(script_docker_ps)[0].decode('utf8'))


def build_parameters(cconfig: ContainerConfig):
    cconfig.container.run_parameters = \
        cconfig.container.name + ' ' + \
        cconfig.container.volume_list + ' ' + \
        cconfig.container.pseudo_tty  + ' ' + \
        cconfig.container.daemon + ' ' + \
        cconfig.container.keep_stdin + ' ' + \
        cconfig.container.privileged + ' ' + \
        cconfig.container.environment_list + ' ' + \
        cconfig.container.hostname
    # print(cconfig.container.run_parameters)

    cconfig.container.exec_parameters = \
        cconfig.container.pseudo_tty + ' ' + \
        cconfig.container.keep_stdin + ' ' + \
        cconfig.container.environment_list
    # print(cconfig.container.exec_parameters)

def main(argv=None):
    result = 0
    cconfig = ContainerConfig()

    parser = argparse.ArgumentParser(description='Description:\n'
                                                 '      Run Container with specific config\n'
                                                 'Example:\n'
                                                 '      %s ./configs/MAC_HOST.yml' % (os.path.basename(__file__)),
                                     formatter_class=argparse.RawTextHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--run', action='store_true',help='execute docker run')
    group.add_argument('-k', '--kill', action='store_true', help='execute docker kill')
    group.add_argument('-e', '--exec', action='store_true', help='execute docker exec')
    group.add_argument('-l', '--list', action='store_true', help='execute docker ps')
    parser.add_argument('config', metavar='CONFIG', type=open, help='The configuration file in configs directory')

    args = parser.parse_args()

    yaml = YAML()
    data = yaml.load(args.config)
    # print(data)

    for key in data['host']:
        # print('host:' + key)
        raw_value = data['host'][key]
        s = {
            'os': lambda: 'os',
            'network_intf': lambda: 'network_intf'
        }.get(key)()
        setattr(cconfig.host, s, raw_value)
        # print(getattr(cconfig.host, s))

    for key in data['container']:
        raw_value = data['container'][key]
        # print('container: %s:%s %s' % (key, type(value), value))
        s = {
            'name': lambda: {'attr':'name', 'param':'--name'},
            'volume-list': lambda: {'attr': 'volume_list', 'param': '-v'},
            'pseudo-tty': lambda: {'attr': 'pseudo_tty', 'param': '-t'},
            'daemon': lambda: {'attr': 'daemon', 'param': '-d'},
            'keep-stdin': lambda: {'attr': 'keep_stdin', 'param': '-i'},
            'privileged': lambda: {'attr': 'privileged', 'param': '--privileged'},
            'environment-list': lambda: {'attr': 'environment_list', 'param': '-e'},
            'hostname': lambda: {'attr': 'hostname', 'param': '-h'},
            'cmd': lambda: {'attr': 'cmd', 'param': ''}
        }.get(key, lambda : print('container:' + key + ' is not supported yet'))()
        if s == None:
            return 1

        if type(raw_value) is comments.CommentedSeq:
            for val in raw_value:
                fin_value = convert_val(cconfig, val)
                latest_value = getattr(cconfig.container, s['attr'])
                latest_value += " %s %s" % (s['param'], fin_value)
                setattr(cconfig.container, s['attr'], latest_value)
                # print(getattr(cconfig.container, s['attr']))

        else:
            fin_value = convert_val(cconfig, raw_value)
            latest_value = getattr(cconfig.container, s['attr'])
            if type(fin_value) is bool:
                latest_value += " %s" % s['param']
            else:
                latest_value += " %s %s" % (s['param'], fin_value)
            setattr(cconfig.container, s['attr'], latest_value)
            # print(getattr(cconfig.container, s['attr']))

    build_parameters(cconfig)

    if args.run is True:
        result = docker_run(cconfig)
    if args.kill is True:
        result = docker_kill(cconfig)
    if args.exec is True:
        result = docker_exec(cconfig)
    if args.list is True:
        result = docker_list(cconfig)

    return 1 if result == False else 0

# This file is invoked from the python interpreter
if __name__ == "__main__":
    sys.exit(main())