# All of our services up here are intended to be ran in clientdriver.py
import sys
from constants import BUFFER_SIZE, ServerResp, ServerID

# Different platforms require different implementations.
if sys.platform == "win32":
    import pyaudiowpatch as pyaudio
elif sys.platform == "linux":
    import pyaudio
else:
    # Fallback, windows is the only known example with wpatch required due to WASAPI devices.
    import pyaudio

# globals (these should only change if the user changes them on channel start
CHUNK = BUFFER_SIZE
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000

# This class is our "god" class. Instead of shared memory with multiprocessing, this should make an object that makes this easier.
class ClientObject:
    # def __init__(self, json_req):
    # Store our original request here as a dict
    json_req = {}

    # Store other details as needed.
    user_streams = {str: list()}

    # Stream instance
    p = pyaudio.PyAudio()

    # Store pointers to our input/output devices.
    # By having the indexes on demand, we can redefine our streams as needed for other devices
    input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    input_index = p.get_default_input_device_info()['index']

    @classmethod
    def change_input_device(cls, new_input_idx):
        # Close current stream
        # Note: should we do this while the application is running?
        cls.input_stream.close()

        # Now open a new one
        cls.input_stream = cls.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                                      input_device_index = new_input_idx, frames_per_buffer=CHUNK)
        cls.input_index = new_input_idx
        pass

    output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    output_index = p.get_default_output_device_info()['index']

    @classmethod
    def change_output_device(cls, new_output_idx):
        # Close current stream
        # Note: should we do this while the application is running?
        cls.output_stream.close()

        # Now open a new one
        cls.output_stream = cls.p.open(format=FORMAT,
                      channels=CHANNELS,
                      rate=RATE,
                      out=True,
                      input_device_index = new_output_idx,
                      frames_per_buffer=CHUNK)
        cls.input_index = new_output_idx
        pass
    pass