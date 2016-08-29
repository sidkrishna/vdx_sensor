from st2actions.runners.pythonrunner import Action
from common.common import Connection
from dicttoxml import dicttoxml
import xmltodict

class VDXTagVlanAction(Action):

    def __init__(self, config=None, action_service=None):
        super(VDXCreateVlanAction, self).__init__(config=config, action_service=action_service)
        self._connection = Connection(self.logger)

    def run(self, interface_type, interface, mode, vlan, device_ip, username, password, protocol="http", port=80):
        self._connection.setup(device_ip, username, password, protocol, port)

        if mode == 'trunk':
            url = self._connection.get_config_url("running/interface/{}/{}/switchport/trunk/allowed/vlan/add".format(interface_type, interface))
            payload = {'add': vlan}
        elif mode == 'access':
            url = self._connection.get_config_url("running/interface/{}/{}/switchport/access/vlan".format(interface_type, interface))
            payload = {'vlan': vlan}
        else:
            self.logger.error("Supplied VLAN mode %s is neither 'trunk' or 'access'", mode)
            return False
        r = self._connection.perform_put(url, dicttoxml(payload, root=False, attr_type=False))
        if r:
            content = xmltodict.parse(r.content)
            self.logger.info("VLAN %s added", vlan)
            return r
        return False
