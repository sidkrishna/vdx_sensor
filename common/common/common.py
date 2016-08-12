import requests

class Connection(object):

    def __init__(self, logger):
        self._logger = logger
        self._device_ip = None
        self._username = None
        self._password = None
        self._protocol = "http"
        self._port = 80
        self._session = None

    def setup(self, device_ip, username, password, protocol="http", port=80):
        self._device_ip = device_ip
        self._username = username
        self._password = password
        self._protocol = protocol
        self._port = port
        self._session = self.setup_session()

    def setup_session(self):
        s = requests.Session()
        s.auth = (self._username, self._password)
        s.headers.update({"Accept": "application/vnd.configuration.resource+xml"})
        return s

    def get_base_url(self):
        return "%s://%s:%s/rest" %(self._protocol, self._device_ip, self._port)

    def get_config_url(self, resource, *args):
        return self.get_base_url()+"/config/"+resource.format(*args)

    def get_operational_url(self, resource, *args):
        return self.get_base_url()+"/operational-state/"+resource.format(*args)

    def perform_put(self, uri, payload):
        try:
            self._logger.debug('HTTP PUT on %s', uri)
            self._logger.debug('HTTP PUT Payload: %s', payload)
            r = self._session.put(uri, data=payload, timeout=30)
            self._logger.debug('HTTP Status Code: %s', r.status_code)

            if(r.status_code < 200 or r.status_code >= 300):
                self._logger.info('Content: %s', r.content)
                return False
            return True
        except requests.exceptions.RequestException as e:
            self._logger.error('HTTP PUT unexpected error')
            self._logger.error(e)
            return False

    def perform_post(self, uri, payload):
        try:
            self._logger.debug('HTTP POST on %s', uri)
            self._logger.debug('HTTP POST Payload: %s', payload)
            r = self._session.post(uri, data=payload, timeout=30)
            self._logger.debug('HTTP Status Code: %s', r.status_code)

            if(r.status_code < 200 or r.status_code >= 300):
                self._logger.info('Content: %s', r.content)
                return False
            return True
        except requests.exceptions.RequestException as e:
          self._logger.error('HTTP POST unexpected error')
          self._logger.error(e)
          return False

    def perform_delete(self, uri):
        try:
            self._logger.debug('HTTP DELETE on %s', uri)
            r = self._session.delete(uri, data=None, timeout=30)
            self._logger.debug('HTTP Status Code: %s', r.status_code)

            if(r.status_code < 200 or r.status_code >= 300):
                self._logger.info('Content: %s', r.content)
                return False
            return True
        except requests.exceptions.RequestException as e:
            self._logger.error('HTTP DELETE unexpected error')
            self._logger.error(e)
            return False

    def perform_get(self, uri):
        try:
            self._logger.debug('HTTP GET on %s', uri)
            r = self._session.get(uri, timeout=30)
            self._logger.debug('HTTP Status Code: %s', r.status_code)

            if(r.status_code < 200 or r.status_code >= 300):
                self._logger.info('Content: %s', r.content)
                return False
            return r
        except requests.exceptions.RequestException as e:
            self._logger.error('HTTP GET unexpected error')
            self._logger.error(e)
            return False
