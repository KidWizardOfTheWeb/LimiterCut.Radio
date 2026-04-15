# Websocket Client
import os
import sys
import json
import threading
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from threading import Thread
from queue import Queue

from environ import ImproperlyConfigured
import environ # For reading environment variables
from constants import BUFFER_SIZE, ServerResp, ServerID

# Different platforms require different implementations.
if sys.platform == "win32":
    import pyaudiowpatch as pyaudio
elif sys.platform == "linux":
    import pyaudio
else:
    # Fallback, windows is the only known example with wpatch required due to WASAPI devices.
    import pyaudio

"""Client using the asyncio API."""

import asyncio
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

# Set up .env
BASE_DIR = Path(__file__).resolve().parent
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Try to put in an ip for the server to connect to. If none, do localhost instead for local testing.
try:
    serverName = env("CLIENT_SERVER")
except ImproperlyConfigured as e:
    print(e)
    serverName = "localhost"
serverPort = 3601

# def input_callback(in_data, frame_count, time_info, status):
#     # places frames into queue
#     frames_sent.put(in_data)
#     return (in_data, pyaudio.paContinue)

# Audio I/O streams
# TODO: add stream for desktop audio with wpatch.
CHUNK = BUFFER_SIZE
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000
p = pyaudio.PyAudio()
input_stream = p.open(format=FORMAT,
                      channels=CHANNELS,
                      rate=RATE,
                      input=True,
                      frames_per_buffer=CHUNK,
                      # stream_callback=input_callback
                      )

USER_STATE = None

output_stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       output=True,
                       frames_per_buffer=CHUNK)

# We append our sent/received frames here as a way to create buffer and prevent choppy audio for chat rooms.
frames_sent = Queue()
frames_recv = Queue()

async def pop_frames():
    global output_stream
    while not frames_recv.empty():
        output_stream.write(frames_recv.get())
        pass
    pass

async def caster_handler(websocket):
    global input_stream
    # while True:
    await asyncio.sleep(0)
    try:
        await websocket.send(input_stream.read(CHUNK))
    except ConnectionClosed:
        raise ConnectionClosed
    await asyncio.sleep(0)
    pass

async def listener_handler(websocket):
    # global output_stream
    await asyncio.sleep(0)
    while True:
        async for data in websocket:
            try:
                # await websocket.send("Hello world!")
                # data = await websocket.recv()
                try:
                    frames_recv.put_nowait(data)
                except:
                    pass
                # fr_list.append(data)
                # output_stream.write(data)
                # This break statement makes the chat functionality work for local.
                # Unless you move things to new threads or make buffers, KEEP THIS FOR LOCAL TESTING.
                # break
            except ConnectionClosed:
                raise ConnectionClosed
    pass

async def radio_caster_handler(websocket):
    global input_stream
    # while True:
    # await asyncio.sleep(0)
    try:
        await websocket.send(input_stream.read(CHUNK))
    except ConnectionClosed:
        raise ConnectionClosed
    # await asyncio.sleep(0)
    pass

async def radio_listener_handler(websocket):
    global output_stream
    async for data in websocket:
        try:
            # await websocket.send("Hello world!")
            # data = await websocket.recv()
            output_stream.write(data)
            # await websocket.send(data)
            # print(message)
            # await asyncio.sleep(1)
        except ConnectionClosed:
            raise ConnectionClosed

async def new_listener_handler(websocket):
    # Reimplemented the functionality for "async for ... in websocket"
    # https://github.com/python-websockets/websockets/blob/16.0/src/websockets/asyncio/connection.py#L230-L246
    # In our version, we want to receive and write continuously without blocking casting.
    await asyncio.sleep(0)
    try:
        # while True:
        data = await websocket.recv()
        output_stream.write(data)
    except ConnectionClosedOK:
        return

async def handler(request_packet):
    global USER_STATE
    # Start with API call endpoint, unless this is a self-hosted server.
    # If API call fails, then don't continue with the rest.

    # Note: add API endpoint in statement below, retrieve token from API as needed.
    # async with connect("ws://apihost:8765") as websocket:
    #     await websocket.send("Hello world!")
    #     message = await websocket.recv()
    #     print(message)

    # API call should return the uri we want to connect to for the actual server

    # TODO: use uri received from API if a server is searched for.
    # If a user has a history of servers and they want to find one, keep a list in some user data folder.
    # For now, this loads from the packet, which comes from the .env file.
    server_uri = json.loads(request_packet)["server_endpoint"]

    # Perform casting/listening/other functions while connected.
    async for websocket in connect(server_uri):
        # First, connect to server and send the initial packet.
        # Packet includes channel requested, other information.
        if USER_STATE is None:
            await websocket.send(request_packet)
            USER_STATE = await websocket.recv()
            print(USER_STATE)
        if USER_STATE == ServerResp.CHAT_OK:
            # Cast and Listen permissions both active.
            try:
                while True:
                    listen_task = asyncio.create_task(new_listener_handler(websocket))
                    cast_task = asyncio.create_task(caster_handler(websocket))
                    done, pending = await asyncio.wait([listen_task, cast_task],
                                       # timeout=1,
                                       return_when=asyncio.FIRST_COMPLETED)
                    for task in pending:
                        task.cancel()
            except ConnectionClosed:
                print("Closed from chatting.")
                continue
        if USER_STATE == ServerResp.CAST_OK:
            try:
                while True:
                # await caster_handler(websocket)
                # await websocket.send("Hello world!")
                    await radio_caster_handler(websocket)
                    # await websocket.send(data)
                # message = await websocket.recv()
                # print(message)
            except ConnectionClosed:
                print("Closed from casting.")
                continue
        elif USER_STATE == ServerResp.LISTEN_OK:
            try:
                while True:
                    # data = await websocket.recv()
                    # print(data)
                    # output_stream.write(data)
                    await radio_listener_handler(websocket)
                # await websocket.send("Hello world!")
                # data = input_stream.read(CHUNK)
                # await websocket.send(data)
                # message = await websocket.recv()
                # print(message)
            except ConnectionClosed:
                print("Closed from listening.")
                continue



if __name__ == "__main__":
    # Note: change this later to not be hardcoded and allow this to retrieve name and ID from an API
    # server_names = [(s_names.name, s_names.value) for s_names in ServerID]
    # print("Available servers:")
    # print(*server_names, sep='\n')

    # server_id = input("Request access to an available server: ")

    print("Available channels:\n"
          "10.24 <-> 655.35")

    channel_id = input("Request access to an available channel: ")
    channel_type = input("Request channel type (Radio, chat): ")
    print("Requesting channel access to the server and waiting for approval...")

    # TODO: Allow the user to choose a server first.
    # Server set to Master System for now by default.

    # Uncomment this for local testing. Should make this a script arg in the future, honestly.
    # serverName = "localhost"

    server_endpoint = "ws://" + serverName + ":" + str(serverPort)
    channel_request_pack = {
        "server_endpoint": str(server_endpoint),
        "server_id": ServerID.MS,
        "channel_id": channel_id,
        "channel_type": channel_type
        # "user_name": "" # Add this later for the server to visibly show who's casting.
    }

    json_req = json.dumps(channel_request_pack)


    # Implement pyaudio threads here instead of in our async tasks
    # ...

    # Call channel connection and run async tasks
    asyncio.run(handler(json_req))