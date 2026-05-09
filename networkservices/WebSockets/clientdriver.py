# Main client driver for all services, use this as your main launching point.
import os
import json
from pathlib import Path
from environ import ImproperlyConfigured
import environ # For reading environment variables
from constants import ServerID
import asyncio

# Our imports
import websockclient
import redisclient

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

def request_a_channel():
    # Note: change this later to not be hardcoded and allow this to retrieve name and ID from an API
    # server_names = [(s_names.name, s_names.value) for s_names in ServerID]
    # print("Available servers:")
    # print(*server_names, sep='\n')

    # server_id = input("Request access to an available server: ")

    # print("Available channels:\n"
    #       "10.24 <-> 655.35")

    user_name = input("What's your username?\n")
    channel_id = input("Request access to an available channel, or type the name to a new one: ")
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
        "channel_type": channel_type,
        "user_name": user_name # Add this later for the server to visibly show who's casting, redis management, etc.
    }

    return channel_request_pack


async def main_runner(json_req):
    """
    SERVICE: Websocket voice client.
    from websockclient import handler
    Handles audio I/O, channel connections to server, audio transmission protocols
    """

    """
    SERVICE: Redis chat client.
    from redisclient import handler
    Handles all chat notifications when connected to a channel.
    """

    async_funcs = await asyncio.gather(
        websockclient.handler(json_req),
        redisclient.handler(json_req)
    )
    pass

# THIS IS OUR BIG MAIN DRIVER FOR OUR CLIENT.
# Any extra overarching async functionality you want to run as a new service goes here.
if __name__ == "__main__":
    # Any init functionality should go before the asyncio run.
    # TODO: allow args to be passed in instead of typing in CLI.

    # Create json-request
    json_req = json.dumps(request_a_channel())

    # Now, call our async services and run async tasks.
    try:
        asyncio.run(main_runner(json_req))
    except KeyboardInterrupt as e:
        # Remove this except to make debugging more verbose.
        print("Keyboard Interrupt closed LC-Radio.")

