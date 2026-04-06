# Client
import os
import json
from pathlib import Path
from socket import *
import pyaudiowpatch as pyaudio
from environ import ImproperlyConfigured
import environ # For reading environment variables
from constants import BUFFER_SIZE, ServerResp, ServerID

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

# Connect sockets here
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

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

output_stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK)

def join_channel():
    # After sending a connect request, immediate run .send(token) to verify the token.
    # If that returns 200, then we can start sending data.
    print("Available channels:\n"
          "10.24 <-> 655.35")

    channel_id = input("Request access to an available channel: ")
    print("Requesting channel access to the server and waiting for approval...")

    # TODO: Allow the user to choose a server first.
    # Server set to Master System for now by default.
    channel_request_pack = {
        "server_id": ServerID.MS,
        "channel_id": channel_id,
        # "user_name": "" # Add this later for the server to visibly show who's casting.
    }

    json_req = json.dumps(channel_request_pack)

    # TODO: replace .send() with .sendto(), so the user can send to a designated IP based on server_id.
    # clientSocket.send(channel_id.encode())
    clientSocket.send(json_req.encode())
    message_response = clientSocket.recv(1024)
    print(message_response.decode())

    return message_response


# if message_response.decode() == ServerResp.LISTEN_OK:

def listener_handler():
    try:
        while True:
            # Note: consider .recv_into() for buffer storage instead.
            # This means that the client could store a buffer and need to call receive less often.
            # https://docs.python.org/3.14/library/socket.html#socket.socket.recv_into
            data = clientSocket.recv(4096)
            if data:
                output_stream.write(data)
    except KeyboardInterrupt as e:
        # Close connection, send the kill packet to disconnect
        # clientSocket.sendall("EOF".encode())
        clientSocket.close()
        pass
    clientSocket.close()

# else:

# TODO: implement threaded functions below:
# def handle_cocast_requests():
#     # Thread function.
#     # If someone requests to cocast, receive the notif here and allow the host-caster to accept or deny.
#     pass
#
# def receive_cocast_packets():
#     # Thread function.
#     # Co-cast packets will be received here
#     pass
#
# def process_audio():
#     # Thread function.
#     # All packets from host-caster + co-casters are combined and processed before being sent to the server.
#     pass

def caster_handler():
    # Send audio here
    # TODO: Make sending data a thread.
    # TODO: make receiving data from the server a thread.
    # TODO: if someone else tries to connect to this channel:
    # 1. send a message to the casting client and ask for permission to join.
    # 2. If accepted, receive data from the co-casting user directly (think of the first caster as the host of all co-casters, they have their own server).
    # 2a. Move the co-host status from just "cast" to "co-cast".
    # 2b. Co-cast function will stream directly to the caster instead of the listener, while receiving data from main caster/other co-casters.
    # 2c. We could let the server average all the packets maybe? But we cannot guarantee the packets will come in on the same thread in order to average them.
    # 3. Combine audio input, normalize, send to listeners.
    try:
        while True:
            # Implement another thread that receives audio data from co-caster input streams from the server.
            # Server sends all co-caster data to the main caster on the channel, all audio is averaged and sent to server.
            data = input_stream.read(CHUNK)
            # Note: use .sendall() instead to ensure all voice packets make it? Or just do .send()
            # Testing .sendall() for now.
            clientSocket.sendall(data)
    except KeyboardInterrupt as e:
        clientSocket.close()
        pass

    clientSocket.close()


if __name__ == '__main__':
    # Connect to server
    response = join_channel()

    # If a listener, enter this handler
    # Listeners should be able to:
    # 1. Check which channel they're listening to.
    # 2. The caster/channel's name.
    # Note: make this a separate process?
    if response == ServerResp.LISTEN_OK:
        listener_handler()

    # If a caster, enter this handler
    # Casters should be able to:
    # 1. Send audio data to the server, which redirects to the listener.
    # 2. Receive data from "co-hosts" in a separate thread,
    # Note: make this a separate process?
    if response == ServerResp.CAST_OK:
        caster_handler()
    pass