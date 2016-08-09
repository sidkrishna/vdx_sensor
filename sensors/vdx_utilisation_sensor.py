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
        average_metrics = self._calc_average_metrics(interfaces)
        self._set_metrics(average_metrics)
        self._check_threshold(average_metrics)

    def _calc_average_metrics(self, interfaces):
        prev_metrics = self._get_metrics()
        if prev_metrics is None:
            return interfaces
        avg_metrics = {}
        for interface_name, interface_stats in interfaces.iteritems():
            avg_metrics[interface_name] = {}
            for metric, metric_value in prev_metrics[interface_name].iteritems():
                avg_metrics[interface_name][metric] = (int(interface_stats[metric]) + int(metric_value)) / 2
        return avg_metrics

    def _set_metrics(self, metrics):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='metrics', value=metrics)

    def _get_metrics(self):
        if hasattr(self._sensor_service, 'get_value'):
            metrics = self._sensor_service.get_value(name='metrics')
            if metrics:
                return ast.literal_eval(metrics)

    def _check_threshold(self, metrics):
        for interface_name, interface_stats in metrics.iteritems():
            for metric, metric_value in self._config['sensor_utilisation']['metric_thresholds'].iteritems():
                if int(interface_stats[metric]) > int(metric_value):
                    self._dispatch_trigger(interface_name, metrics[interface_name], metric, metric_value)

    def _dispatch_trigger(self, interface_name, interface_stats, metric, metric_value):
        trigger = self._trigger_ref
        payload = {
            'interface_name': interface_name,
            'interface_stats': interface_stats,
            'metric': metric,
            'metric_value': metric_value
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
