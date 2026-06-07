# All of our services up here are intended to be ran in clientdriver.py
import sys
from constants import BUFFER_SIZE, ServerResp, ServerID
from asyncio import Queue, queues
import functools

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

def output_callback(from_user, in_data, frame_count, time_info, status):
    # Get the specific user stream, consume it if available
    audio_stream = ClientObject.user_streams.get(from_user, None)
    if audio_stream is None:
        return (bytes(2496), pyaudio.paContinue)
    try:
        raw_audio_bytes = audio_stream.get_nowait()
    except queues.QueueEmpty as e:
        print(e)
        return (bytes(2496), pyaudio.paContinue)
    return (raw_audio_bytes, pyaudio.paContinue)

class UserStreamsDict(dict):
    def __setitem__(self, key, value):
        if key not in self:
            # Create new ffmpeg process

            print(f"New user stream from: '{key}' added!")
        super().__setitem__(key, value)
    pass

class UserObjectsDict(dict):
    def __setitem__(self, key, value):
        if key not in self:
            # p = pyaudio.PyAudio()
            # # Create new ffmpeg process
            # value = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
            print(f"New user object from: '{key}' added!")
        super().__setitem__(key, value)
    pass

# This class is our "god" class. Instead of shared memory with multiprocessing, this should make an object that makes this easier.
class ClientObject:
    # def __init__(self, json_req):
    # Store our original request here as a dict
    json_req = {}

    # Stream instance
    p = pyaudio.PyAudio()

    # Store other details as needed.
    user_streams = UserStreamsDict()

    user_objects = UserObjectsDict()
    # {str: Queue()}

    @classmethod
    def add_new_output_stream(cls, user_to_add):
        if user_to_add not in cls.user_objects.keys():
            # Create new ffmpeg process
            new_stream = cls.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK, stream_callback=functools.partial(output_callback, user_to_add))
            cls.user_objects[user_to_add] = new_stream
        pass

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

    # output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
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
                      output_device_index = new_output_idx,
                      frames_per_buffer=CHUNK)
        cls.input_index = new_output_idx
        pass
    pass