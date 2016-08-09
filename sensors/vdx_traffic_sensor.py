from vdx_base_sensor import VDXBaseSensor
import requests
import xmltodict
from distutils.util import strtobool
from dicttoxml import dicttoxml
import ast

__all__ = [
    'VDXTrafficSensor'
]

class VDXTrafficSensor(VDXBaseSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        poll_interval = config['sensor_traffic'].get('poll_interval', 30)
        super(VDXTrafficSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._trigger_ref = 'vdx_sensor.matched_no_traffic'
        self._logger = self._sensor_service.get_logger(__name__)

    def poll(self):
        self._logger.info("Traffic Sensor Polling")
        interfaces = super(VDXTrafficSensor, self).poll()
        prev_interfaces = self._get_interfaces()
        self._set_interfaces(interfaces)
        self._do_delta(prev_interfaces, interfaces)

    def _set_interfaces(self, interfaces):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='vdx_traffic_sensor', value=interfaces)

    def _get_interfaces(self):
        if hasattr(self._sensor_service, 'get_value'):
            interfaces = self._sensor_service.get_value(name='vdx_traffic_sensor')
            if interfaces:
                return ast.literal_eval(interfaces)

    def _do_delta(self, prev_interfaces, interfaces):
        self._logger.debug("Previous Interfaces are: %s" %(prev_interfaces))
        self._logger.debug("Current Interfaces are: %s" %(interfaces))
        for interface_name, interface_stats in interfaces.iteritems():
            if interface_name in prev_interfaces:
                if interface_stats['in_unicast'] == prev_interfaces[interface_name]['in_unicast']:
                    self._dispatch_trigger(interface_name, interfaces[interface_name])
