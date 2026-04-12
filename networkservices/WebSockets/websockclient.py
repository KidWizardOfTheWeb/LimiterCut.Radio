# Websocket Client
import os
import sys
import json
from pathlib import Path
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
from websockets.exceptions import ConnectionClosed

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
                      frames_per_buffer=CHUNK)

USER_STATE = None

output_stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       output=True,
                       frames_per_buffer=CHUNK)


async def caster_handler(websocket):
    while True:
        try:
            # await websocket.send("Hello world!")
            data = input_stream.read(CHUNK)
            # data_pack = {
            #     "raw_data": data
            # }
            # json_req = json.dumps(data_pack)
            await websocket.send(data)
            # await websocket.wait_closed()
            # message = await websocket.recv()
            # print(message)
        except ConnectionClosed:
            raise ConnectionClosed
    pass

async def listener_handler(websocket):
    # while True:
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
    pass

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
        if USER_STATE == ServerResp.CAST_OK:
            try:
                while True:
                # await caster_handler(websocket)
                # await websocket.send("Hello world!")
                    data = input_stream.read(CHUNK)
                    await websocket.send(data)
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
                    await listener_handler(websocket)
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
        # "user_name": "" # Add this later for the server to visibly show who's casting.
    }

    json_req = json.dumps(channel_request_pack)

    # Call channel connection and run async tasks
    asyncio.run(handler(json_req))