from vdx_base_sensor import VDXBaseSensor
import requests
import xmltodict
from distutils.util import strtobool
from dicttoxml import dicttoxml
import ast

__all__ = [
    'VDXErrorSensor'
]

class VDXErrorSensor(VDXBaseSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        poll_interval = config['sensor_error'].get('poll_interval', 30)
        super(VDXErrorSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._trigger_ref = 'vdx_sensor.matched_error_threshold'
        self._logger = self._sensor_service.get_logger(__name__)

    def poll(self):
        self._logger.info("Error Sensor Polling")
        interfaces = super(VDXErrorSensor, self).poll()
        self._check_threshold(interfaces)

    def _check_threshold(self, interfaces):
        for interface_name, interface_stats in interfaces.iteritems():
            if int(interface_stats['in_errors']) > int(self._config['sensor_error']['in_errors']) or \
            int(interface_stats['out_errors']) > int(self._config['sensor_error']['out_errors']):
                self._dispatch_trigger(interface_name, interfaces[interface_name])
