# WIP
# Intended to parse packets received from clients as separate stream objects and overlay them using ffmpeg
from asyncio import QueueEmpty

import sys

import numpy
import numpy as np

from clientclass import ClientObject
import asyncio

# Different platforms require different implementations.
if sys.platform == "win32":
    import pyaudiowpatch as pyaudio
elif sys.platform == "linux":
    import pyaudio
else:
    # Fallback, windows is the only known example with wpatch required due to WASAPI devices.
    import pyaudio

# Supposedly nonblocking, this should prevent blocking from below
# def output_callback(from_user, in_data, frame_count, time_info, status):
#     # Get the specific user stream, consume it if available
#     audio_stream = ClientObject.user_streams.get(from_user, None)
#     if audio_stream is None:
#         return (None, pyaudio.paContinue)
#     return (audio_stream, pyaudio.paContinue)

# Temporarily deprecated
async def mix_stored_packets():
    while True:
        await asyncio.sleep(0)
        if ClientObject.user_streams:
            output_buffer = bytes()
            # final_frame = numpy.empty((4096,2), dtype=np.int16)
            # If this has entries, get the lists (audio streams intake) off each user and play it.
            for user, audio_list in ClientObject.user_streams.items():
                if audio_list.empty():
                    continue
                # Output to their own objects
                ClientObject.user_objects[user].write(audio_list.get_nowait())
                # output_buffer += audio_list.get_nowait()
            # Only when all streams are done being retrieved, do we read it here.

            # ClientObject.output_stream.write(output_buffer)
                # Using queues, we can push and pop properly.
                # In the future, for each queue, we want to make an input object with ffmpeg and mix them down into one output.
                # If this idea works, this should solve this implementation short-term before WebRTC becomes the main one.
            #     try:
            #         # Get filterable stream for a user.
            #         frame = audio_list.get_nowait()
            #         frame_array = numpy.frombuffer(frame, dtype=np.int16)
            #         frame_array = frame_array.reshape(-1,2)
            #         final_frame += frame_array
            #         final_frame // 2
            #         # Do calculations for final frame to play
            #         # ClientObject.output_stream.write(frame)
            #     except QueueEmpty as e:
            #         pass
            #
            # final_frame = np.clip(final_frame, -32768, 32767)
            # final_frame = final_frame / np.max(np.abs(final_frame))
            # ClientObject.output_stream.write(final_frame.astype(np.int16).tobytes())
            # mixed = ffmpeg.filter(list(ClientObject.user_streams.values()), 'amix', inputs=len(ClientObject.user_streams), duration='longest')
            # ffmpeg.output(mixed, 'output_mixed.mp3').run()
            # pass
    pass