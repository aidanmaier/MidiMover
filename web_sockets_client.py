from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import websocket
import json
import socket


def on_message(ws, message):
    values = json.loads(message)['values']
    x = values[0]
    y = values[1]
    z = values[2]
    print("x = ", x , "y = ", y , "z = ", z )

def on_error(ws, error):
    print("error occurred ", error)
    
def on_close(ws, close_code, reason):
    print("connection closed : ", reason)
    
def on_open(ws):
    print("connected")
    

def connect(url):
    ws = websocket.WebSocketApp(url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()
 

class MyServiceListener(ServiceListener):

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
                connect(f"ws://{address}:{portNo}/sensor/connect?type=android.sensor.accelerometer")
                # change type= to access others sensors
                # type=android.sensor.gyroscope

    
zeroconf = Zeroconf()
listener = MyServiceListener()
browser = ServiceBrowser(zeroconf, "_websocket._tcp.local.", listener)
try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
    