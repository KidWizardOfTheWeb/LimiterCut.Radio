import selectors
import socket
import time

import pyaudiowpatch as pyaudio

# CONVERT TO UDP?

sel = selectors.DefaultSelector()

channel_table = {}
cast_table = {}
receive_table = {}

serverName = "localhost"
serverPort = 3601

# Audio
p = pyaudio.PyAudio()
CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000
# RECORD_SECONDS = 3
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK)

def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    # Register first to a function that gets their token first and verifies with the API.
    # Then once verified, modify the registration with modify() to go to read.
    sel.register(conn, selectors.EVENT_READ, verify_token)
    # sel.register(conn, selectors.EVENT_READ, read)

def verify_token(conn, mask):
    # TODO: retrieve token from user here to verify
    data = conn.recv(1000)
    if data:
        # Here, we want to find an address to send to
        channelID_requested = data.decode()

        print('User is requesting an action on channel: ', channelID_requested, '\nfrom: ', conn)

        # TODO: Add verify token here
        res = int(input("Accept connection? 1 for cast, 2 for receive: "))
        if res == 1:
            # Add Cast/Listen flag, Channel ID, verified connection maybe? Probably a class structure for everything later.
            # These flags will help choose what function these connections will use
            # Casters will send their packets to the cast function
            # Listeners will retrieve packets from the listen function

            # Move to cast function, set data to channel casting to
            sel.modify(conn, selectors.EVENT_READ, cast)

            # Move to table
            list_of_casters = cast_table.get(channelID_requested)
            if not list_of_casters:
                # If not in our table, add this connection
                cast_table[conn] = channelID_requested
            else:
                # If it does exist, the value should be a list of connections. Append to the connection list, if allowed.
                # Currently, there can ONLY be one caster.
                # However, if we can ensure that sending multiple audio packets from different sources is safe, we will allow it.
                print("DEBUG HERE.")
                pass

            # Send response
            conn.send(b"Connection allowed as caster.")


        if res == 2:
            # Move to listen function
            sel.modify(conn, selectors.EVENT_READ, read)
            print("Modified to read.")

            # Move to table
            list_of_receivers = receive_table.get(channelID_requested)
            if not list_of_receivers:
                # If not in our table, add it
                receive_table[channelID_requested] = [conn]
            else:
                # If it does exist, the value should be a list of connections. Append to the connection list
                receive_table[channelID_requested].append(conn)
                print("DEBUG HERE.")
                pass

            # This helps the issue of nonblocking packets, but when someone else connects things freeze until accepted
            # By the above function
            # Instead, automate this and maybe multithread the acceptance criteria?
            conn.settimeout(1)
            # conn.setblocking(True)
            conn.send(b"Connection allowed as listener.")
        # conn.send(data)  # Hope it won't block
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()

def cast(conn, mask):
    # CHANGED THIS TO HANDLE AUDIO DATA CASTING
    # data = None
    try:
        data = conn.recv(4096)
    except (ConnectionResetError, ConnectionAbortedError) as e:
        # TODO: Close channel entirely if caster is gone, disconnect listeners from said channel too.
        data = None

    # data = conn.recv(1000)  # Should be ready

    # Find which channel this current caster is casting to.
    # sel.get_key(conn)

    if data:
        channel_to_cast = cast_table.get(conn)
        # Here, we want to find an address to send to
        # print('echoing audio data to: ', conn)
        # print('echoing', repr(data), 'to', conn)
        # conn.send(data)  # Hope it won't block

        if channel_to_cast:
            # Get listeners
            if receive_table.get(channel_to_cast):
                # print(receive_table.get(channel_to_cast))
                all_listeners = receive_table[channel_to_cast]
                for listener in all_listeners:
                    try:
                        print('sending audio data to: ', listener)
                        listener.send(data)  # Hope it won't block
                    except (TimeoutError, OSError) as e:
                        # Timed out, either disconnected or something else failed.
                        # Remove listener if this is the case.
                        receive_table[channel_to_cast].remove(listener)
                        print("Listener removed.")

                    # NOTE: are there other triggers for OSError that need specifics?
                    # except OSError as e:
                        # Listener is currently a closed socket, remove it.
                        # receive_table[channel_to_cast].remove(listener)
                        # print("Listener removed.")
                        # print("Listener is currently: ", repr(listener))
    else:
        print('closing', conn)
        # Remove this caster from the tables
        cast_table.pop(conn)
        sel.unregister(conn)
        conn.close()

def read(conn, mask):
    try:
        # CHANGED THIS TO HANDLE AUDIO DATA CASTING
        # data = conn.recv(4096)
        data = conn.recv(1000)  # Should be ready
    except (ConnectionResetError, ConnectionAbortedError) as e:
        # Catch closing the instance here, unregister the socket
        data = None
        pass
    # Might be able to change registration in this func by doing unregister and reregister.
    # See https://docs.python.org/3.14/library/selectors.html#selectors.BaseSelector.modify

    # If there's any data sent from the client currently, decode the signals.
    # This might turn into chatting later.
    if data:
        recv_signal = data.decode()
        # if recv_signal == "EOF":
        #     print('closing', conn)
        #     sel.unregister(conn)
        #     conn.close()
    else:
        print('closing', conn)
        # Remove this listener as a connection, table removal is handled in cast if listener is disconnected at all.
        sel.unregister(conn)
        conn.close()

sock = socket.socket()
sock.bind((serverName, serverPort))
sock.listen(100)
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accept)

while True:
    events = sel.select()
    for key, mask in events:
        callback = key.data
        callback(key.fileobj, mask)