import json
import socket
import websocket
from typing import Any
from zeroconf import ServiceListener, Zeroconf

class WebsocketServiceListener(ServiceListener):

    def __init__(self, sensors: list[str]) -> None:
        """
        Initiates zero-config Websockes connection with SensorStreamer and listens for streamed sensor data. 
        
        Parameters: 
        sensors (list of strings): list of Android sensor types to access, must contain two or more items.
        """
        super().__init__()

        # Handle sensors value
        if isinstance(sensors, list):
            if len(sensors) >= 2:
                self.sensors = sensors
            else:
                ValueError('two or more sensors must be specified')
        else:
            TypeError('sensors must be a list of strings')

        self.open: bool = False # connection flag

        # Data structure to hold the latest values for each sensor
        self.latest_values: dict[str, Any] = {
            'timestamp' : None,
            'sensors' : {
                sensor: [] for sensor in self.sensors
            }}

    def on_message(self, ws: Any, message: str) -> None:
        """
        Callback function which loads JSON of latest sensor data and stores it at self.latest_values.
        Messages are 1 per sensor change, not batched.
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

    def on_error(self, ws: Any, error: Exception) -> None:
        """
        Display error message.
        """
        print(f'{self} error: {error}')

    def on_close(self, ws: Any, close_code: int | None, reason: str) -> None:
        """
        Connection closed message.
        """
        self.latest_values = {} # reset values before close
        print(f'{self} disconnected')
        self.open = False

    def on_open(self, ws: Any) -> None:
        """
        Connection confirmation message.
        """
        print(f'{self} connected')
        self.open = True

    def connect(self, url: str) -> None:
        """
        Established open-ended connection to the given socket.
        """
        ws = websocket.WebSocketApp(
                url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
        ws.run_forever()

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            print(f"  Service Added:")
            print(f"  Name: {name}")
            print(f"  Addresses: {addresses}")
            print(f"  Port: {info.port}\n")

            if len(addresses) != 0:
                address = addresses[0]
                portNo = info.port
                print("connecting...\n")
                sensor_str = ','.join([f'"android.sensor.{sensor}"' for sensor in self.sensors])
                self.connect(f'ws://{address}:{portNo}/sensors/connect?types=[{sensor_str}]')
