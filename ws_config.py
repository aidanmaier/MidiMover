from typing import Any
from zeroconf import ServiceListener, Zeroconf
import websocket
import json
import socket

class MyServiceListener(ServiceListener):

    def __init__(self, sensor: str) -> None:
        super().__init__()
        self.sensor = sensor
        self.latest_values: tuple[float, float, float] | None = None

    def on_message(self, ws: Any, message: str) -> None:
        """Callback function."""
        values = json.loads(message)['values']
        x, y, z = values[0], values[1], values[2]
        self.latest_values = (x, y, z)

    def get_values(self) -> tuple[float, float, float] | None:
        """ Listener function. """
        return self.latest_values

    def on_error(self, ws: Any, error: Exception) -> None:
        print(f'{self.sensor} error: {error}')

    def on_close(self, ws: Any, close_code: int | None, reason: str) -> None:
        self.latest_values = None # reset values before close
        print(f'{self.sensor} connection closed (reason: {reason})')

    def on_open(self, ws: Any) -> None:
        print(f'{self.sensor} connected')

    def connect(self, url: str) -> None:
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
