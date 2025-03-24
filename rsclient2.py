import socket

# Server details
SERVER_IP = "9.60.56.68"  # Change to the actual server IP
SERVER_PORT = 1952       # Change to the actual port

# Number to send
number = "macbook meghana h2 2"  # Change this to any number

#
def receive_lines(sock):
    dataline = ""  # Buffer for incoming data
    num = 0        # Line counter

    while True:  # Infinite loop to receive data
        try:
            # Read data from the socket
            # data = sock.recv(1024).decode('ascii', errors='replace')  # Read up to 1024 bytes
            data = sock.recv(1024).decode('latin-1')  # Read up to 1024 bytes
            # data = sock.recv(1024) # Read up to 1024 bytes
            if not data:  # If empty, the connection is closed
                break

            print(f"{data} \n")
            # dataline += data  # Append received data to buffer

            # while '\x15' in dataline:  # Process complete lines (delimiter = '15'x in REXX)
            #   nextline, dataline = dataline.split('\x15', 1)  # Extract first complete line
            #   num += 1
            #   print(f"{num:5}: {nextline}")  # Print line number and data

        except Exception as e:
            print(f"Error: {e}")
            break

try:
    # Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print(f"Connected to {SERVER_IP}:{SERVER_PORT}")

    # Send the number (encode to bytes)
    client_socket.sendall(number.encode('ascii'))

    # Receive response
    # response = client_socket.recv(1024).decode('ascii')
    # response = client_socket.recv(1024)
    # print(f"Server response: {response}")
    receive_lines(client_socket)

except Exception as e:
    print(f"Error: {e}")

finally:
    # Close the connection
    client_socket.close()
