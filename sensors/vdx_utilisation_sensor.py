from vdx_base_sensor import VDXBaseSensor
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
        self._set_polls()

        interfaces = {}
        for interface in data:
            if 'hardware-type' in interface:
                if interface['if-state'] == 'up' and interface['line-protocol-state'] == 'up':
                    interfaces[interface['interface-name']] = \
                    {
                     'tx_octets': interface['ifHCOutOctets'],
                     'rx_octets': interface['ifHCInOctets']
                     }
        self._logger.debug("Interfaces are: %s" %(interfaces))
        average_metrics = self._calc_average_metrics(interfaces)

        self._set_metrics(average_metrics)
        self._check_threshold(average_metrics)

    def octet_to_megabytes_per_second(self, previous_octet, new_octet):
        return ((int(new_octet) - int(previous_octet))/self._poll_interval)/(1000^2)

    def _calc_average_metrics(self, interfaces):
        prev_metrics = self._get_metrics()
        if prev_metrics is None:
            prev_metrics = {}

        avg_metrics = {}
        def _do_average_calc(previous_average, polls, latest):
            return (int(previous_average) * int(polls) + int(latest)) / (int(polls) + 1)

        for interface_name, interface_stats in interfaces.iteritems():
            avg_metrics[interface_name] = {}
            avg_metrics[interface_name]['tx_avg_octets'] = _do_average_calc(prev_metrics.get('tx_octets',0), self._get_polls(), interface_stats['tx_octets'])
            avg_metrics[interface_name]['tx_MBps'] = self.octet_to_megabytes_per_second(prev_metrics.get('tx_avg_octets', 0), avg_metrics[interface_name]['tx_avg_octets'])
            avg_metrics[interface_name]['rx_avg_octets'] = _do_average_calc(prev_metrics.get('rx_octets',0), self._get_polls(), interface_stats['rx_octets'])
            avg_metrics[interface_name]['rx_MBps'] = self.octet_to_megabytes_per_second(prev_metrics.get('rx_avg_octets', 0), avg_metrics[interface_name]['rx_avg_octets'])
        return avg_metrics

    def _set_metrics(self, metrics):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='metrics', value=metrics)

    def _get_metrics(self):
        if hasattr(self._sensor_service, 'get_value'):
            metrics = self._sensor_service.get_value(name='metrics')
            if metrics:
                return ast.literal_eval(metrics)

    def _set_polls(self):
        polls = self._get_polls()
        if polls is None:
            polls = 1
        else:
            polls = int(polls) + 1
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='polls', value=polls)

    def _get_polls(self):
        if hasattr(self._sensor_service, 'get_value'):
            polls = self._sensor_service.get_value(name='polls')
            if polls:
                return int(polls)

    def _check_threshold(self, metrics):
        for interface_name, interface_stats in metrics.iteritems():
            if int(interface_stats['tx_MBps']) > int(self._config['sensor_utilisation']['tx_threshold']) \
            or int(interface_stats['rx_MBps']) > int(self._config['sensor_utilisation']['rx_threshold']):
                self._dispatch_trigger(interface_name,
                    interface_stats['tx_MBps'],
                    self._config['sensor_utilisation']['tx_threshold'],
                    interface_stats['rx_MBps'],
                    self._config['sensor_utilisation']['rx_threshold'])

    def _dispatch_trigger(self, interface_name, tx, tx_threshold, rx, rx_threshold):
        trigger = self._trigger_ref
        payload = {
            'interface_name': interface_name,
            'tx_MBps': tx,
            'tx_threshold': tx_threshold,
            'rx_MBps': rx,
            'rx_threshold': rx_threshold
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
