# Main client driver for redis based operations, such as chat.
import os
import json
import redis.asyncio as redis
import asyncio
from pathlib import Path
from environ import ImproperlyConfigured
import environ # For reading environment variables

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
    if result is not None:
        await redis_channel.publish(request_packet["channel_id"], str(request_packet["user_name"] + ": " + result))
    pass

async def handler(request_packet):
    r = redis.Redis(host=env("CLIENT_SERVER"), port=6379)

    json_pack = json.loads(request_packet)

    async with r.pubsub() as pubsub:
        await pubsub.subscribe(json_pack["channel_id"])

        # Run both, return when one of these is completed.
        while True:
            reader_task = asyncio.create_task(reader(pubsub))
            writer_task = asyncio.create_task(writer(r, json_pack))
            done, pending = await asyncio.wait([reader_task, writer_task], return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()