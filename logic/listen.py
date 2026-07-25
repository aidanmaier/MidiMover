import json
import socket
import websocket
from typing import Any, Callable
from zeroconf import ServiceListener, Zeroconf

class WebsocketServiceListener(ServiceListener):

    def __init__(self, sensors: list[str], on_disconnect: Callable) -> None:
        """
        Initiates zero-config Websockes connection with SensorStreamer and listens for streamed sensor data. 
        
        Parameters: 
        sensors (list of strings): list of Android sensor types to access, must contain two or more items.
        on_disconnect (callable function): cleanup function which passes disconnection cause back to the main thread.
        """
        super().__init__()

        # Handle sensors value
        if isinstance(sensors, list):
            if len(sensors) >= 2:
                self.sensors = sensors
            else:
                raise ValueError('two or more sensors must be specified')
        else:
            raise TypeError('sensors must be a list of strings')

        self.on_disconnect = on_disconnect

        self.open: bool = False # connection flag

        # Devices discovered via zeroconf, keyed by service name.
        # e.g. {'SensorStreamer._websocket._tcp.local.': {'address': '192.168.1.5', 'port': 8080}}
        self.discovered_services: dict[str, dict[str, Any]] = {}

        # Active websocket connection, if any
        self.ws_app: websocket.WebSocketApp | None = None
        self.connected_service_name: str | None = None

        # Data structure to hold the latest values for each sensor
        self.latest_values: dict[str, Any] = {
            'timestamp' : None,
            'sensors' : {
                sensor: [] for sensor in self.sensors
            }}

    def on_message(self, ws: Any, message: str) -> None:
        """
        Callback function which loads latest sensor data from API and stores it at self.latest_values.
        Messages are per individual sensor change, not batched.
        """

        # Load JSON from API
        try:
            msg = json.loads(message)
        except json.JSONDecodeError as exc:
            print(f'{self} could not decode message: {exc}')
            return
        
        # Extract data from JSON
        timestamp = msg.get('timestamp', None)
        sensor_str = msg.get('type', None)
        if isinstance(sensor_str, str):
            sensor_type = sensor_str.replace('android.sensor.', '')
        else:
            sensor_type = None
        values = msg.get('values', [])

        # Update latest values
        if timestamp:
            self.latest_values['timestamp'] = timestamp
        if sensor_type and values:
            self.latest_values['sensors'][sensor_type] = values

    def get_values(self) -> dict[str, Any]:
        """
        Listener function which returns the latest captured sensor values.
        """
        return self.latest_values

    def get_available_devices(self) -> list[str]:
        """
        Returns the names of all available devices.
        """
        return list(self.discovered_services.keys())

    def on_error(self, ws: Any, error: Exception) -> None:
        """
        Display error message.
        """
        print(f'{self} error: {error}')

    def on_close(self, ws: Any, close_code: int | None, reason: str) -> None:
        """
        Connection closed message.
        """
        self.latest_values = {
            'timestamp': None,
            'sensors': {sensor: [] for sensor in self.sensors},
        } # reset values before close

        print(f'{self} disconnected') # DEBUG

        self.open = False
        self.ws_app = None
        self.connected_service_name = None
        self.on_disconnect() # disconnect cleanup function

    def on_open(self, ws: Any) -> None:
        """
        Connection confirmation message.
        """
        print(f'{self} connected') # DEBUG
        self.open = True

    def connect(self, url: str) -> None:
        """
        Establishes an open-ended connection to the given socket. 
        Blocks until the connection is closed, so should be called from a background thread.
        """
        self.ws_app = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
        self.ws_app.run_forever()

    def connect_to_service(self, name: str) -> None:
        """
        Looks up a previously discovered device by its service name and connects to it.
        Blocks until the connection is closed, so should be called from a
        background thread.
        """
        service = self.discovered_services.get(name)
        if not service:
            raise ValueError(f'Unknown or unavailable service: {name}')

        self.connected_service_name = name
        sensor_str = ','.join(f'"android.sensor.{sensor}"' for sensor in self.sensors)
        url = f"ws://{service['address']}:{service['port']}/sensors/connect?types=[{sensor_str}]"
        self.connect(url)

    def disconnect(self) -> None:
        """ Closes any active connection. """
        if self.ws_app:
            self.ws_app.close()

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed") # DEBUG
        self.discovered_services.pop(name, None)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            print(f"\n  Service Added:") # DEBUG
            print(f"  Name: {name}")
            print(f"  Addresses: {addresses}")
            print(f"  Port: {info.port}\n")

            if len(addresses) != 0:
                # Record the device as available for the GUI to display, rather than
                # connecting immediately. Connection is now triggered explicitly via
                # connect_to_service() (e.g. from a "Connect" button).
                self.discovered_services[name] = {
                    'address': addresses[0],
                    'port': info.port,
                }