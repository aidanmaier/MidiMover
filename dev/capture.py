import time
import asyncio
import pandas as pd
from zeroconf import ServiceBrowser, Zeroconf
from sys import path
path.insert(0, "../")
from ws_config import WebsocketServiceListener

# Input variables
sensors = [

    ## Hardware senors:
    # 'accelerometer', 
    # 'gyroscope'

    ## Software sensors:
    'linear_acceleration',
    'rotation_vector'

           ]

ws_address = '_websocket._tcp.local.'
axes = ['x', 'y', 'z']
polling_rate_hz = 50 # in Hz

# Outputs variables
output_directory = '../data/'
output_filename = 'test.csv'

# Separate listener and browser for each sensor
zeroconf = Zeroconf()
listeners = [WebsocketServiceListener(sensor) for sensor in sensors]
browsers = [ServiceBrowser(zeroconf, ws_address, listener) for listener in listeners]

# Record time-series data in df
labels = [sensors, axes]
cols = pd.MultiIndex.from_product(labels, names=['Sensor', 'Axis'])
df = pd.DataFrame(columns=cols)

def estimate_sample_rate(dataframe: pd.DataFrame) -> float:
    """
    Estimate the average sample rate from the recorded timestamp span.
    """
    timestamps = pd.to_numeric(pd.Series(dataframe.index))
    ordered = timestamps.sort_values()
    duration_seconds = (ordered.iloc[-1] - ordered.iloc[0]) / 1_000_000_000 # convert ns to s
    return (len(ordered) - 1) / duration_seconds

async def main():
    """
    Loops through listeners to poll sensor values, and writes out to .csv with timestamp.
    """

    # User starts stream recording manually
    try:
        input("\nConnect, then press enter to begin stream...\n\n")
    finally:
        zeroconf.close()

    # Capture Loop running at polling_rate_hz
    stream = True
    sample_period = 1 / polling_rate_hz # sample period in seconds
    print('streaming...\n')
    next_time = time.monotonic() # start forward-only clock

    while stream:

        # Shared timestamp for all sensors
        timestamp_message = listeners[0].get_values()
        if timestamp_message is None or 'timestamp' not in timestamp_message:
            print('No input message received - stopping capture')
            stream = False
            break
        else:
            timestamp = timestamp_message['timestamp']

        # Iterate through listeners retrieving data
        for listener in listeners:
            message = listener.get_values()

            if message is not None:
                sensor = listener.sensor
                values = message.get('values', [])
                if len(values) < 3:
                    continue

                # retrieve data from listener
                (x, y, z) = values[:3] # axes data = first 3 items in values

                # write data to df
                df.loc[timestamp, [(sensor, ax) for ax in axes]] = x, y, z
                print(f'{sensor}: {timestamp} {[x, y, z]}') # DEBUG 
            else:
                stream = False
                break

        # Normalise loop length to sample_period
        next_time += sample_period # ideal sample period length
        delay = next_time - time.monotonic() # remainder after subtracting elapsed time
        if delay > 0:
            await asyncio.sleep(delay) # wait for duration of remainder

    if df.index.empty:
        print('\nNo sensor data was captured.')
    else:
        
        # Write out to .csv
        df.to_csv(output_directory + output_filename)
        print(f'\noutput saved to: {output_filename}')

        # Rates estimated from recorded data
        sample_rate = estimate_sample_rate(df)
        print(f'\nAverage sample rate: {sample_rate} Hz')
        print(f'Average sample period: {1 / sample_rate} seconds\n')

if __name__ == '__main__':
    asyncio.run(main())