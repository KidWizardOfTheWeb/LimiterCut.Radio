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
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK
import base64

from clientclass import ClientObject

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

USER_STATE = None

async def chat_caster_handler(websocket):
    # global input_stream
    # while True:
    await asyncio.sleep(0)
    try:
        # Send a packet with the username recorded for our hash-layered stream protocol (still working on the name)
        # MUST BE SENT AS A TEXT-FRAME (JSON string)

        # Get out input audio chunk
        audio_chunk = ClientObject.input_stream.read(BUFFER_SIZE)

        # Create our data packet
        LC_audio_packet = {
            "user_name": ClientObject.json_req["user_name"],
            "audio_data": base64.b64encode(audio_chunk).decode()
        }

        # Dump the string
        json_rep = json.dumps(LC_audio_packet)

        # Send to websocket.
        await websocket.send(json_rep)
    except ConnectionClosed:
        raise ConnectionClosed
    await asyncio.sleep(0)
    pass

async def chat_listener_handler(websocket):
    # Reimplemented the functionality for "async for ... in websocket"
    # https://github.com/python-websockets/websockets/blob/16.0/src/websockets/asyncio/connection.py#L230-L246
    # In our version, we want to receive and write continuously without blocking casting.
    await asyncio.sleep(0)
    try:
        data = await websocket.recv()

        # Load our data packet
        json_packet = json.loads(data)

        # The actual data itself
        audio_chunk = json_packet["audio_data"]
        audio_chunk = base64.b64decode(audio_chunk)

        # This is the user who sent in the data
        from_user_name = json_packet["user_name"]
        if ClientObject.user_streams.get(from_user_name, None) is None:
            ClientObject.user_streams[from_user_name] = list()
        ClientObject.user_streams[from_user_name].append(audio_chunk)

        # The write to output function
        ClientObject.output_stream.write(audio_chunk)
    except ConnectionClosedOK:
        return

async def radio_caster_handler(websocket):
    # global input_stream
    # while True:
    # await asyncio.sleep(0)
    try:
        # Send a packet with the username recorded for our hash-layered stream protocol (still working on the name)
        # MUST BE SENT AS A TEXT-FRAME (JSON string)

        # Get out input audio chunk
        audio_chunk = ClientObject.input_stream.read(BUFFER_SIZE)

        # Create our data packet
        LC_audio_packet = {
            "user_name": ClientObject.json_req["user_name"],
            "audio_data": base64.b64encode(audio_chunk).decode()
        }

        # Dump the string
        json_rep = json.dumps(LC_audio_packet)

        # Send to websocket.
        await websocket.send(json_rep)
    except ConnectionClosed:
        raise ConnectionClosed
    # await asyncio.sleep(0)
    pass

async def radio_listener_handler(websocket):
    # global output_stream
    async for data in websocket:
        try:
            # Load our data packet
            json_packet = json.loads(data)

            # The actual data itself
            audio_chunk = json_packet["audio_data"]
            audio_chunk = base64.b64decode(audio_chunk)

            # This is the user who sent in the data.
            # For each unique name, add a new entry to our user_streams dict and record packets.
            # Each packet goes into our list for our user
            from_user_name = json_packet["user_name"]
            if ClientObject.user_streams.get(from_user_name, None) is None:
                ClientObject.user_streams[from_user_name] = list()
            ClientObject.user_streams[from_user_name].append(audio_chunk)

            # The write to output function
            ClientObject.output_stream.write(audio_chunk)
        except ConnectionClosed:
            raise ConnectionClosed

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
                    # TODO: move the output_stream.write() functionality to audioprocessing.py
                    listen_task = asyncio.create_task(chat_listener_handler(websocket))
                    cast_task = asyncio.create_task(chat_caster_handler(websocket))
                    done, pending = await asyncio.wait(
                        [listen_task, cast_task],
                        # timeout=1,
                        return_when=asyncio.FIRST_COMPLETED)

                    for task in pending:
                        task.cancel()

            except ConnectionClosed:
                print("Closed from chatting.")
                # Reset user state here to ask for permission to connect again.
                USER_STATE = None
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
                USER_STATE = None
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
                USER_STATE = None
                continue

# [[deprecated]]
# NOTE: deprecated for clientdriver.py instead. Use that script to run this file in the future.
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
        # "user_name": "" # Add this later for the server to visibly show who's casting, redis management, etc.
    }

    # Create json-request
    json_req = json.dumps(channel_request_pack)

    # Call channel connection and run async tasks
    asyncio.run(handler(json_req))