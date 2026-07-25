import time
import asyncio
from typing import Callable
from zeroconf import ServiceBrowser, Zeroconf
from logic.listen import WebsocketServiceListener

class DataStreamer():

    def __init__(self, ws_address: str, sensors: list[str]) -> None:
        """ 
        Parameters: 
        ws_address (string): local websocket address
        sensors (list of strings): list of Android sensor types to access, must contain two or more items.
        """
        # Handle ws_address value
        if isinstance(ws_address, str):
            self.ws_address = ws_address
        else:
            TypeError('ws_address must be a string')

        # Handle sensors value
        if isinstance(sensors, list):
            if len(sensors) >= 2:
                self.sensors = sensors
            else:
                ValueError('two or more sensors must be specified')
        else:
            TypeError('sensors must be a list of strings')
            
        # Create Listener and Zeroconf Browser
        self.zeroconf = Zeroconf() # Zerconf instance
        self.listener = WebsocketServiceListener(self.sensors)
        self.browser = ServiceBrowser(self.zeroconf, self.ws_address, self.listener)
    
    async def stream(self, callback: Callable, sample_rate: int, wait_for_user: bool = True, stop_event = None) -> None:
        """
        Streams input data at given sample_rate data and triggers the callback function for each sample.

        Parameters:
        callback (Callable): callback function triggered once per sample
        sample_rate (int): sampling rate in Hz
        wait_for_user (bool): whether to pause for manual confirmation before streaming
        """

        # Wait for connection
        print('\nConnect input device\n')
        while not self.listener.open:
            await asyncio.sleep(0.1)
        self.zeroconf.close()

        # User starts stream recording manually
        if wait_for_user:
            try:
                input('\nPress enter to begin streaming\n')
            finally:
                print('streaming...\n')
        else:
            print('streaming...\n')

        # Capture Loop running at sample rate (Hz)
        stream = True
        sample_period = 1 / sample_rate # sample period in seconds
        next_time = time.monotonic() # start forward-only clock
    
        while stream:
            if stop_event is not None and stop_event.is_set():
                break

            sample = self.listener.get_values()

            if sample and sample['timestamp']:
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