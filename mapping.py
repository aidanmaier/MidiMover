from playback import *
import time
import mido

input_directory = './data/'
input_filename = 'gesture.csv'
sensor = 'gyroscope'
axis = 'x'

# Load data from .csv
data = DataLoader(input_directory, input_filename)
gyro_streamer = SensorStreamer(data)
polling_rate = gyro_streamer.polling_rate

print(f'\nPolling rate: {polling_rate} Hz\n')

# Stream values for given sensor and axis at the polling rate
stream = gyro_streamer.stream(sensor, axis)
for sample in stream:
    print(sample)
    time.sleep(1/polling_rate) # convert Hz to seconds