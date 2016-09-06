from st2actions.runners.pythonrunner import Action
from common.common import Connection

class VDXConfigureSTEdgeport(Action):

    def __init__(self, config=None, action_service=None):
        super(VDXConfigureSTEdgeport, self).__init__(config=config, action_service=action_service)
        self._connection = Connection(self.logger)

    def run(self, interface_type, interface, device_ip, username, password, protocol="http", port=80):
        self._connection.setup(device_ip, username, password, protocol, port)

        url = self._connection.get_config_url("running/interface/{}/%22{}%22/spanning-tree/edgeport".format(interface_type, interface))
        r = self._connection.perform_put(url)
        if r:
            url = self._connection.get_config_url("running/interface/{}/%22{}%22/spanning-tree/edgeport/bpdu-guard".format(interface_type, interface))
            return self._connection.perform_put(url)
        return False
