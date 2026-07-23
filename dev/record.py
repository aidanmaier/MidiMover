import asyncio
import pandas as pd
from zeroconf import ServiceBrowser, Zeroconf
from sys import path
path.insert(0, "../")
from logic.capture import DataStreamer

def estimate_sample_rate(dataframe: pd.DataFrame) -> float:
    """
    Estimate the average sample rate from the recorded timestamp span.
    """
    timestamps = pd.to_numeric(pd.Series(dataframe.index))
    ordered = timestamps.sort_values()
    duration_seconds = (ordered.iloc[-1] - ordered.iloc[0]) / 1_000_000_000 # convert ns to s
    return (len(ordered) - 1) / duration_seconds

# Input variables
ws_address = '_websocket._tcp.local.'
sensors = [
    'gyroscope', 
    'accelerometer', 
    'rotation_vector', 
    'linear_acceleration',
    'gravity'
        ]
axes = ['x', 'y', 'z', 'w'] # Android sensor all return x, y, z and rotation_vector also returns w (scalar)
sample_rate = 50 # Hz

# Output variabls
output_directory = '../data/'
output_filename = 'test.csv'

labels = [sensors, axes]
cols = pd.MultiIndex.from_product(labels, names=['Sensor', 'Axis'])
df = pd.DataFrame(columns=cols)

# Callback function
def save_sample(sample):
    
    # Extract timestamp for index
    timestamp = sample.get('timestamp')
    if timestamp is None:
        return
    
    # Data structure
    ds = pd.Series(index=cols, dtype=float)
    
    # Extract data
    sensor_data = sample.get('sensors', {})
    for sensor in sensors:
        values = sensor_data.get(sensor, [])
        # Handle for different sensors returning different number of floats
        if isinstance(values, (list, tuple)):
            for axis_name, value in zip(axes, values):
                ds[(sensor, axis_name)] = value
    
    # Save data to df
    df.loc[timestamp, cols] = ds.values

# Input object
data = DataStreamer(ws_address, sensors)

async def main():

    await data.stream(save_sample, sample_rate)

    if df.index.empty:
        print('\nNo sensor data was captured.')
    else:
        # Write out to .csv
        df.to_csv(output_directory + output_filename)
        print(f'\noutput saved to: {output_directory + output_filename}')

    # Rates estimated from recorded data
    avg_sample_rate = estimate_sample_rate(df)
    print(f'\nAverage sample rate: {avg_sample_rate} Hz')
    print(f'Average sample period: {1 / avg_sample_rate} seconds\n')

asyncio.run(main())