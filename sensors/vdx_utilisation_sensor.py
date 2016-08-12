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

        data = self._poll_device()

        interfaces = {}
        for interface in data:
            if 'hardware-type' in interface:
                if interface['if-state'] == 'up' and interface['line-protocol-state'] == 'up':
                    interfaces[interface['interface-name']] = \
                    {'tx': interface['ifHCOutOctets'],
                     'rx': interface['ifHCInOctets']}
        self._logger.debug("Interfaces are: %s" %(interfaces))

        average_metrics = self._calc_average_metrics(interfaces)
        self._set_metrics(average_metrics)
        self._check_threshold(average_metrics)

    def _calc_average_metrics(self, interfaces):
        prev_metrics = self._get_metrics()
        if prev_metrics is None:
            # 0 out tx/rx first time round
            return {key: {key_: 0 for key_, val_ in val.iteritems()} for key, val in interfaces.iteritems()}
        avg_metrics = {}
        for interface_name, interface_stats in interfaces.iteritems():
            avg_metrics[interface_name] = {}
            avg_metrics[interface_name]['tx'] = ((int(interface_stats['tx']) - int(prev_metrics[interface_name]['tx']))/self._poll_interval)/(1000^2)
            avg_metrics[interface_name]['rx'] = ((int(interface_stats['rx']) - int(prev_metrics[interface_name]['rx']))/self._poll_interval)/(1000^2)
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
            if int(interface_stats['tx']) > int(self._config['sensor_utilisation']['tx_threshold']) \
            or int(interface_stats['rx']) > int(self._config['sensor_utilisation']['rx_threshold']):
                self._dispatch_trigger(interface_name,
                    interface_stats['tx'],
                    self._config['sensor_utilisation']['tx_threshold'],
                    interface_stats['rx'],
                    self._config['sensor_utilisation']['rx_threshold'])

    def _dispatch_trigger(self, interface_name, tx, tx_threshold, rx, rx_threshold):
        trigger = self._trigger_ref
        payload = {
            'interface_name': interface_name,
            'tx': tx,
            'tx_threshold': tx_threshold,
            'rx': rx,
            'rx_threshold': rx_threshold
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
