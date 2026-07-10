import time
import asyncio
from typing import Callable
from zeroconf import ServiceBrowser, Zeroconf
from ws_config import WebsocketServiceListener

class DataStreamer():

    def __init__(self, ws_address: str, sensors: list[str]) -> None:
        """ """
        self.ws_address = ws_address
        self.sensors = sensors

        # Create Listener and Browser
        self.listener = WebsocketServiceListener(self.sensors)
        self.browser = ServiceBrowser(Zeroconf(), self.ws_address, self.listener)
    
    async def stream(self, callback: Callable, sample_rate: int) -> None:
        """
        Streams input data at given sample_rate data and triggers the callback function for each sample.

        Parameters:
        callback (Callable): callback function triggered once per sample
        sample_rate (int): sampling rate in Hz
        """
        # User starts stream recording manually
        try:
            input("\nConnect, then press enter to begin stream...\n\n")
        finally:
            Zeroconf().close()

        # Capture Loop running at sample rate (Hz)
        stream = True
        sample_period = 1 / sample_rate # sample period in seconds
        next_time = time.monotonic() # start forward-only clock
        print('streaming...\n')

        while stream:

            sample = self.listener.get_values()

            if sample:
                callback(sample)
            else:
                stream = False
                break

            # Normalise loop length to sample_period
            next_time += sample_period # ideal sample period length
            delay = next_time - time.monotonic() # remainder after subtracting elapsed time
            # print(f'Sample period: {delay} s, Sample rate: {1 / delay}') #DEBUG
            if delay > 0:
                await asyncio.sleep(delay) # wait for duration of remainder 

            
# TEST CODE:
if __name__ == '__main__':

    ws_address = '_websocket._tcp.local.'
    sensors = [
        # 'gyroscope', 
        # 'accelerometer', 
        'rotation_vector', 
        'linear_acceleration'
            ]
    sample_rate = 50 # Hz
    data = DataStreamer(ws_address, sensors)

    # Callback function
    def print_sample(sample):
        print(sample)

    async def main():
        await data.stream(print_sample, sample_rate)

    asyncio.run(main())