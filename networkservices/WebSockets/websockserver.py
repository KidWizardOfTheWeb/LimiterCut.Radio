#!/usr/bin/env python
# Websocket Server
import os
import sys
import json
from socket import gethostname
# from pathlib import Path
# import pyaudiowpatch as pyaudio
# from environ import ImproperlyConfigured
# import environ # For reading environment variables
from constants import BUFFER_SIZE, ServerResp, ServerID, Connect4
"""Echo server using the asyncio API."""

import asyncio
from websockets.asyncio.server import broadcast, serve
import secrets

# Our overarching globals for recording casters & receivers
channel_table = {}
cast_table = {}
receive_table = {}
room_table = {}

# Join keys, from the example
JOIN = {}

if sys.platform == "win32":
    serverName = "localhost"
elif sys.platform == "linux":
    # Keeps all ports open for this to work. Go back and adjust this later.
  serverName = "0.0.0.0"
else:
    # fallback option
    # Note: can we do this without this import? This is the only usage.
    serverName = gethostname()
serverPort = 3601

# NOTE: the "start" function below this comment is from the websockets example, ignore this for now (unused).
# But feel free to refactor in the future when we want to make an init func on each channel instance (highly likely!)
async def start(websocket):
    # Initialize a Connect Four game, the set of WebSocket connections
    # receiving moves from this game, and secret access token.
    game = Connect4()
    connected = {websocket}

    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected

    try:
        # Send the secret access token to the browser of the first player,
        # where it'll be used for building a "join" link.
        event = {
            "type": "init",
            "join": join_key,
        }
        await websocket.send(json.dumps(event))

        # Temporary - for testing.
        print("first player started game", id(game))
        async for message in websocket:
            print("first player sent", message)

    finally:
        del JOIN[join_key]

async def cast_to_client(websocket, channel_id):
    # When packets are received from the caster, broadcast them to the clients connected.
    # TODO: use the second param instead of retrieving every single time data is received.
    async for data in websocket:
        channel_to_cast = cast_table.get(websocket.id, None)
        if receive_table.get(channel_to_cast, None) is not None:
            broadcast(set(receive_table[channel_to_cast]), data)
    pass


async def broadcast_to_clients(websocket, channel_id):
    # When packets are received from the caster, broadcast them to the clients connected.
    async for data in websocket:
        # Get all users that are not this specific websocket and broadcast
        # This will broadcast to everyone in the room as usual, including the main user.
        # NOTE: to test on the same local device, uncomment this line and comment the other version out.
        # users_to_receive = room_table[channel_id]
        users_to_receive = room_table[channel_id].difference({websocket})
        broadcast(users_to_receive, data)
    pass


async def join_room(websocket, channel_id):
    # If room exists, user joins the set instead.
    room_table[channel_id].add(websocket)
    '''
    room_table[channel_X] = {websock1, websock2, ...}
    '''
    try:
        await websocket.send(ServerResp.CHAT_OK)
        await broadcast_to_clients(websocket, channel_id)
        await websocket.wait_closed()
    finally:
        room_table[channel_id].remove(websocket)
    pass


async def start_room(websocket, channel_id):
    # Init a duplex room here.
    # One user starts a room, so add them as the first in the set
    room_table[channel_id] = {websocket}
    '''
    room_table[channel_X] = {websock1}
    '''
    try:
        await websocket.send(ServerResp.CHAT_OK)
        await broadcast_to_clients(websocket, channel_id)
        await websocket.wait_closed()
    finally:
        room_table[channel_id].remove(websocket)
    pass


async def handler(websocket):
    message = await websocket.recv()
    try:
        event = json.loads(message)
    except:
        # If bytes, this is an audio packet. Don't. Just don't.
        # Note: we should handle this WAY better honestly. Event has a chance of just not existing.
        if isinstance(message, bytes):
            return
        pass

    # TODO: add more events for verification when connecting to the server for the first time, like init, cast, listen, etc.

    print(event)
    print('User is requesting an action on channel: ', event["channel_id"], '\nfrom: ', websocket)

    if "chat" in event["channel_type"]:
        # Start room proc here if room isn't open, otherwise search for room and join
        if event["channel_id"] not in room_table.keys():
            await start_room(websocket, event["channel_id"])
        else:
            await join_room(websocket, event["channel_id"])
        pass
    else:
        # If the channel is not being hosted currently, open new channel
        list_of_casters = cast_table.get(event["channel_id"])
        # print(list_of_casters)

        # TODO: add "start channel func" instead of instantly casting to client.
        # Also, refactor the below logic into their own functions for easier readability.

        # If there is no caster AND there is no one casting to the current channel requested, set them as the caster.
        if not list_of_casters and event["channel_id"] not in cast_table.values():
            # Assign caster to table, value is channel_id
            cast_table[websocket.id] = event["channel_id"]
            try:
                # Send success response for casting.
                await websocket.send(ServerResp.CAST_OK)
                # Send them to cast func, where messages received will be broadcast properly in an async loop.
                await cast_to_client(websocket, event["channel_id"])
            finally:
                # Remove the caster from cast_table on disconnect
                cast_table.pop(websocket.id)
                pass
            pass
        else:
            # Check if the user is already casting. If they are, do NOT let them in here.
            # Sets disallow the same websocket from connecting, lists allow dupes.
            if cast_table.get(websocket.id, None) is None:
                list_of_receivers = receive_table.get(event["channel_id"])
                if not list_of_receivers:
                    # If not in our table, add it.
                    # Note: currently a set. Can change back to list later to allow dupes.
                    receive_table[event["channel_id"]] = {websocket}
                else:
                    # If it does exist, the value should be a list of connections. Append to the connection list
                    receive_table[event["channel_id"]].add(websocket)
                try:
                    # Send success response for listening.
                    await websocket.send(ServerResp.LISTEN_OK)
                    # Keep socket open, but don't perform any operations here.
                    # The listener will instead just receive packets from the caster broadcast.
                    # Later, we might add a chat function here or some way for listeners to interact with the server. Who knows.
                    await websocket.wait_closed()
                finally:
                    # Remove this listener from the receive_table's set/list on disconnect.
                    receive_table[event["channel_id"]].remove(websocket)
                    pass
                pass

    # async for message in websocket:
        # if data:
        # output_stream.write(message)
        # await websocket.send(message)


async def main():
    async with serve(handler, serverName, serverPort) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())