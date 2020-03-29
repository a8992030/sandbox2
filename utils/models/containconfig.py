class ContainerConfig:
    def __init__(self):
        self.host = self.Host()
        self.container = self.Container()

    class Host:
        os = ''
        network_intf= ''

    class Container:
        name = ''
        port_list = ''
        volume_list = ''
        pseudo_tty = ''
        daemon = ''
        keep_stdin = ''
        privileged = ''
        environment_list = ''
        hostname = ''
        run_parameters = ''
        exec_parameters = ''
        cmd = ''
