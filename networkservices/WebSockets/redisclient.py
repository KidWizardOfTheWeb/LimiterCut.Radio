# Main client driver for redis based operations, such as chat.
import os
import sys
import json
import redis.asyncio as redis
import asyncio
from pathlib import Path
from environ import ImproperlyConfigured
import environ # For reading environment variables

from clientclass import ClientObject

# This is only for device references right now.
# DO NOT RUN ANY AUDIO SERVICES IN HERE.
if sys.platform == "win32":
    import pyaudiowpatch as pyaudio
elif sys.platform == "linux":
    import pyaudio
else:
    # Fallback, windows is the only known example with wpatch required due to WASAPI devices.
    import pyaudio


from constants import slash_commands

# Set up .env
BASE_DIR = Path(__file__).resolve().parent
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

async def reader(channel: redis.client.PubSub):
    while True:
        await asyncio.sleep(0)
        message = await channel.get_message(ignore_subscribe_messages=True, timeout=None)
        if message is not None:
            print(message['data'].decode())

async def ainput(prompt: str = ""):
    return await asyncio.to_thread(input, prompt)

async def writer(redis_channel, request_packet):
    await asyncio.sleep(0)
    result = await ainput()
    result = str(result)

    # If string contains slash command and slash command is start of line, compare to keyword list and print to console as needed.
    if "/" in result and result.find("/") == 0:
        # This is a possible slash command, parse the substring after the slash.
        # Split the string by slash. If the split is longer than X amount, this is too long.
        # TODO: depending on the command, it may have room for parameters. Make the below check change the length check depending on command

        command_id = result.split("/")[1] # This should be the first word in the command. Any other segment should be a param.

        command = slash_commands.get(command_id, None)
        match command_id:
            case "help":
                print(command.format(list(slash_commands.keys())))
            case "whoami":
                print(command.format(request_packet["user_name"]))
            case "devicelist":
                ClientObject.p.print_detailed_system_info()
            case "ping":
                # Pings the websocket here.
                # Currently invoking this in some other tests does not work well, so we'll have to find a way soon.
                pass
            case "getinputdevice":
                # Get input device details
                print(ClientObject.p.get_device_info_by_index(ClientObject.input_index))
            case "getoutputdevice":
                # Get output device details
                print(ClientObject.p.get_device_info_by_index(ClientObject.output_index))
            case _:
                pass
        pass

    # If string is not empty, push.
    elif result != "":
        await redis_channel.publish(request_packet["channel_id"], str(request_packet["user_name"] + ": " + result))
    pass

async def handler(request_packet):
    # Parse JSON-String to dict.
    json_pack = json.loads(request_packet)

    r = redis.Redis(host=json_pack["server_endpoint"], port=6379)

    async with r.pubsub() as pubsub:
        try:
            # Try to subscribe to the channel.
            await pubsub.subscribe(json_pack["channel_id"])

            # If successful, let everyone know you've joined!
            await r.publish(json_pack["channel_id"], str(json_pack["user_name"] + " has joined the channel!"))
        except Exception as e:
            # pass
            print(e)
            print("Redis pub/sub server cannot be reached. Skipping chat service activation...")
            return

        # Run both, return when one of these is completed.
        while True:
            reader_task = asyncio.create_task(reader(pubsub))
            writer_task = asyncio.create_task(writer(r, json_pack))
            done, pending = await asyncio.wait([reader_task, writer_task], return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()