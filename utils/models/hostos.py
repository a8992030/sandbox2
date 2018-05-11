from abc import abstractmethod


class HostOS(object):
    @staticmethod
    def factory(cconfig):
        if cconfig.host.os == 'MACOS':
            from .macos import MacOS
            return MacOS()
        assert 0, "Bad HostOS creation: " + cconfig.host.os

    @abstractmethod
    def pre_exec(self, cconfig) -> bool:
        pass

    @abstractmethod
    def post_exec(self, cconfig) -> bool:
        pass
