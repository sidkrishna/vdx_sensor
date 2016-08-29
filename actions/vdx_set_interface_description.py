from st2actions.runners.pythonrunner import Action
from common.common import Connection
from dicttoxml import dicttoxml
import xmltodict

class VDXSetInterfaceDescription(Action):

    def __init__(self, config=None, action_service=None):
        super(VDXSetInterfaceDescription, self).__init__(config=config, action_service=action_service)
        self._connection = Connection(self.logger)

    def run(self, interface_type, interface, description, device_ip, username, password, protocol="http", port=80):
        self._connection.setup(device_ip, username, password, protocol, port)

        url = self._connection.get_config_url("running/interface/{}/%22{}%22/description".format(interface_type, interface))
        payload = {'description': description.replace(' ','_')}
        r = self._connection.perform_put(url, dicttoxml(payload, root=False, attr_type=False))
        if r:
            return True
        return False
