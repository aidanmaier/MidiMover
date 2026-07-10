import time
import asyncio
import pandas as pd
from pathlib import Path
from typing import Callable

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

    def get_sample(self, index: int) -> pd.Series:
        """
        Returns a pd.Series of all sensor values at the given index.
        """

        sample = self.data.iloc[index]
        return sample

    async def stream(self, callback: Callable[[pd.Series], None], loop: bool = False) -> None:
        """
        Streams loaded data at its average sample rate, and triggers the callback function for each sample.
        """

        next_time = time.monotonic() # start forward-only clock
        index = 0

        while index < self.samples:

            # Iterate through samples in data stream and trigger callback function for each
            sample = self.get_sample(index)
            callback(sample)
            index += 1

            # Normalise loop time to sample_period
            next_time += self.sample_period # ideal sample period length
            delay = next_time - time.monotonic() # remainder after subtracting elapsed time
            if delay > 0:
                await asyncio.sleep(delay) # wait for duration of remainder

            # If loop, restart the index at completion
            if (index >= self.samples) and loop:
                index = 0

# TEST CODE:

if __name__ == '__main__':
    
# Input variables
    input_directory = Path(__file__).resolve().parent.parent / 'data'
    input_filename = 'test.csv'

    # Callback functions
    def z_rotation(sample: pd.Series):
        # streaming rotation around z axis
        sensor = 'rotation_vector'
        axis = 'z'
        z_value = float(sample[(sensor, axis)]) 
        # print(f'{sensor} {axis}: {z_value}') 
        print(sample)

    def print_values(sample: pd.Series):
        print(sample)

    async def main():

        # Load sensor data from .csv
        data = DataLoader(input_directory, input_filename)
        await data.stream(callback=print_values, loop=False)
        print(f'\nSample rate: {data.sample_rate}, Sample period: {data.sample_period}\n') #DEBUG

    asyncio.run(main())