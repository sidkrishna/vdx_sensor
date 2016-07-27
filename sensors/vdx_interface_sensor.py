from st2reactor.sensor.base import PollingSensor
import requests
import xmltodict
from distutils.util import strtobool
import ast

__all__ = [
    'VDXInterfaceSensor'
]

class VDXInterfaceSensor(PollingSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        super(VDXInterfaceSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._trigger_ref = 'vdx_sensor.matched_no_traffic'
        self._logger = self._sensor_service.get_logger(__name__)

    def setup(self):
        self._session = self._setup_session(self._config['username'], self._config['password'])
        self._base_url = self._config['base_url']

    def poll(self):
        try:
            _url = self._base_url + "/operational-state/get-interface-detail"
            _r = self._session.post(_url, data={}, timeout=30)
        except requests.exceptions.RequestException as e:
            self._logger.exception('HTTP POST unexpected error')
            raise e

        data = xmltodict.parse(_r.content)
        _has_more = strtobool(data['output']['has-more'])
        if _has_more:
            # TODO: Repeat call and add to data variable
            pass
        else:
            interfaces = {}
            for interface in data['output']['interface']:
                if 'hardware-type' in interface:
                    if interface['if-state'] == 'up' and interface['line-protocol-state'] == 'up':
                        interfaces[interface['interface-name']] = {'in': interface['ifHCInOctets'], 'out': interface['ifHCOutOctets']}
            self._logger.info("Interfaces are: %s" %(interfaces))
            prev_interfaces = self._get_interfaces()
            self._set_interfaces(interfaces)
            self._do_delta(prev_interfaces, interfaces)

    def cleanup(self):
        pass

    def add_trigger(self, trigger):
        pass

    def update_trigger(self, trigger):
        pass

    def remove_trigger(self, trigger):
        pass

    def _setup_session(self, username, password):
        s = requests.Session()
        s.auth = (username, password)
        s.headers.update({"Accept": "application/vnd.configuration.resource+xml"})
        return s

    def _set_interfaces(self, interfaces):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='vdx_sensor_interfaces', value=interfaces)

    def _get_interfaces(self):
        if hasattr(self._sensor_service, 'get_value'):
            interfaces = self._sensor_service.get_value(name='vdx_sensor_interfaces')
            if interfaces:
                return ast.literal_eval(interfaces)

    def _do_delta(self, prev_interfaces, interfaces):
        self._logger.info("Previous Interfaces are: %s" %(prev_interfaces))
        self._logger.info("Current Interfaces are: %s" %(interfaces))
        for interface_name, interface_stats in interfaces.iteritems():
            if interface_name in prev_interfaces:
                if interface_stats['in'] == prev_interfaces[interface_name]['in']:
                    self._dispatch_trigger(interface_name, interfaces[interface_name])


    def _dispatch_trigger(self, interface_name, interface_stats):
        trigger = self._trigger_ref
        payload = {
            'interface_name': interface_name,
            'interface_stats': interface_stats
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
