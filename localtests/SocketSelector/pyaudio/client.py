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
    while True:
        data = clientSocket.recv(4096)
        if data:
            output_stream.write(data)

# Send audio here
while True:
    data = input_stream.read(CHUNK)
    clientSocket.send(data)

for i in range (0, 3):
    # if i == 0:
    #
    # else:
        message = input('Type a sentence to send\n')
        clientSocket.send(message.encode())
        modifiedMessage = clientSocket.recv(1024)
        print(modifiedMessage.decode())

clientSocket.close()