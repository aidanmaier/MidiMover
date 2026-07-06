import pandas as pd
import time
import asyncio

# Input variables
input_directory = '../data/'
input_filename = 'test.csv'

# Output variables
target_sensor = 'rotation_vector'
target_axis = 'x'

class DataLoader():
    def __init__(self, directory: str, filename: str) -> None:
        """
        Loads captured motion sensor data from .csv to df.
        """
        self.dir = directory
        self.file = filename
        self.filepath = directory + filename

        # Load data to df from .csv
        df = pd.read_csv(self.filepath, header=[0, 1], index_col=0)
        self.data = df

        self.length = (df.index[-1] - df.index[0]) / 1_000_000_000  # length in seconds
        self.samples = len(df.index) # number of samples
        self.sample_rate = (self.samples - 1) / self.length # in Hz

    def stream(self, sensor: str, axis: str) -> list:
        """
        Returns data for given sensor and axis as list.
        """
        data = self.data[(sensor, axis)]
        return list(data)

async def main():

    # Load sensor data from .csv
    data = DataLoader(input_directory, input_filename)

    # Calculate rates
    sample_rate = data.sample_rate
    sample_period = 1 / sample_rate # sample period in seconds
    print(f'\nAverage sample rate: {sample_rate} Hz\n')
    print(f'Average sample period: {sample_period} seconds\n')

    # Stream data at sample rate
    next_time = time.monotonic() # start forward-only clock
    for sample in data.stream(target_sensor, target_axis):
        print(sample)

        # Normalise loop length to sample_period
        next_time += sample_period # ideal sample period length
        delay = next_time - time.monotonic() # remainder after subtracting elapsed time
        if delay > 0:
            await asyncio.sleep(delay) # wait for duration of remainder

if __name__ == '__main__':
    asyncio.run(main())