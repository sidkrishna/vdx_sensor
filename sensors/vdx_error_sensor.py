from vdx_base_sensor import VDXBaseSensor
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

         prev_error_metrics = self._get_metrics()
         if prev_error_metrics is None:
            self._logger.info("############ prev_metrics is None #################")
            prev_error_metrics = {}

         error_metrics = {}

         for interface_name, interface_stats in interfaces.iteritems():
             interface_exists_in_prev = 0

             if interface_name in prev_error_metrics:
                 interface_exists_in_prev = 1

             if interface_exists_in_prev:
                 latest_tx_errors = int(interface_stats['out_errors']) - int(prev_error_metrics[interface_name]['out_errors'])
                 latest_rx_errors = int(interface_stats['in_errors']) - int(prev_error_metrics[interface_name]['in_errors'])

                 if latest_tx_errors > int(self._config['sensor_error']['out_errors']) \
                 or latest_rx_errors > int(self._config['sensor_error']['in_errors']):
                     self._dispatch_trigger(interface_stats['interface_type'], interface_name, latest_tx_errors, latest_rx_errors, self._config['sensor_error']['poll_interval'])

             error_metrics[interface_name] = {}
             error_metrics[interface_name]['out_errors'] = interface_stats['out_errors']
             error_metrics[interface_name]['in_errors'] = interface_stats['in_errors']

         self._set_metrics(error_metrics)

    def _set_metrics(self, metrics):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='metrics', value=metrics)

    def _get_metrics(self):
        if hasattr(self._sensor_service, 'get_value'):
            metrics = self._sensor_service.get_value(name='metrics')
            if metrics:
                return ast.literal_eval(metrics)

    def _dispatch_trigger(self, interface_type, interface_name, tx_errors, rx_errors, poll_interval):
        trigger = self._trigger_ref
        payload = {
            'interface_type': interface_type,
            'interface_name': interface_name,
            'tx_errors': tx_errors,
            'rx_errors': rx_errors,
            'poll_interval': poll_interval 
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
