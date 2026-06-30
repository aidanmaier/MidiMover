import time
from zeroconf import ServiceBrowser, Zeroconf
from ws_config import MyServiceListener
import pandas as pd

ws_address = '_websocket._tcp.local.'
sensors = ['accelerometer', 'gyroscope']
axes = ['x', 'y', 'z']
output_directory = './data/'
output_filename = 'gesture.csv'
polling_rate = 1000 # in Hz (MIDI controller standard = 1 kHz)

# Separate listener and browser for each sensor
zeroconf = Zeroconf()
listeners = [MyServiceListener(sensor) for sensor in sensors]
browsers = [ServiceBrowser(zeroconf, ws_address, listener) for listener in listeners]

# Record time-series data in df
labels = [sensors, axes]
cols = pd.MultiIndex.from_product(labels, names=['Sensor', 'Axis'])
df = pd.DataFrame(columns=cols)

# Stream controls for testing
try:
    input("\nConnect, then press enter to begin stream...\n\n")
finally:
    zeroconf.close()

# Loop to poll listener values
stream = True
print('streaming...\n')
while stream:
    timestamp = time.time()
    # Iterate through listeners
    for listener in listeners:
        values = listener.get_values()
        if values is not None:
            sensor = listener.sensor
            (x, y, z) = values
            df.loc[timestamp, [(sensor, ax) for ax in axes]] = x, y, z
            print(f'{sensor}:\t', values)
        else:
            stream = False
            break
        time.sleep(1/polling_rate) # convert Hz to seconds

# Write out to .csv
df.to_csv(output_directory + output_filename)
print(f'\noutput saved to: {output_filename}\n')