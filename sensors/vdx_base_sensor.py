from st2reactor.sensor.base import PollingSensor
from common.common import Connection
import xmltodict
from distutils.util import strtobool
from dicttoxml import dicttoxml
import ast

class VDXBaseSensor(PollingSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        super(VDXBaseSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._base_config = self._config['base_config']
        self._logger = self._sensor_service.get_logger(__name__)
        self.setup()

    def setup(self):
        self._connection = Connection(self._logger)
        self._connection.setup(self._base_config['device_ip'],
                                self._base_config['username'],
                                self._base_config['password'])

    def poll(self):
        data = self._poll_device()

        interfaces = {}
        for interface in data:
            if 'hardware-type' in interface:
                if interface['if-state'] == 'up' and interface['line-protocol-state'] == 'up':
                    interfaces[interface['interface-name']] = \
                    { 'in_octets': interface['ifHCInOctets'],
                    'out_octets': interface['ifHCOutOctets'],
                    'in_unicast': interface['ifHCInUcastPkts'],
                    'out_unicast': interface['ifHCOutUcastPkts'],
                    'in_multicast': interface['ifHCInMulticastPkts'],
                    'out_multicast': interface['ifHCOutMulticastPkts'],
                    'in_broadcast': interface['ifHCInBroadcastPkts'],
                    'out_broadcast': interface['ifHCOutBroadcastPkts'],
                    'in_errors': interface['ifHCInErrors'],
                    'out_errors': interface['ifHCOutErrors']}
        self._logger.debug("Interfaces are: %s" %(interfaces))
        return interfaces

    def cleanup(self):
        pass

    def add_trigger(self, trigger):
        pass

    def update_trigger(self, trigger):
        pass

    def remove_trigger(self, trigger):
        pass

    def _poll_device(self):
        interfaces = []

        def _do_poll(parent, payload={}):
            _url = self._connection.get_operational_url('get-interface-detail')
            _r = self._connection.perform_post(_url, payload)

            content = xmltodict.parse(_r.content)

            parent._logger.debug("Content is: %s" %(content))

            if 'interface' in content['output']:
                interfaces.extend(content['output']['interface'])

            _has_more = strtobool(content['output']['has-more'])
            if _has_more:
                last_interface = content['output']['interface'][-1]
                payload = {
                    'get-interface-detail': {
                        'last-rcvd-interface': {
                            'interface-type': last_interface['interface-type'],
                            'interface-name': last_interface['interface-name']
                        }
                    }
                }
                _do_poll(parent, dicttoxml(payload, root=False, attr_type=False))

        _do_poll(self)
        return interfaces

    def _dispatch_trigger(self, interface_name, interface_stats):
        trigger = self._trigger_ref
        payload = {
            'interface_name': interface_name,
            'interface_stats': interface_stats
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
