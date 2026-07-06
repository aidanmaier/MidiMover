from typing import Any
from zeroconf import ServiceListener, Zeroconf
import websocket
import json
import socket

class WebsocketServiceListener(ServiceListener):

    def __init__(self, sensor: str) -> None:
        """
        
        """
        super().__init__()
        self.sensor = sensor
        self.latest_values: Any = None

    def on_message(self, ws: Any, message: str) -> None:
        """
        Callback function which loads JSON of latest sensor values and timestamp, 
        and stores them at self.latest_values.
        """
        self.latest_values = json.loads(message)

    def get_values(self) -> Any:
        """ 
        Listener function which returns latest captured sensor value and timestamp
        from JSON stoed in self.latest_values.
        """
        return self.latest_values

    def on_error(self, ws: Any, error: Exception) -> None:
        """
        Error message for debugging.
        """
        print(f'{self.sensor} error: {error}')

    def on_close(self, ws: Any, close_code: int | None, reason: str) -> None:
        """
        Connection closed message.
        """
        self.latest_values = None # reset values before close
        print(f'{self.sensor} connection closed (reason: {reason})')

    def on_open(self, ws: Any) -> None:
        """
        Connection confirmation message.
        """
        print(f'{self.sensor} connected')

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
                self.connect(f"ws://{address}:{portNo}/sensor/connect?type=android.sensor.{self.sensor}")
