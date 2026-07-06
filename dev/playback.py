import pandas as pd
import time
import asyncio
from pathlib import Path

# Input variables
input_directory = Path(__file__).resolve().parent.parent / 'data'
input_filename = 'test.csv'

# Output variables
target_sensors = ['linear_acceleration', 'rotation_vector']
target_axes = ['x', 'y', 'z']

class DataLoader():
    def __init__(self, directory: str | Path, filename: str) -> None:
        """
        Loads captured motion sensor data from .csv to df.
        """
        self.dir = Path(directory)
        self.file = filename
        self.filepath = self.dir / filename

        # Load data to df from .csv
        df = pd.read_csv(self.filepath, header=[0, 1], index_col=0)
        self.data = df

        self.length = (df.index[-1] - df.index[0]) / 1_000_000_000  # length in seconds
        self.samples = len(df.index) # number of samples
        self.sample_rate = (self.samples - 1) / self.length # in Hz

    def get_sample(self, sensor: str, index: int) -> list:
        """
        Returns a list of sensor values for all axes of given sensor at given index.
        """
        sample = self.data.iloc[index][sensor]
        return list(sample)

async def main():

    # Load sensor data from .csv
    sensor_stream = DataLoader(input_directory, input_filename)

    # Calculate rates
    sample_rate = sensor_stream.sample_rate
    sample_period = 1 / sample_rate # sample period in seconds
    print(f'\nAverage sample rate: {sample_rate} Hz')
    print(f'Average sample period: {sample_period} seconds\n')

    # Stream data at sample rate
    next_time = time.monotonic() # start forward-only clock
    index = 0
    while index < len(sensor_stream.data):
        
        # Iterate through target sensors and access data by sample
        for sensor in target_sensors:
            print(sensor, sensor_stream.get_sample(sensor, index))

        index += 1

        # Normalise loop length to sample_period
        next_time += sample_period # ideal sample period length
        delay = next_time - time.monotonic() # remainder after subtracting elapsed time
        if delay > 0:
            await asyncio.sleep(delay) # wait for duration of remainder

if __name__ == '__main__':
    asyncio.run(main())