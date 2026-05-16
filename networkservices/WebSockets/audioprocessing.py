# WIP
# Intended to parse packets received from clients as separate stream objects and overlay them using ffmpeg
from asyncio import QueueEmpty

import ffmpeg
from clientclass import ClientObject
import asyncio

async def mix_stored_packets():
    while True:
        await asyncio.sleep(0)
        if ClientObject.user_streams:
            # If this has entries, get the lists (audio streams intake) off each user and play it.
            for audio_list in ClientObject.user_streams.values():
                # Using queues, we can push and pop properly.
                # In the future, for each queue, we want to make an input object with ffmpeg and mix them down into one output.
                # If this idea works, this should solve this implementation short-term before WebRTC becomes the main one.
                try:
                    frame = audio_list.get_nowait()
                    ClientObject.output_stream.write(frame)
                except QueueEmpty as e:
                    pass
            pass
    pass