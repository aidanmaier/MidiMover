import pandas as pd
import time
import asyncio
from pathlib import Path
from typing import Callable

# Input variables
input_directory = Path(__file__).resolve().parent.parent / 'data'
input_filename = 'rotation_z.csv'

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
        self.sensors = {tup[0] for tup in df.columns} # set of available sensors

        self.length = (df.index[-1] - df.index[0]) / 1_000_000_000  # length in seconds
        self.samples = len(df.index) # number of samples
        self.sample_rate = (self.samples - 1) / self.length # in Hz
        self.sample_period = 1 / self.sample_rate # sample period in seconds

    def get_sample(self, sensor: str, index: int) -> list:
        """
        Returns a list of sensor values for all axes of given sensor at given index.
        """
        sample = self.data.iloc[index][sensor]
        return list(sample)

    async def stream(self, callback: Callable, loop: bool = False) -> None:
        """
        Streams loaded data at its average sample rate, and triggers the callback function for each sample.
        """
        
        next_time = time.monotonic() # start forward-only clock
        index = 0

        while index < self.samples:

            # Iterate through samples in data stream and trigger callback function for each
            callback(index, self)
            index += 1

            # Normalise loop time to sample_period
            next_time += self.sample_period # ideal sample period length
            delay = next_time - time.monotonic() # remainder after subtracting elapsed time
            if delay > 0:
                await asyncio.sleep(delay) # wait for duration of remainder

            # If loop, restart the index at completition
            if index >= self.samples and loop:
                index = 0


# TEST CODE:

def stream_z(index, dataLoader):
    sensor = 'rotation_vector'
    print(sensor, dataLoader.get_sample(sensor, index)[2]) # streaming rotation around z axis

async def main():

    # Load sensor data from .csv
    dataLoader = DataLoader(input_directory, input_filename)
    await dataLoader.stream(stream_z, loop=False)

if __name__ == '__main__':
    asyncio.run(main())