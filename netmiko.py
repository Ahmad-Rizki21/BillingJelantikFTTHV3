"""
Dummy netmiko module for compatibility when netmiko is not available
This provides mock classes to prevent import errors
"""

class ConnectHandler:
    """Mock ConnectHandler for when netmiko is not available"""

    def __init__(self, **kwargs):
        self.device_type = kwargs.get('device_type', 'cisco_ios')
        self.host = kwargs.get('host', '')
        self.username = kwargs.get('username', '')
        self.password = kwargs.get('password', '')
        self.port = kwargs.get('port', 22)
        self.connected = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        """Mock connect method"""
        self.connected = True
        return True

    def disconnect(self):
        """Mock disconnect method"""
        self.connected = False

    def send_command(self, command_string, **kwargs):
        """Mock send_command method"""
        if not self.connected:
            raise ConnectionError("Not connected to device")
        return f"Mock output for: {command_string}"

class NetmikoAuthenticationException(Exception):
    """Mock exception"""
    pass

class NetmikoTimeoutException(Exception):
    """Mock exception"""
    pass