from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import websocket
import json
import socket

class MyServiceListener(ServiceListener):

    def __init__(self, sensor: str) -> None:
        super().__init__()
        self.sensor = sensor

    def on_message(self, ws, message):
        values = json.loads(message)['values']
        x, y, z = values[0], values[1], values[2]
        ts = json.loads(message)['timestamp']

        print(ts, "x = ", x , "y = ", y , "z = ", z)

    def on_error(self, ws, error):
        print("error occurred ", error)
        
    def on_close(self, ws, close_code, reason):
        print("connection closed : ", reason)
        
    def on_open(self, ws):
        print("connected")
        

    def connect(self, url):
        ws = websocket.WebSocketApp(url,
                                on_open=self.on_open,
                                on_message=self.on_message,
                                on_error=self.on_error,
                                on_close=self.on_close)
        ws.run_forever()

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            print(f"\nService Added:")
            print(f"  Name: {name}")
            print(f"  Addresses: {addresses}")
            print(f"  Port: {info.port}")

            if len(addresses) != 0:
                address = addresses[0]
                portNo = info.port
                print("connecting...")
                self.connect(f"ws://{address}:{portNo}/sensor/connect?type=android.sensor.{self.sensor}")

zeroconf = Zeroconf()
listener = MyServiceListener('accelerometer') # sensors = ['accelerometer', 'gyroscope']
browser = ServiceBrowser(zeroconf, "_websocket._tcp.local.", listener)

try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
