from st2actions.runners.pythonrunner import Action
from common.common import Connection
from dicttoxml import dicttoxml

class VDXCreateVlanAction(Action):

    def __init__(self, config=None, action_service=None):
        super(VDXCreateVlanAction, self).__init__(config=config, action_service=action_service)
        self._connection = Connection(self.logger)

    def run(self, vlan, device_ip, username, password, protocol="http", port=80):
        self._connection.setup(device_ip, username, password, protocol, port)
        url = self._connection.get_config_url("running/interface/Vlan/%s" %(vlan))
        r = self._connection.perform_get(url)
        if r:
            self.logger.info("VLAN %s already exists", vlan)
            return False
        else:
            url = self._connection.get_config_url("running/interface")
            payload = {
                'Vlan': {
                    'name': vlan
                }
            }
            r = self._connection.perform_post(url, dicttoxml(payload, root=False, attr_type=False))
            if r:
                self.logger.info("VLAN %s added", vlan)
            return r
