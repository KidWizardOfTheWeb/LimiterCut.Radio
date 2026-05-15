# WIP
# Intended to parse packets received from clients and overlay them using ffmpeg
import ffmpeg
from clientclass import ClientObject
import asyncio

async def mix_stored_packets():
    while True:
        await asyncio.sleep(0)
        if ClientObject.user_streams:
            # If this has entries, get the lists (audio streams intake) off each user and play it.
            for audio_list in ClientObject.user_streams.values():
                # > BUFFER
                # NOTE: this really doesn't work as well as it did in my head.
                # There's too much blocking, and buffer being arbitrary instead of adaptive really puts a damper on it.
                # What also happens is that if someone is passing in packets and there's too many,
                # incoming packets are DEMOLISHED (popped) before even playing, rather than playing first, then destroying.
                if len(audio_list) > 30:
                    ClientObject.output_stream.write(audio_list.pop())
            pass
    pass