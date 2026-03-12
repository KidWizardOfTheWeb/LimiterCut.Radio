# Client
# CONVERT TO UDP
import pyaudiowpatch as pyaudio
from socket import *
serverName = "localhost"
serverPort = 3601
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
# After sending a connect request, immediate run .send(token) to verify the token.
# If that returns 200, then we can start sending data.
print("Available channels:\n"
      "10.24")
message = input("Request access to an available channel: ")
print("Requesting channel access to the server and waiting for approval...")
clientSocket.send(message.encode())
modifiedMessage = clientSocket.recv(1024)
print(modifiedMessage.decode())

# Audio
CHUNK = 1024 * 4
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

if modifiedMessage.decode() == "Connection allowed as listener.":
    try:
        while True:
            data = clientSocket.recv(4096)
            if data:
                output_stream.write(data)
    except KeyboardInterrupt as e:
        # Close connection, send the kill packet to disconnect
        # clientSocket.sendall("EOF".encode())
        clientSocket.close()
        pass
else:
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
            clientSocket.send(data)
    except KeyboardInterrupt as e:
        clientSocket.close()
        pass

clientSocket.close()