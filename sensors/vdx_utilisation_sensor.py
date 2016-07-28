from vdx_base_sensor import VDXBaseSensor
import requests
import xmltodict
from distutils.util import strtobool
from dicttoxml import dicttoxml
import ast

__all__ = [
    'VDXUtilisationSensor'
]

class VDXUtilisationSensor(VDXBaseSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        poll_interval = config['sensor_utilisation'].get('poll_interval', 30)
        super(VDXUtilisationSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._trigger_ref = 'vdx_sensor.matched_utilisation_threshold'
        self._logger = self._sensor_service.get_logger(__name__)

    def poll(self):
        self._logger.info("Utilisation Sensor Polling")
        interfaces = super(VDXUtilisationSensor, self).poll()
        self._check_threshold(interfaces)

    def _check_threshold(self, interfaces):
        for interface_name, interface_stats in interfaces.iteritems():
            for metric, metric_value in self._config['sensor_utilisation']['metric_thresholds'].iteritems():
                if int(interface_stats[metric]) > int(metric_value):
                    self._dispatch_trigger(interface_name, interfaces[interface_name], metric, metric_value)

    def _dispatch_trigger(self, interface_name, interface_stats, metric, metric_value):
        trigger = self._trigger_ref
        payload = {
            'interface_name': interface_name,
            'interface_stats': interface_stats,
            'metric': metric,
            'metric_value': metric_value
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
