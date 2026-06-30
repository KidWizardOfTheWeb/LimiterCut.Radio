# Main client driver for all services, use this as your main launching point.
import os
import json
from pathlib import Path
import asyncio
import argparse
import uuid
import configparser

# Our imports
from clientclass import *
import websockclient
import redisclient
# import audioprocessing

# Our defaults for no params/config details
default_server_name = "localhost"
default_server_port = 3601
default_username = "UndefUser"

def request_a_channel(config_dict: dict):
    # Note: change this later to not be hardcoded and allow this to retrieve name and ID from an API
    # server_names = [(s_names.name, s_names.value) for s_names in ServerID]
    # print("Available servers:")
    # print(*server_names, sep='\n')

    # Uses details from the parsed arguments and retrieves them, otherwise using defaults.
    server_name = config_dict.get("servername", default_server_name)
    server_port = config_dict.get("serverport", default_server_port)
    user_name = config_dict.get("username", default_username)

    while len(user_name) > 16:
        # Name length cannot be greater than 16 characters.
        user_name = input("Username cannot be longer than 16 characters. Enter new username:\n")

    channel_id = config_dict.get("channel", None)
    if not channel_id:
        channel_id = input("Request access to an available channel, or type the name to a new one: ")

    channel_type = config_dict.get("connecttype", None)
    while not channel_type and channel_type != "radio".casefold() and channel_type != "chat".casefold():
        channel_type = input("Request channel type (Radio, chat): ")

    print("Requesting channel access to the server and waiting for approval...")

    # TODO: Allow the user to choose a server first.
    # Server set to Master System for now by default.

    # Uncomment this for local testing. Should make this a script arg in the future, honestly.
    # serverName = "localhost"

    server_websocket = "ws://" + server_name + ":" + str(server_port)
    channel_request_pack = {
        "server_websocket": str(server_websocket),
        "server_endpoint": str(server_name),
        "server_id": ServerID.MS,
        "channel_id": channel_id,
        "channel_type": channel_type,
        "user_name": user_name, # Add this later for the server to visibly show who's casting, redis management, etc.
        "user_id": uuid.uuid4().hex # GUID for a user in bytes (32 len)
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
        # configreader.handler(),
        websockclient.handler(json_req),
        # audioprocessing.mix_stored_packets(),
        redisclient.handler(json_req),
    )
    pass

# THIS IS OUR BIG MAIN DRIVER FOR OUR CLIENT.
# Any extra overarching async functionality you want to run as a new service goes here.
if __name__ == "__main__":
    # Any init functionality should go before the asyncio run.
    """
    This should handle the following:
    1. -GUI, --GUI (default OFF). Allows pyqt6 window to hook in for options.
    2. -useconfig, --Useconfig (default OFF). Allows users to change things live, like inputs.
    """
    parser = argparse.ArgumentParser()

    # Config file support, this should be a direct file path to it.
    parser.add_argument("-config", "--config",
                        help="Path to config file. Uses a preset config file to connect to a specific channel and server as a specific user.")

    # Base info for connecting to the server, if the user chooses to add any of these flags on exec.
    parser.add_argument("-ServerName", "--servername",
                        help="Specify a server to connect to. If not provided, uses localhost.")
    parser.add_argument("-ServerPort", "--serverport",
                        help="Specify a server port to connect to. If not provided, uses 3601 as default.")
    parser.add_argument("-Username", "--username",
                        help="Enters a username to use when connecting to the server. If not provided, user is prompted in CLI instead.")
    parser.add_argument("-Channel", "--channel",
                        help="Enters a channel to connect to on a given server. If not provided, user is prompted in CLI instead.")
    parser.add_argument("-Connecttype", "--connecttype",
                        help="Chooses a connection type to a channel (radio/chat). If not provided, user is prompted in CLI instead.")

    # Extra settings
    parser.add_argument("-GUI", "--gui", default=False, action='store_true', help="Turns GUI (windows instead of CLI) on or off. Default is OFF.")
    args = parser.parse_args()

    if args.gui:
        print("GUI: ON.")
        # Add GUI hooks here (PyQt6 WIP).

    # Convert args to dictionary
    config_dict = vars(args)

    # If no args, use a config file passed in.
    if args.config:
        config_data = configparser.ConfigParser()
        try:
            config_data.read(args.config)
            # For each section,
            # Replace each field with the config variants.
            for section in config_data.sections():
                for keys, vals in config_data.items(section):
                    # Do replacements of args read from config here.
                    config_dict[keys] = vals
        except Exception as e:
            print(e)
            input("Continue execution?")
            pass


    # Create json-request.
    json_req = json.dumps(request_a_channel(config_dict))

    # Store in clientclass.
    ClientObject.json_req = json.loads(json_req)

    # Now, call our async services and run async tasks.
    # Note: maybe allow the user to choose to turn off certain services? Like redis chat.
    try:
        asyncio.run(main_runner(json_req))
    except KeyboardInterrupt as e:
        # Remove this except to make debugging more verbose.
        print("Keyboard Interrupt closed LC-Radio.")
    except Exception as e:
        print(e)

