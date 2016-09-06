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

        def calc_average(previous_average, polls, latest):
            return (int(previous_average) * int(polls) + int(latest)) / (int(polls) + 1)

        data = self._poll_device()

        interfaces = {}
        for interface in data:
            if 'hardware-type' in interface:
                if interface['if-state'] == 'up' and interface['line-protocol-state'] == 'up':
                    interfaces[interface['interface-name']] = \
                    {
                     'tx_octets': interface['ifHCOutOctets'],
                     'rx_octets': interface['ifHCInOctets']
                    }
        self._logger.info("Interfaces are: %s" %(interfaces))
        

        prev_metrics = self._get_metrics()
        if prev_metrics is None:
            self._logger.info("prev_metrics is None")
            prev_metrics = {}

        avg_metrics = {}
        self._set_polls()

        for interface_name, interface_stats in interfaces.iteritems():
            interface_exists_in_prev = 0

            if interface_name in prev_metrics:
                interface_exists_in_prev = 1
                self._logger.info("Interface %s exists in prev" %(interface_name))
            else:
                self._logger.info("Interface %s does not exist in prev" %(interface_name))

            if interface_exists_in_prev:
                latest_tx_MBps = ((int(interface_stats['tx_octets']) - int(prev_metrics[interface_name]['tx_last_octets']))/self._poll_interval)/(1000**2)
                self._logger.info("current tx octets %d" %(int(interface_stats['tx_octets'])))
                self._logger.info("prev tx octets %d" %(int(prev_metrics[interface_name]['tx_last_octets'])))
                self._logger.info("latest_tx_MBps: %d" %(latest_tx_MBps))
            else:
                latest_tx_MBps = 0
                self._logger.info("Setting latest_tx_MBps to 0")

            if interface_exists_in_prev: 
                latest_rx_MBps = ((int(interface_stats['rx_octets']) - int(prev_metrics[interface_name]['rx_last_octets']))/self._poll_interval)/(1000**2)
            else:
                latest_rx_MBps = 0 

            if interface_exists_in_prev:
                if latest_tx_MBps > float((1 + (float(self._config['sensor_utilisation']['tx_threshold'])/100)))*(int(prev_metrics[interface_name]['tx_avg_MBps'])) \
                or latest_rx_MBps > float((1 + (float(self._config['sensor_utilisation']['rx_threshold'])/100)))*(int(prev_metrics[interface_name]['rx_avg_MBps'])) \
                or latest_tx_MBps < float((1 - (float(self._config['sensor_utilisation']['tx_threshold'])/100)))*(int(prev_metrics[interface_name]['tx_avg_MBps'])) \
                or latest_rx_MBps < float((1 - (float(self._config['sensor_utilisation']['rx_threshold'])/100)))*(int(prev_metrics[interface_name]['rx_avg_MBps'])): 
                    self._logger.info("Threshold check detected!!")
                    self._logger.info("latest_tx_MBps: %d" %(latest_tx_MBps))
                    self._logger.info("prev tx_avg_MBps: %d" %(int(prev_metrics[interface_name]['tx_avg_MBps'])))
                    self._dispatch_trigger(interface_name,
                        latest_tx_MBps,
                        self._config['sensor_utilisation']['tx_threshold'],
                        latest_rx_MBps,
                        self._config['sensor_utilisation']['rx_threshold'])

            avg_metrics[interface_name] = {}
            avg_metrics[interface_name]['tx_last_octets'] = interface_stats['tx_octets']
            if interface_exists_in_prev:
                avg_metrics[interface_name]['tx_avg_MBps'] = calc_average(prev_metrics[interface_name]['tx_avg_MBps'], self._get_polls()-2, latest_tx_MBps)
            else:
                avg_metrics[interface_name]['tx_avg_MBps'] = latest_tx_MBps 
            avg_metrics[interface_name]['rx_last_octets'] = interface_stats['rx_octets']
            if interface_exists_in_prev: 
                avg_metrics[interface_name]['rx_avg_MBps'] = calc_average(prev_metrics[interface_name]['rx_avg_MBps'], self._get_polls()-2, latest_rx_MBps) 
            else:
                avg_metrics[interface_name]['rx_avg_MBps'] = latest_rx_MBps

        self._set_metrics(avg_metrics)

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
